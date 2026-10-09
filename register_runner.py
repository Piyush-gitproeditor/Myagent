import json
import re
import sys
from playwright.sync_api import sync_playwright
from config import BASE_DIR
from db import conn
from notify import send

PROFILE = json.load(open(BASE_DIR / "profile.json"))

# profile key -> words that may appear in a field's name/label/placeholder.
# Order matters: "college" must come before "name" so "college name" isn't filled with your name.
FIELD_HINTS = {
    "email": ["email"],
    "phone": ["phone", "mobile", "contact number"],
    "college": ["college", "university", "institute", "organization", "organisation"],
    "github": ["github"],
    "linkedin": ["linkedin"],
    "city": ["city", "location"],
    "name": ["full name", "your name", "name"],
}
CTA_WORDS = ["Register", "Join hackathon", "Join", "Apply now", "Apply", "Participate"]


def click_cta(page):
    """Click the first Register/Join/Apply button or link found."""
    for word in CTA_WORDS:
        pattern = re.compile(word, re.I)
        loc = page.get_by_role("button", name=pattern).or_(page.get_by_role("link", name=pattern))
        if loc.count():
            loc.first.click()
            page.wait_for_load_state("domcontentloaded")
            return word
    return None


def fill_known_fields(page):
    """Best-effort fill of empty text fields from profile.json. Returns the keys filled."""
    filled = []
    inputs = page.locator("input:visible, textarea:visible")
    for i in range(inputs.count()):
        el = inputs.nth(i)
        try:
            typ = (el.get_attribute("type") or "text").lower()
            if typ not in ("text", "email", "tel", "url"):
                continue
            if el.input_value():
                continue                     # never overwrite something already filled

            hint = " ".join(filter(None, (el.get_attribute(a) for a in
                            ("name", "id", "placeholder", "aria-label")))).lower()
            fid = el.get_attribute("id")
            if fid:
                lab = page.locator(f"label[for='{fid}']")
                if lab.count():
                    hint += " " + lab.first.inner_text().lower()

            if typ == "email":
                key = "email"
            elif typ == "tel":
                key = "phone"
            else:
                key = next((k for k, words in FIELD_HINTS.items()
                            if any(w in hint for w in words)), None)

            value = PROFILE.get(key) if key else None
            if value:
                el.fill(str(value))
                filled.append(key)
        except Exception:
            continue                          # one odd field shouldn't stop the run
    return filled


def login_mode():
    """Open the sites once so you can log in. The session is saved in browser_data/."""
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(BASE_DIR / "browser_data"), headless=False)
        for url in ("https://devpost.com/users/login",
                    "https://unstop.com",
                    "https://internshala.com/login"):
            ctx.new_page().goto(url)
        input("Log in to each site in the browser, then press Enter here to save and close... ")
        ctx.close()


def run(limit=5):
    c = conn()
    rows = c.execute("SELECT id, title, url, source FROM opps WHERE status='approved' LIMIT ?",
                     (limit,)).fetchall()
    if not rows:
        print("No approved items. Tap Register on some in Telegram first.")
        return

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(BASE_DIR / "browser_data"), headless=False)
        for opp_id, title, url, source in rows:
            print(f"\n=== {title} ({source}) ===")
            page = ctx.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                cta = click_cta(page)
                page.wait_for_timeout(1500)
                filled = fill_known_fields(page)
                print(f"clicked: {cta} | pre-filled: {filled or 'nothing'}")
            except Exception as e:
                print("automation error:", e)

            try:
                send(f"🖐 <b>Needs you:</b> {title}\nSolve any CAPTCHA/OTP, review and submit "
                     f"in the browser window, then answer in the terminal.")
            except Exception:
                pass

            ans = input("[d] submitted  [f] failed  [s] skip for now  > ").strip().lower()
            if ans == "d":
                c.execute("UPDATE opps SET status='registered' WHERE id=?", (opp_id,))
            elif ans == "f":
                c.execute("UPDATE opps SET status='failed' WHERE id=?", (opp_id,))
            c.commit()
            page.close()
        ctx.close()
    print("\nDone.")


if __name__ == "__main__":
    login_mode() if "--login" in sys.argv else run()