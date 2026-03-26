import os
import json
import requests
from datetime import datetime, timedelta, timezone
from get_team import get_team



GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ORG = "OpenPecha"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
WINDOW_DAYS = 3


def _headers():
    if not GITHUB_TOKEN:
        raise RuntimeError(
            "Set GITHUB_TOKEN in your environment (Personal Access Token with repo scope)."
        )
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def load_data(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default


def _utc_today_date():
    return datetime.now(timezone.utc).date()


def commit_window_bounds():
    """
    Last WINDOW_DAYS calendar days in UTC, excluding the day of execution.
    Returns (start_date, end_date_exclusive) as date objects,
    and a range string for the GitHub committer-date qualifier.
    """
    today = _utc_today_date()
    end = today  # exclusive upper bound (today is not included)
    start = today - timedelta(days=WINDOW_DAYS)
    last_inclusive = end - timedelta(days=1)
    date_range = f"{start.isoformat()}..{last_inclusive.isoformat()}"
    return start, end, date_range


def fetch_user_commit_search_raw(username, date_range):
    """
    Paginate GET /search/commits for commits in the given date_range
    (inclusive GitHub range syntax YYYY-MM-DD..YYYY-MM-DD) and return
    the list of raw JSON bodies (one dict per HTTP response, unchanged).
    """
    q = f"org:{ORG} author:{username} committer-date:{date_range}"
    raw_pages = []
    page = 1
    while True:
        response = requests.get(
            "https://api.github.com/search/commits",
            headers=_headers(),
            params={"q": q, "per_page": 100, "page": page},
            timeout=60,
        )
        data = response.json()
        if response.status_code == 422 and "first 1000" in data.get("message", ""):
            break
        if response.status_code != 200:
            err = data.get("message", response.text)
            raise RuntimeError(
                f"GitHub API error ({response.status_code}) for {username}: {err}"
            )
        raw_pages.append(data)
        batch = data.get("items") or []
        total_count = data.get("total_count", 0)
        total_fetched = sum(len(p.get("items") or []) for p in raw_pages)
        if len(batch) < 100 or total_fetched >= total_count:
            break
        page += 1
    return raw_pages


def _commit_days_from_raw_pages(raw_pages, window_start, window_end_exclusive):
    """UTC calendar dates (YYYY-MM-DD) that appear as committer dates in search items."""
    days = set()
    for page in raw_pages:
        for item in page.get("items") or []:
            commit = item.get("commit") or {}
            committer = commit.get("committer") or {}
            raw = committer.get("date")
            if not raw:
                continue
            try:
                d = datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
            except ValueError:
                continue
            if window_start <= d < window_end_exclusive:
                days.add(d.isoformat())
    return days


def _apply_skip_credits(state_user, skip_dates_iso):
    """
    Increment total_skips once per calendar day with no commits, only the first time we credit it.
    """
    credited = set(state_user.get("skip_credited_dates") or [])
    added = 0
    for d in sorted(skip_dates_iso):
        if d not in credited:
            credited.add(d)
            added += 1
    state_user["skip_credited_dates"] = sorted(credited)
    state_user["total_skips"] = state_user.get("total_skips", 0) + added
    return added


def run_monitor():
    members = get_team()
    state = load_data("state.json", {})

    start_d, end_d, date_range = commit_window_bounds()
    window_dates = [
        (start_d + timedelta(days=i)).isoformat() for i in range(WINDOW_DAYS)
    ]
    lines = [
        f"Window (UTC): {date_range} (exclusive of today, {WINDOW_DAYS} days)"
    ]
    for user in members:
        raw_pages = fetch_user_commit_search_raw(user, date_range)
        first = raw_pages[0] if raw_pages else {}
        commit_count = first.get("total_count", 0)

        if user not in state:
            state[user] = {"total_skips": 0, "skip_credited_dates": []}
        else:
            su = state[user]
            su.setdefault("skip_credited_dates", [])
            su.setdefault("total_skips", 0)

        days_with_commits = _commit_days_from_raw_pages(
            raw_pages, start_d, end_d
        )
        skip_dates = [d for d in window_dates if d not in days_with_commits]
        window_skip_days = len(skip_dates)
        newly_credited = _apply_skip_credits(state[user], skip_dates)

        state[user]["search_responses"] = raw_pages
        state[user]["window_skip_days"] = window_skip_days
        state[user]["window_dates"] = window_dates
        state[user]["days_with_commits_in_window"] = sorted(days_with_commits)
        lines.append(
            f"{user}: {len(raw_pages)} page(s), total_count={commit_count}, "
            f"window_skip_days={window_skip_days}, +total_skips={newly_credited}, "
            f"total_skips={state[user]['total_skips']}"
        )

    with open("state.json", "w") as f:
        json.dump(state, f, indent=4)

    return "\n".join(lines)


if __name__ == "__main__":
    print(run_monitor())




