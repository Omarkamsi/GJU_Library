# /root/ieee-gju/wp_api.py
import requests
import json
import os
from datetime import datetime
from config import SITE_URL

BASE = f"{SITE_URL}/wp-json/wp/v2"
UNDO_LOG = "/root/ieee-gju/undo-log/undo-log.json"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

COOKIES = {
    'wpe-auth': '9dba71c25c7bc3844e2e4dd9221c66e20abd9324d8c62952404232e6a58af8ab',
    'wp_lang': 'en_US',
    'wordpress_sec_8567efcacec22616e224b7f1d95cb6ed': 'oalamssi%7C1777254742%7Ctb8q1vmJxFxwXazcVpkW5yj4qFi75ynKpDFTt4L7eq6%7C9c7bdd7a9bad3e74b9538769661a42b627eec75a91b0cfdd8f70b634b0c10027',
    'wordpress_logged_in_8567efcacec22616e224b7f1d95cb6ed': 'oalamssi%7C1777254742%7Ctb8q1vmJxFxwXazcVpkW5yj4qFi75ynKpDFTt4L7eq6%7C3536ea74a5cd509b3bf7f80bb2343585764b515cee392b040b2530dbbf53a2b7',
}

_session = None
_nonce = None


def _get_session():
    global _session, _nonce
    if _session is None:
        try:
            import cloudscraper
            _session = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
            )
        except ImportError:
            _session = requests.Session()
        _session.headers.update(HEADERS)
        _session.cookies.update(COOKIES)
        # Get fresh nonce for REST API write access
        r = _session.get(f"{SITE_URL}/wp-admin/admin-ajax.php?action=rest-nonce")
        r.raise_for_status()
        _nonce = r.text.strip()
        _session.headers.update({'X-WP-Nonce': _nonce})
    return _session


def _load_undo_log():
    if os.path.exists(UNDO_LOG):
        with open(UNDO_LOG) as f:
            return json.load(f)
    return []


def _save_undo_log(log):
    with open(UNDO_LOG, "w") as f:
        json.dump(log, f, indent=2)


def log_undo(description, method, url, payload):
    """Record a reversible action to the undo log."""
    log = _load_undo_log()
    log.append({
        "timestamp": datetime.utcnow().isoformat(),
        "description": description,
        "reversal": {"method": method, "url": url, "payload": payload}
    })
    _save_undo_log(log)


def get(endpoint, params=None):
    s = _get_session()
    r = s.get(f"{BASE}{endpoint}", params=params)
    r.raise_for_status()
    return r.json()


def post(endpoint, data):
    s = _get_session()
    r = s.post(f"{BASE}{endpoint}", json=data)
    r.raise_for_status()
    return r.json()


def put(endpoint, data):
    s = _get_session()
    r = s.put(f"{BASE}{endpoint}", json=data)
    r.raise_for_status()
    return r.json()


def patch(endpoint, data):
    s = _get_session()
    r = s.patch(f"{BASE}{endpoint}", json=data)
    r.raise_for_status()
    return r.json()


def delete(endpoint):
    s = _get_session()
    r = s.delete(f"{BASE}{endpoint}")
    r.raise_for_status()
    return r.json()


def test_connection():
    """Verify session works. Returns site info dict."""
    s = _get_session()
    r = s.get(f"{SITE_URL}/wp-json/")
    r.raise_for_status()
    info = r.json()
    print(f"Connected to: {info.get('name')}")
    print(f"URL: {info.get('url')}")
    print(f"Nonce: {_nonce}")
    me = s.get(f"{BASE}/users/me")
    if me.status_code == 200:
        user = me.json()
        print(f"Authenticated as: {user.get('name')} (roles: {user.get('roles', [])})")
    else:
        print(f"Auth check: {me.status_code} - {me.text[:100]}")
    return info
