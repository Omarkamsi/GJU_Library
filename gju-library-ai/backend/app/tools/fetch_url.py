import httpx
import trafilatura

_ALLOWED_DOMAINS = ("gju.edu.jo", "jopuls.org.jo", "openlibrary.org")
_MAX_CHARS = 3_000
_HEADERS = {"User-Agent": "GJULibraryAI/1.0 (+https://library.gju.edu.jo)"}


def fetch_url(url: str) -> str:
    """Fetch a URL and return extracted plain text (allow-listed domains only)."""
    if not any(domain in url for domain in _ALLOWED_DOMAINS):
        return "URL not allowed. Only GJU and JOPULS domains are permitted."

    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True, headers=_HEADERS)
        resp.raise_for_status()
    except Exception as exc:
        return f"Fetch failed: {exc}"

    text = trafilatura.extract(resp.text) or resp.text
    return text[:_MAX_CHARS]
