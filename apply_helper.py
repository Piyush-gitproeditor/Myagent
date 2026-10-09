import json
import re
import sys
from playwright.sync_api import sync_playwright
from config import BASE_DIR

PROFILE = json.load(open(BASE_DIR / "profile.json"))

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
    for word in CTA_WORDS:
        pattern = re.compile(word, re.I)
        loc = page.get_by_role("button", name=pattern).or_(page.get_by_role("link", name=pattern))
        if loc.count():
            loc.first.click()
            page.wait_for_load_state("domcontentloaded")
            return word
    return None


def fill_known_fields(page):
    filled = []
    inputs = page.locator("input:visible, textarea:visible")
    for i in range(inputs.count()):
        el = inputs.nth(i)
        try:
            typ = (el.get_attribute("type") or "text").lower()
            if typ not in ("text", "email", "tel", "url") or el.input_value():
                continue
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
            continue
    return filled

def wait_for_human_check(page, timeout_s=180):
    """If a bot-check page is showing, leave it alone until the person passes it."""
    markers = ("security verification", "verify you are human",
               "just a moment", "checking your browser")
    for _ in range(timeout_s):
        try:
            text = (page.title() + " " + page.inner_text("body")[:600]).lower()
        except Exception:
            text = ""
        if not any(m in text for m in markers):
            return True
        page.wait_for_timeout(1000)
    return False

def main(url):
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(BASE_DIR / "browser_data"), channel="chrome", headless=False)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            cta = click_cta(page)
            page.wait_for_timeout(1500)
            filled = fill_known_fields(page)
            print(f"clicked: {cta} | pre-filled: {filled or 'nothing'}")
        except Exception as e:
            print("automation error:", e)

        # Stay open for you (CAPTCHA, OTP, review, submit) until you close the window
        while True:
            try:
                if not ctx.pages:
                    break
                ctx.pages[0].wait_for_timeout(1000)
            except Exception:
                break
        try:
            ctx.close()
        except Exception:
            pass


if __name__ == "__main__":
    main(sys.argv[1])