import requests

URL = "https://www.hackerearth.com/chrome-extension/events/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

def search_hackerearth(keywords: str = "", limit: int = 15):
    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    events = r.json().get("response", [])

    rows = []
    for e in events:
        if (e.get("status") or "").upper() not in ("ONGOING", "UPCOMING"):
            continue
        ctype = (e.get("challenge_type") or "").lower()
        rows.append({
            "source": "hackerearth",
            "kind": "hackathon" if "hackathon" in ctype else (ctype or "challenge"),
            "title": e.get("title"),
            "url": e.get("url"),
            "deadline": str(e.get("end_utc_tz") or e.get("end_tz") or "")[:10] or None,
        })

    # keywords are a soft filter: if nothing matches, return everything
    if keywords:
        kw = keywords.lower()
        matched = [x for x in rows if kw in (x["title"] or "").lower()]
        rows = matched or rows
    return rows[:limit]


if __name__ == "__main__":
    for row in search_hackerearth():
        print(row)