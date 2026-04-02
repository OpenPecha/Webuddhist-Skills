import os
import json
import requests
from datetime import datetime, timedelta, timezone


ORG = "OpenPecha"
WINDOW_DAYS = 3
TEAM_SLUG = "openpecha-dev-team"
_ISO_TZ_OFFSET = "+00:00"


def _api_headers():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "Set GITHUB_TOKEN in your environment (Personal Access Token with repo scope)."
        )
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2026-03-10",
    }


def get_team():
    headers = _api_headers()
    url = f"https://api.github.com/orgs/{ORG}/teams/{TEAM_SLUG}/members"
    res = requests.get(url, headers=headers, timeout=60)
    res.raise_for_status()
    return [user["login"] for user in res.json()]


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
    and a range string for display (same as former GitHub committer-date search).
    """
    today = _utc_today_date()
    end = today  # exclusive upper bound (today is not included)
    start = today - timedelta(days=WINDOW_DAYS)
    last_inclusive = end - timedelta(days=1)
    date_range = f"{start.isoformat()}..{last_inclusive.isoformat()}"
    return start, end, date_range


def _window_to_since_until_iso(window_start, window_end_exclusive):
    """ISO timestamps for GET /repos/.../commits (since / until)."""
    since_dt = datetime(
        window_start.year,
        window_start.month,
        window_start.day,
        0,
        0,
        0,
        tzinfo=timezone.utc,
    )
    until_dt = datetime(
        window_end_exclusive.year,
        window_end_exclusive.month,
        window_end_exclusive.day,
        0,
        0,
        0,
        tzinfo=timezone.utc,
    )
    return (
        since_dt.isoformat().replace(_ISO_TZ_OFFSET, "Z"),
        until_dt.isoformat().replace(_ISO_TZ_OFFSET, "Z"),
    )


def _get_json_allow_missing(url, headers, params=None):
    """GET JSON; return None on 403/404 so one repo cannot stop the run."""
    r = requests.get(url, headers=headers, params=params or {}, timeout=60)
    if r.status_code in (403, 404):
        return None
    r.raise_for_status()
    return r.json()


def _iter_org_repos(headers):
    page = 1
    while True:
        data = _get_json_allow_missing(
            f"https://api.github.com/orgs/{ORG}/repos",
            headers,
            {"per_page": 100, "page": page, "type": "all"},
        )
        if not data:
            break
        yield from data
        if len(data) < 100:
            break
        page += 1


def _iter_repo_branches(headers, owner, repo):
    page = 1
    while True:
        data = _get_json_allow_missing(
            f"https://api.github.com/repos/{owner}/{repo}/branches",
            headers,
            {"per_page": 100, "page": page},
        )
        if not data:
            break
        yield from data
        if len(data) < 100:
            break
        page += 1


def _committer_date(commit_obj):
    commit = commit_obj.get("commit") or {}
    committer = commit.get("committer") or {}
    raw = committer.get("date")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", _ISO_TZ_OFFSET)).date()
    except ValueError:
        return None


def _paginate_commits_for_branch(
    headers, owner, repo, branch_name, author, since_iso, until_iso
):
    """
    Newest-first commits reachable from branch_name, filtered by author and dates.
    Stops early once the page is entirely before the window (descending order).
    """
    page = 1
    while True:
        batch = _get_json_allow_missing(
            f"https://api.github.com/repos/{owner}/{repo}/commits",
            headers,
            {
                "sha": branch_name,
                "author": author,
                "since": since_iso,
                "until": until_iso,
                "per_page": 100,
                "page": page,
            },
        )
        if not batch:
            break
        yield from batch
        if len(batch) < 100:
            break
        oldest = _committer_date(batch[-1])
        if oldest is not None:
            window_start = datetime.fromisoformat(
                since_iso.replace("Z", _ISO_TZ_OFFSET)
            ).date()
            if oldest < window_start:
                break
        page += 1


def fetch_user_commit_days_all_branches(username, window_start, window_end_exclusive):
    """
    GitHub /search/commits only indexes the default branch. To count activity on
    any branch, list commits per branch with author + since/until and dedupe by SHA.

    Returns (days_with_commits_iso_set, meta_dict).
    """
    headers = _api_headers()
    since_iso, until_iso = _window_to_since_until_iso(
        window_start, window_end_exclusive
    )
    seen_shas = set()
    days = set()
    repos_scanned = 0
    branch_requests = 0
    skipped_repos = 0

    for repo in _iter_org_repos(headers):
        full = repo.get("full_name") or ""
        if "/" not in full:
            continue
        owner, name = full.split("/", 1)
        repos_scanned += 1
        branches = list(_iter_repo_branches(headers, owner, name))
        if not branches:
            skipped_repos += 1
            continue
        for br in branches:
            branch_name = br.get("name")
            if not branch_name:
                continue
            branch_requests += 1
            for commit_obj in _paginate_commits_for_branch(
                headers, owner, name, branch_name, username, since_iso, until_iso
            ):
                sha = commit_obj.get("sha")
                if not sha or sha in seen_shas:
                    continue
                seen_shas.add(sha)
                d = _committer_date(commit_obj)
                if d is None:
                    continue
                if window_start <= d < window_end_exclusive:
                    days.add(d.isoformat())

    meta = {
        "mode": "all_branches",
        "repos_scanned": repos_scanned,
        "branch_requests": branch_requests,
        "unique_commits_in_window": len(seen_shas),
        "repos_with_no_branches": skipped_repos,
        "since": since_iso,
        "until": until_iso,
    }
    return days, meta


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
        f"Window (UTC): {date_range} (exclusive of today, {WINDOW_DAYS} days); "
        f"commits from all branches (not search API)"
    ]
    for user in members:
        days_with_commits, fetch_meta = fetch_user_commit_days_all_branches(
            user, start_d, end_d
        )

        if user not in state:
            state[user] = {"total_skips": 0, "skip_credited_dates": []}
        else:
            su = state[user]
            su.setdefault("skip_credited_dates", [])
            su.setdefault("total_skips", 0)

        skip_dates = [d for d in window_dates if d not in days_with_commits]
        window_skip_days = len(skip_dates)
        newly_credited = _apply_skip_credits(state[user], skip_dates)

        state[user]["fetch_meta"] = fetch_meta
        state[user]["window_skip_days"] = window_skip_days
        state[user]["window_dates"] = window_dates
        state[user]["days_with_commits_in_window"] = sorted(days_with_commits)
        lines.append(
            f"{user}: repos={fetch_meta['repos_scanned']}, "
            f"branch_requests={fetch_meta['branch_requests']}, "
            f"unique_commits={fetch_meta['unique_commits_in_window']}, "
            f"window_skip_days={window_skip_days}, +total_skips={newly_credited}, "
            f"total_skips={state[user]['total_skips']}"
        )

    with open("state.json", "w") as f:
        json.dump(state, f, indent=4)

    return "\n".join(lines)


if __name__ == "__main__":
    print(run_monitor())
