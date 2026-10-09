import json
from openai import OpenAI
from config import API_KEY, BASE_URL, MODEL, BASE_DIR
from tools import TOOL_SCHEMAS, run_tool, schema

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
PROFILE = json.load(open(BASE_DIR / "profile.json"))

SHOW_TOOL = schema(
    "show_opportunity",
    "Show ONE opportunity to the user as a card with Apply/Skip buttons. "
    "Call it once for each good match.",
    {"title": {"type": "string"}, "company": {"type": "string"},
     "kind": {"type": "string"}, "deadline": {"type": "string"},
     "details": {"type": "string", "description": "stipend, location, why it fits"},
     "url": {"type": "string"}},
    ["title", "url"])
TOOLS = TOOL_SCHEMAS + [SHOW_TOOL]

SYSTEM = f"""You are a friendly assistant that helps a student find hackathons, internships and jobs.
Student profile: {json.dumps(PROFILE)}

- When asked for opportunities, call only the search tools that fit the request. For Unstop,
  call search_unstop separately per kind (hackathon / internship).
- Then call show_opportunity for each of the best matches (at most 6). Skip expired ones.
  Use URLs exactly as the tools returned them; never invent one.
- After the cards, write a short chat message and ask which ones they want to apply to.
- Never say you applied. Applying happens when the user presses Apply on a card.
- Keep replies short and conversational."""


def chat_turn(history):
    """history: [{'role': 'user'|'assistant', 'content': str}]. Returns (reply, cards)."""
    msgs = [{"role": "system", "content": SYSTEM}] + history
    cards = []
    for _ in range(10):
        resp = client.chat.completions.create(
            model=MODEL, messages=msgs, tools=TOOLS, temperature=0.3, max_tokens=3000)
        m = resp.choices[0].message
        entry = {"role": "assistant", "content": m.content or ""}
        if m.tool_calls:
            entry["tool_calls"] = [
                {"id": c.id, "type": "function",
                 "function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in m.tool_calls]
        msgs.append(entry)

        if not m.tool_calls:
            return m.content or "", cards

        for call in m.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            if call.function.name == "show_opportunity":
                cards.append(args)
                result = {"shown": True}
            else:
                result = run_tool(call.function.name, args)
            msgs.append({"role": "tool", "tool_call_id": call.id,
                         "content": json.dumps(result)[:12000]})
    return "I ran out of steps. Try a narrower request.", cards
def write_pack(card):
    """Cover note + common answers for one listing, using only facts from profile.json."""
    prompt = f"""Write an application pack for this opportunity.

Opportunity: {json.dumps(card)}

Candidate profile. Use ONLY these facts. Never invent experience, projects, grades or numbers.
If something useful is missing, put a [placeholder] in square brackets for the candidate to fill in.
{json.dumps(PROFILE)}

Return Markdown with exactly these sections:
### Cover note
90-130 words, specific to this listing, plain and direct, no cliches like "I am writing to express".
### Why me
3 short bullets tied to what the listing asks for, drawn only from the profile.
### Common answers
Short answers to: Why this role? / A relevant project you've done / Availability and duration.
"""
    resp = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": prompt}],
        temperature=0.5, max_tokens=900)
    return resp.choices[0].message.content or "Could not generate a pack. Try again."