from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web via DuckDuckGo. Returns formatted results text."""
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        return f"Search failed: {exc}"

    if not hits:
        return "No results found."

    lines: list[str] = []
    for h in hits:
        lines.append(h.get("title", ""))
        lines.append(h.get("href", ""))
        lines.append(h.get("body", ""))
        lines.append("---")
    return "\n".join(lines)
