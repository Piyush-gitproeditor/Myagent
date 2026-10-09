import requests
from datetime import datetime, timezone

URL = "https://leetcode.com/graphql"
QUERY = {"query": "{ upcomingContests { title titleSlug startTime duration } }"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
           "Content-Type": "application/json",
           "Referer": "https://leetcode.com/contest/"}

def upcoming_contests():
    r = requests.post(URL, json=QUERY, headers=HEADERS, timeout=20)
    r.raise_for_status()
    contests = (r.json().get("data") or {}).get("upcomingContests") or []

    out = []
    for c in contests:
        start = datetime.fromtimestamp(c["startTime"], tz=timezone.utc)
        out.append({
            "source": "leetcode", "kind": "contest",
            "title": c["title"],
            "url": f"https://leetcode.com/contest/{c['titleSlug']}",
            "deadline": start.strftime("%Y-%m-%d"),     # the contest date
            "starts_utc": start.strftime("%Y-%m-%d %H:%M"),
            "duration_min": c["duration"] // 60,
        })
    return out


if __name__ == "__main__":
    for row in upcoming_contests():
        print(row)