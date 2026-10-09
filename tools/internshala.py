import re
import requests
from bs4 import BeautifulSoup

BASE = "https://internshala.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

def _text(node):
    return node.get_text(" ", strip=True) if node else None

def search_internshala(keywords: str, limit: int = 15):
    slug = _slug(keywords)
    url = f"{BASE}/internships/{slug}-internship/" if slug else f"{BASE}/internships/"

    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    results, seen = [], set()

    # Preferred: full listing cards (company, stipend, location available)
    for card in soup.select("div.individual_internship"):
        a = card.select_one("a[href*='/internship/detail/']")
        if not a:
            continue
        link = BASE + a["href"] if a["href"].startswith("/") else a["href"]
        if link in seen:
            continue
        seen.add(link)
        results.append({
            "source": "internshala", "kind": "internship",
            "title": _text(card.select_one(".job-title-href, .profile, h3")) or _text(a),
            "company": _text(card.select_one(".company-name, .company_name")),
            "stipend": _text(card.select_one(".stipend")),
            "location": _text(card.select_one(".locations, .row-1-item.locations")),
            "url": link, "deadline": None,
        })

    # Fallback: if the card class has changed, collect any detail links on the page
    if not results:
        for a in soup.select("a[href*='/internship/detail/']"):
            link = BASE + a["href"] if a["href"].startswith("/") else a["href"]
            if link in seen or not _text(a):
                continue
            seen.add(link)
            results.append({"source": "internshala", "kind": "internship",
                            "title": _text(a), "url": link, "deadline": None})

    return results[:limit]


if __name__ == "__main__":
    for row in search_internshala("data science"):
        print(row)