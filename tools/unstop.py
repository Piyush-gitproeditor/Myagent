import requests
from datetime import date

BASE = "https://unstop.com"
API = f"{BASE}/api/public/opportunity/search-result"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
           "Accept": "application/json"}

KIND_TO_OPP = {"hackathon": "hackathons", "internship": "internships", "job": "jobs"}

def _dig(d, *path):
    for p in path:
        if not isinstance(d, dict):
            return None
        d = d.get(p)
    return d

def _deadline(item):
    raw = (_dig(item, "regnRequirements", "end_regn_dt")
           or item.get("end_regn_dt") or item.get("end_date"))
    return str(raw)[:10] if raw else None      # keep YYYY-MM-DD

def search_unstop(keywords: str = "", kind: str = "hackathon", limit: int = 15):
    params = {"opportunity": KIND_TO_OPP.get(kind, "hackathons"),
              "page": 1, "per_page": 30, "oppstatus": "open"}
    if keywords:
        params["searchTerm"] = keywords

    r = requests.get(API, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    items = _dig(r.json(), "data", "data") or []

    today = date.today().isoformat()
    results = []
    for it in items:
        dl = _deadline(it)
        if dl and dl < today:                  # API doesn't filter reliably, so we do
            continue
        path = it.get("public_url")
        if not path:
            continue
        results.append({
            "source": "unstop", "kind": kind,
            "title": it.get("title"),
            "organizer": _dig(it, "organisation", "name"),
            "url": path if path.startswith("http") else f"{BASE}/{path.lstrip('/')}",
            "deadline": dl,
        })
        if len(results) >= limit:
            break
    return results


if __name__ == "__main__":
    for k in ("hackathon", "internship"):
        print(f"\n--- {k} ---")
        for row in search_unstop("", k, limit=5):
            print(row)