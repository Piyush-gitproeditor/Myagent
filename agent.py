import json, re
from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL
from tools import TOOL_SCHEMAS, run_tool
from db import conn, save_new

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
PROFILE = json.load(open("profile.json"))

SYSTEM = f"""Call every search tool at least once. For Unstop, call search_unstop separately for kind=hackathon and kind=internship."""

def parse_json(text):
    m = re.search(r"\[.*\]", text, re.S)
    return json.loads(m.group(0)) if m else []

def run_discovery(max_steps=12):
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Find new opportunities for this week."}]
    for step in range(max_steps):
        resp = client.chat.completions.create(
            model=MODEL, messages=msgs, tools=TOOL_SCHEMAS,
            temperature=0.2, max_tokens=4000)
        msg = resp.choices[0].message
        msgs.append(msg)

        if not msg.tool_calls:
            print("Model final answer:\n", msg.content)   # helpful while debugging
            return parse_json(msg.content or "")

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            print(f"[step {step}] tool: {call.function.name} {args}")
            result = run_tool(call.function.name, args)
            msgs.append({"role": "tool", "tool_call_id": call.id,
                         "content": json.dumps(result)})
    return []

if __name__ == "__main__":
    from notify import send_digest
    c = conn()
    fresh = [o for o in run_discovery() if save_new(c, o)]
    print(f"\n{len(fresh)} new opportunities saved")
    print(f"{send_digest()} sent to Telegram")