import requests
from config import API_KEY, BASE_URL

headers = {"Authorization": f"Bearer {API_KEY.strip()}", "Content-Type": "application/json"}

r = requests.get(f"{BASE_URL}models", headers=headers, timeout=30)
print("GET /models ->", r.status_code)
if not r.ok:
    print(r.text[:300]); raise SystemExit

ids = [m["id"] for m in r.json().get("data", [])]
nemo = [i for i in ids if "nemotron" in i.lower()]
print("\nNemotron models on your account:")
for i in nemo:
    print("  ", i)

TOOL = [{"type": "function", "function": {
    "name": "get_weather", "description": "Get weather for a city.",
    "parameters": {"type": "object",
                   "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]

print("\nTool-calling test:")
for m in nemo:
    body = {"model": m, "max_tokens": 200, "tools": TOOL, "tool_choice": "auto",
            "messages": [{"role": "user", "content": "What's the weather in Jaipur? Use the tool."}]}
    r = requests.post(f"{BASE_URL}chat/completions", headers=headers, json=body, timeout=90)
    if r.status_code != 200:
        print(f"{m:55} -> {r.status_code}")
        continue
    calls = r.json()["choices"][0]["message"].get("tool_calls")
    print(f"{m:55} -> {'TOOLS WORK' if calls else 'no tool call'}")