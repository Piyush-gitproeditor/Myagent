import html
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from db import conn

API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def tg(method: str, **payload):
    r = requests.post(f"{API}/{method}", json=payload, timeout=40)
    r.raise_for_status()
    return r.json()

def send(text: str, reply_markup=None):
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text,
               "parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg("sendMessage", **payload)

def keyboard(opp_id: str, url: str):
    rows = [[{"text": "✅ Register", "callback_data": f"reg:{opp_id}"},
             {"text": "⏭ Skip", "callback_data": f"skip:{opp_id}"}]]
    if url and url.startswith("http"):
        rows.append([{"text": "🔗 Open", "url": url}])
    return {"inline_keyboard": rows}

def _fmt(source, kind, title, deadline, score, reason):
    meta = f"{html.escape(source or '')} · {html.escape(kind or '')}"
    if deadline:
        meta += f" · ⏰ {html.escape(str(deadline))}"
    if score is not None:
        meta += f" · ⭐ {score}"
    text = f"<b>{html.escape(title or 'Untitled')}</b>\n{meta}"
    if reason:
        text += f"\n{html.escape(reason)}"
    return text

def send_digest(limit: int = 10):
    c = conn()
    rows = c.execute(
        "SELECT id, source, kind, title, url, deadline, score, reason FROM opps "
        "WHERE status='new' ORDER BY COALESCE(score, 0) DESC LIMIT ?", (limit,)
    ).fetchall()

    if not rows:
        print("Nothing new to send.")
        return 0

    send(f"📌 <b>{len(rows)} new opportunities</b>\nTap Register to approve, Skip to dismiss.")
    sent = 0
    for opp_id, source, kind, title, url, deadline, score, reason in rows:
        try:
            send(_fmt(source, kind, title, deadline, score, reason),
                 reply_markup=keyboard(opp_id, url))
            c.execute("UPDATE opps SET status='notified' WHERE id=?", (opp_id,))
            c.commit()
            sent += 1
        except requests.HTTPError as e:
            print(f"Failed to send '{title}': {e}")
    return sent


if __name__ == "__main__":
    print("sent:", send_digest())