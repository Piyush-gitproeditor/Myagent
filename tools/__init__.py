from . import devpost, hackerearth, leetcode, unstop, internshala

REGISTRY = {
    "search_devpost": devpost.search_devpost,
    "search_hackerearth": hackerearth.search_hackerearth,
    "search_leetcode_contests": leetcode.upcoming_contests,
    "search_unstop": unstop.search_unstop,
    "search_internshala": internshala.search_internshala,
}

def schema(name, desc, props, required=()):
    return {"type": "function",
            "function": {"name": name, "description": desc,
                         "parameters": {"type": "object",
                                        "properties": props,
                                        "required": list(required)}}}

TOOL_SCHEMAS = [
    schema("search_devpost", "Find open hackathons on Devpost.",
           {"keywords": {"type": "string"}}),
    schema("search_hackerearth", "Find open hackathons/challenges on HackerEarth.",
           {"keywords": {"type": "string"}}),
    schema("search_leetcode_contests", "List upcoming LeetCode contests.", {}),
    schema("search_unstop", "Find hackathons, internships, jobs on Unstop.",
           {"keywords": {"type": "string"},
            "kind": {"type": "string", "enum": ["hackathon", "internship", "job"]}}),
    schema("search_internshala", "Find internships on Internshala.",
           {"keywords": {"type": "string"}}, ["keywords"]),
]

def run_tool(name, args):
    try:
        return REGISTRY[name](**args)
    except Exception as e:
        return {"error": str(e)}   # the model sees the error and can recover