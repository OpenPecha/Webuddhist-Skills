import os
import requests

ORG = "OpenPecha"
TEAM_SLUG = "openpecha-dev-team"


def get_team():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "Set GITHUB_TOKEN in your environment (Personal Access Token with repo scope)."
        )
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    url = f"https://api.github.com/orgs/{ORG}/teams/{TEAM_SLUG}/members"
    res = requests.get(url, headers=headers, timeout=60)
    res.raise_for_status()
    return [user["login"] for user in res.json()]


if __name__ == "__main__":
    print(get_team())