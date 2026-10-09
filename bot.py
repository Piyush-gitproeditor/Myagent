import time
import requests
from config import TELEGRAM_CHAT_ID
from db import conn
from notify import tg

ALLOWED = str(TELEGRAM_CHAT_ID)
ACTIONS = {"reg": ("approved", "✅ Approved"),
           "skip": ("skipped", "⏭ Skipped")}

def handle_callback(cb, c):
    # Only you can press the buttons; ignore anyone else who finds the bot
    if str(cb["from"]["id"]) != ALLOWED:
        tg("answerCallbackQuery", callback_query_id=cb["id"], text="Not authorised")
        return

    action, _, opp_id = cb.get("data", "").partition(":")
    if action not in ACTIONS:                    # e.g. the "noop" label button
        tg("answerCallbackQuery", callback_query_id=cb["id"])
        return

    status, label = ACTIONS[action]
    c.execute("UPDATE opps SET status=? WHERE id=? "
              "AND status IN ('new','notified','approved','skipped')", (status, opp_id))
    c.commit()

    tg("answerCallbackQuery", callback_query_id=cb["id"], text=label)
    msg = cb["message"]
    tg("editMessageReplyMarkup", chat_id=msg["chat"]["id"], message_id=msg["message_id"],
       reply_markup={"inline_keyboard": [[{"text": label, "callback_data": "noop"}]]})
    print(f"{label}: {opp_id[:8]}...")

def main():
    c = conn()
    offset = None
    print("Listening for button taps... press Ctrl+C to stop.")
    while True:
        try:
            kwargs = {"timeout": 30, "allowed_updates": ["callback_query"]}
            if offset:
                kwargs["offset"] = offset
            updates = tg("getUpdates", **kwargs).get("result", [])
            for u in updates:
                offset = u["update_id"] + 1
                if "callback_query" in u:
                    handle_callback(u["callback_query"], c)
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:                    # network blip: wait and keep going
            print("error:", e)
            time.sleep(3)

if __name__ == "__main__":
    main()