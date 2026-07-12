from urllib.parse import urlparse

import httpx
import trafilatura

# Exact hostname match — subdomain prefix is fine, path/query must not influence the check.
_ALLOWED_HOSTS = {"gju.edu.jo", "jopuls.org.jo", "openlibrary.org"}
_MAX_CHARS = 3_000
_HEADERS = {"User-Agent": "GJULibraryAI/1.0 (+https://library.gju.edu.jo)"}


def _host_allowed(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception:
        return False
    if p.scheme not in ("http", "https"):
        return False
    host = (p.hostname or "").rstrip(".").lower()
    # Reject IP literals to prevent SSRF to internal addresses.
    if not host or host.replace(".", "").isdigit():
        return False
    return any(host == d or host.endswith("." + d) for d in _ALLOWED_HOSTS)


def fetch_url(url: str) -> str:
    """Fetch a URL and return extracted plain text (allow-listed domains only)."""
    if not _host_allowed(url):
        return "URL not allowed. Only GJU and JOPULS domains are permitted."

    try:
        # Disable automatic redirect-following; re-validate each hop manually.
        resp = httpx.get(url, timeout=10, follow_redirects=False, headers=_HEADERS)
        # Follow up to 3 redirects, re-checking the host at every hop.
        hops = 0
        while resp.is_redirect and hops < 3:
            location = resp.headers.get("location", "")
            if not _host_allowed(location):
                return "Redirect to non-allowed host blocked."
            resp = httpx.get(location, timeout=10, follow_redirects=False, headers=_HEADERS)
            hops += 1
        resp.raise_for_status()
    except Exception:
        return "Fetch failed."

    text = trafilatura.extract(resp.text) or resp.text
    return text[:_MAX_CHARS]
