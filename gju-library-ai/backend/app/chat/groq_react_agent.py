"""ReAct loop using Groq function-calling (OpenAI-compatible format)."""
from __future__ import annotations

import json

from app.llm.groq_client import GroqClient
from app.llm.interface import ChatMessage
from app.tools.fetch_url import fetch_url as _fetch_url
from app.tools.web_search import web_search as _web_search

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the internet for current information about the GJU Library — "
                "staff contacts, hours, events, announcements, or any fact not found "
                "in the provided PASSAGES."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A concise search query, e.g. 'GJU library director site:gju.edu.jo'.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": (
                "Fetch and read the full text of a URL. "
                "Only works for gju.edu.jo, jopuls.org.jo, and openlibrary.org domains."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL to fetch (must be from an allowed domain).",
                    }
                },
                "required": ["url"],
            },
        },
    },
]

_TOOL_FNS = {
    "web_search": lambda args: _web_search(args.get("query", ""), max_results=5),
    "fetch_url": lambda args: _fetch_url(args.get("url", "")),
}


def _execute_tool(name: str, args: dict) -> str:
    fn = _TOOL_FNS.get(name)
    if fn is None:
        return "Unknown tool requested."
    try:
        raw = fn(args)
    except Exception:
        return "Tool execution failed."
    return f"[TOOL_RESULT_START]\n{raw}\n[TOOL_RESULT_END]"


def run_react(
    client: GroqClient,
    messages: list[ChatMessage],
    max_calls: int = 3,
    temperature: float = 0.2,
    max_tokens: int = 600,
) -> str:
    """Run a ReAct tool-calling loop and return the final answer text."""
    groq_msgs = [{"role": m.role, "content": m.content} for m in messages]
    calls_made = 0

    while calls_made < max_calls:
        resp = client.chat_with_tools(
            groq_msgs, _TOOLS, temperature=temperature, max_tokens=max_tokens
        )
        choice = resp.choices[0]

        if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
            return choice.message.content or ""

        # Append assistant turn with tool_calls
        groq_msgs.append(choice.message)

        for tc in choice.message.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except Exception:
                args = {}
            result = _execute_tool(tc.function.name, args)
            calls_made += 1
            groq_msgs.append({
                "role": "tool",
                "content": result,
                "tool_call_id": tc.id,
            })

    # Max calls reached — force final answer without tools
    final = client.chat_with_tools(
        groq_msgs, None, temperature=temperature, max_tokens=max_tokens
    )
    return final.choices[0].message.content or ""
