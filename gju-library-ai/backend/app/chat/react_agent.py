"""ReAct (Reason + Act) loop using Gemini function-calling."""
from __future__ import annotations

from google.genai import types

from app.llm.gemini_client import GeminiClient
from app.llm.interface import ChatMessage
from app.tools.fetch_url import fetch_url as _fetch_url
from app.tools.web_search import web_search as _web_search

_WEB_SEARCH_DECL = types.FunctionDeclaration(
    name="web_search",
    description=(
        "Search the internet for current information about the GJU Library — "
        "staff contacts, hours, events, announcements, or any fact not found "
        "in the provided PASSAGES."
    ),
    parameters={
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": (
                    "A concise search query. Prefer queries like "
                    "'GJU library director contact site:gju.edu.jo'."
                ),
            }
        },
        "required": ["query"],
    },
)

_FETCH_URL_DECL = types.FunctionDeclaration(
    name="fetch_url",
    description=(
        "Fetch and read the full text of a URL. "
        "Only works for gju.edu.jo, jopuls.org.jo, and openlibrary.org domains."
    ),
    parameters={
        "type": "OBJECT",
        "properties": {
            "url": {
                "type": "STRING",
                "description": "The full URL to fetch (must be from an allowed domain).",
            }
        },
        "required": ["url"],
    },
)

_TOOLS = types.Tool(function_declarations=[_WEB_SEARCH_DECL, _FETCH_URL_DECL])

_TOOL_FNS = {
    "web_search": lambda args: _web_search(args.get("query", ""), max_results=5),
    "fetch_url": lambda args: _fetch_url(args.get("url", "")),
}


def _execute_tool(name: str, args: dict) -> str:
    fn = _TOOL_FNS.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    try:
        return fn(args)
    except Exception as exc:
        return f"Tool error: {exc}"


def run_react(
    client: GeminiClient,
    messages: list[ChatMessage],
    max_calls: int = 3,
    temperature: float = 0.2,
    max_tokens: int = 600,
) -> str:
    """Run a ReAct tool-calling loop and return the final answer text."""
    contents, system_instruction = client._build_contents(messages)
    calls_made = 0

    while calls_made < max_calls:
        response = client.generate_raw(
            contents,
            system_instruction,
            tools=[_TOOLS],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        candidate = response.candidates[0]
        model_content = candidate.content

        func_call_part = None
        for part in model_content.parts:
            if hasattr(part, "function_call") and part.function_call:
                func_call_part = part
                break

        if func_call_part is None:
            return "".join(
                p.text for p in model_content.parts if hasattr(p, "text") and p.text
            )

        fc = func_call_part.function_call
        tool_result = _execute_tool(fc.name, dict(fc.args))
        calls_made += 1

        contents.append(model_content)
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_function_response(
                        name=fc.name,
                        response={"result": tool_result},
                    )
                ],
            )
        )

    # Max calls reached — force final answer without tools
    final = client.generate_raw(
        contents,
        system_instruction,
        tools=None,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return "".join(
        p.text
        for p in final.candidates[0].content.parts
        if hasattr(p, "text") and p.text
    )
