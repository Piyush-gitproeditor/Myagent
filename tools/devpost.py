import requests

def search_devpost(keywords: str = "", limit: int = 20):
    r = requests.get(
        "https://devpost.com/api/hackathons",
        params={"status[]": "open", "search": keywords},
        headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    r.raise_for_status()
    return [{"source": "devpost", "kind": "hackathon",
             "title": h.get("title"), "url": h.get("url"),
             "deadline": h.get("submission_period_dates")}
            for h in r.json().get("hackathons", [])[:limit]]