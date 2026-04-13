# IEEE GJU WordPress Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the IEEE GJU WordPress site (https://edu.ieee.org/jo-gju/) via the REST API — updating the visual design, navigation, homepage, and adding Events, Contact, and News pages — with full undo capability at every step.

**Architecture:** Python scripts call the WordPress REST API using Application Password auth. Every destructive operation is preceded by a local backup saved to `undo-log/`. All new pages are created as drafts and only published after explicit approval. An `undo-log/undo-log.json` records every change with its reversal payload.

**Tech Stack:** Python 3, `requests` library, WordPress REST API v2, HTML/CSS (injected as raw page content)

---

## File Structure

```
/root/ieee-gju/
├── config.py                  # Site URL + credentials (gitignored)
├── wp_api.py                  # Reusable API helper functions
├── undo.py                    # Undo runner — reads undo-log.json and reverses changes
├── undo-log/
│   ├── undo-log.json          # Master log of all changes + reversal payloads
│   ├── original-css.txt       # Backed-up custom CSS before modification
│   ├── menus.json             # Backed-up menu structure
│   └── pages/                 # Backed-up page content keyed by post ID
│       └── <id>.json
├── assets/
│   └── style.css              # Full design system CSS
└── tasks/
    ├── 01_backup.py           # Backup current site state
    ├── 02_discover.py         # Discover WP version, endpoints, theme
    ├── 03_inject_css.py       # Inject design system CSS
    ├── 04_update_nav.py       # Update navigation menu
    ├── 05_homepage.py         # Rewrite homepage content
    ├── 06_events_page.py      # Create Events page (draft)
    ├── 07_contact_page.py     # Create Contact page (draft)
    └── 08_news_page.py        # Create News & Announcements page (draft)
```

---

## Task 1: Project Setup & Credentials

**Files:**
- Create: `/root/ieee-gju/config.py`
- Create: `/root/ieee-gju/.gitignore`

- [ ] **Step 1.1: Create project directory and install dependencies**

```bash
mkdir -p /root/ieee-gju/undo-log/pages /root/ieee-gju/assets /root/ieee-gju/tasks
cd /root/ieee-gju
pip install requests
```

Expected: `Successfully installed requests-X.X.X`

- [ ] **Step 1.2: Generate a WordPress Application Password**

In WordPress admin: go to **Users → Profile → Application Passwords** (scroll to bottom). Enter name "Claude Redesign", click **Add New Application Password**. Copy the generated password — it will only show once.

- [ ] **Step 1.3: Create config.py with credentials**

```python
# /root/ieee-gju/config.py
SITE_URL = "https://edu.ieee.org/jo-gju"
WP_USER = "your_admin_username"          # Replace with your WP admin username
WP_APP_PASSWORD = "xxxx xxxx xxxx xxxx"  # Replace with Application Password from Step 1.2
```

- [ ] **Step 1.4: Create .gitignore**

```
# /root/ieee-gju/.gitignore
config.py
undo-log/
```

- [ ] **Step 1.5: Commit project scaffold**

```bash
cd /root/ieee-gju
git init
git add .gitignore assets/ tasks/
git commit -m "feat: scaffold IEEE GJU redesign project"
```

---

## Task 2: WordPress API Helper

**Files:**
- Create: `/root/ieee-gju/wp_api.py`
- Create: `/root/ieee-gju/undo.py`

- [ ] **Step 2.1: Write wp_api.py**

```python
# /root/ieee-gju/wp_api.py
import requests
import json
import os
from datetime import datetime
from config import SITE_URL, WP_USER, WP_APP_PASSWORD

AUTH = (WP_USER, WP_APP_PASSWORD)
BASE = f"{SITE_URL}/wp-json/wp/v2"
UNDO_LOG = "/root/ieee-gju/undo-log/undo-log.json"


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
    r = requests.get(f"{BASE}{endpoint}", auth=AUTH, params=params)
    r.raise_for_status()
    return r.json()


def post(endpoint, data):
    r = requests.post(f"{BASE}{endpoint}", auth=AUTH, json=data)
    r.raise_for_status()
    return r.json()


def put(endpoint, data):
    r = requests.put(f"{BASE}{endpoint}", auth=AUTH, json=data)
    r.raise_for_status()
    return r.json()


def patch(endpoint, data):
    r = requests.patch(f"{BASE}{endpoint}", auth=AUTH, json=data)
    r.raise_for_status()
    return r.json()


def test_connection():
    """Verify credentials work. Returns site info dict."""
    r = requests.get(f"{SITE_URL}/wp-json/", auth=AUTH)
    r.raise_for_status()
    info = r.json()
    print(f"Connected to: {info.get('name')} (WP {info.get('description', '')})")
    print(f"URL: {info.get('url')}")
    return info
```

- [ ] **Step 2.2: Write undo.py**

```python
# /root/ieee-gju/undo.py
import json
import requests
import sys
from config import WP_USER, WP_APP_PASSWORD

AUTH = (WP_USER, WP_APP_PASSWORD)
UNDO_LOG = "/root/ieee-gju/undo-log/undo-log.json"


def undo_last(n=1):
    with open(UNDO_LOG) as f:
        log = json.load(f)

    if not log:
        print("Nothing to undo.")
        return

    to_reverse = log[-n:]
    remaining = log[:-n]

    for entry in reversed(to_reverse):
        r = entry["reversal"]
        print(f"Undoing: {entry['description']}")
        method = r["method"].upper()
        if method == "PUT":
            resp = requests.put(r["url"], auth=AUTH, json=r["payload"])
        elif method == "POST":
            resp = requests.post(r["url"], auth=AUTH, json=r["payload"])
        elif method == "DELETE":
            resp = requests.delete(r["url"], auth=AUTH)
        resp.raise_for_status()
        print(f"  Done ({resp.status_code})")

    with open(UNDO_LOG, "w") as f:
        json.dump(remaining, f, indent=2)

    print(f"Undid {len(to_reverse)} action(s).")


def undo_all():
    with open(UNDO_LOG) as f:
        log = json.load(f)
    count = len(log)
    undo_last(count)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        undo_all()
    elif len(sys.argv) > 1:
        undo_last(int(sys.argv[1]))
    else:
        undo_last(1)
```

- [ ] **Step 2.3: Test connection**

```bash
cd /root/ieee-gju
python3 -c "import wp_api; wp_api.test_connection()"
```

Expected output:
```
Connected to: IEEE GJU (...)
URL: https://edu.ieee.org/jo-gju
```

If you see a 401 error, re-check the Application Password in config.py — copy it exactly as shown in wp-admin, spaces included.

- [ ] **Step 2.4: Commit helpers**

```bash
cd /root/ieee-gju
git add wp_api.py undo.py
git commit -m "feat: add WP API helper and undo runner"
```

---

## Task 3: Backup Current Site State

**Files:**
- Create: `/root/ieee-gju/tasks/01_backup.py`

- [ ] **Step 3.1: Write backup script**

```python
# /root/ieee-gju/tasks/01_backup.py
import sys, json, os, requests
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL, WP_USER, WP_APP_PASSWORD

AUTH = (WP_USER, WP_APP_PASSWORD)
UNDO_DIR = "/root/ieee-gju/undo-log"
os.makedirs(f"{UNDO_DIR}/pages", exist_ok=True)


def backup_pages():
    pages = wp_api.get("/pages", params={"per_page": 50, "status": "publish"})
    for page in pages:
        pid = page["id"]
        slug = page["slug"]
        path = f"{UNDO_DIR}/pages/{pid}-{slug}.json"
        with open(path, "w") as f:
            json.dump({"id": pid, "content": page["content"]["raw"],
                       "title": page["title"]["raw"],
                       "status": page["status"]}, f, indent=2)
        print(f"  Backed up page: {slug} (id={pid})")


def backup_custom_css():
    # Try global styles endpoint (WP 5.9+)
    try:
        r = requests.get(f"{SITE_URL}/wp-json/wp/v2/global-styles/themes",
                         auth=AUTH)
        if r.status_code == 200:
            data = r.json()
            with open(f"{UNDO_DIR}/global-styles.json", "w") as f:
                json.dump(data, f, indent=2)
            print("  Backed up global styles (WP 5.9+ endpoint)")
            return "global-styles"
    except Exception:
        pass

    # Fallback: check settings for custom_css
    try:
        settings = wp_api.get("/settings")
        css = settings.get("custom_css", "")
        with open(f"{UNDO_DIR}/original-css.txt", "w") as f:
            f.write(css)
        print(f"  Backed up custom CSS ({len(css)} chars)")
        return "settings"
    except Exception as e:
        print(f"  CSS backup via settings failed: {e}")
        return None


def backup_menus():
    # WP 5.9+ menu endpoints
    try:
        menus = wp_api.get("/menus")
        items = wp_api.get("/menu-items", params={"per_page": 100})
        with open(f"{UNDO_DIR}/menus.json", "w") as f:
            json.dump({"menus": menus, "items": items}, f, indent=2)
        print(f"  Backed up {len(menus)} menu(s), {len(items)} item(s)")
    except Exception as e:
        print(f"  Menu backup skipped (endpoint may need plugin): {e}")


if __name__ == "__main__":
    print("=== Backing up site state ===")
    backup_pages()
    backup_custom_css()
    backup_menus()
    print("=== Backup complete ===")
```

- [ ] **Step 3.2: Run backup**

```bash
cd /root/ieee-gju
python3 tasks/01_backup.py
```

Expected output:
```
=== Backing up site state ===
  Backed up page: home (id=2)
  Backed up page: communities (id=5)
  ...
  Backed up custom CSS (NNN chars)
  Backed up X menu(s), Y item(s)
=== Backup complete ===
```

Verify files exist:
```bash
ls /root/ieee-gju/undo-log/pages/
ls /root/ieee-gju/undo-log/
```

- [ ] **Step 3.3: Commit backup scripts (not the backup data — it's gitignored)**

```bash
cd /root/ieee-gju
git add tasks/01_backup.py
git commit -m "feat: add site backup script"
```

---

## Task 4: Discover WordPress Environment

**Files:**
- Create: `/root/ieee-gju/tasks/02_discover.py`

- [ ] **Step 4.1: Write discovery script**

```python
# /root/ieee-gju/tasks/02_discover.py
import sys, requests
sys.path.insert(0, "/root/ieee-gju")
from config import SITE_URL, WP_USER, WP_APP_PASSWORD

AUTH = (WP_USER, WP_APP_PASSWORD)


def check_endpoints():
    base = f"{SITE_URL}/wp-json/wp/v2"
    endpoints = {
        "pages":         f"{base}/pages",
        "posts":         f"{base}/posts",
        "menus":         f"{base}/menus",
        "menu-items":    f"{base}/menu-items",
        "global-styles": f"{base}/global-styles",
        "settings":      f"{base}/settings",
        "themes":        f"{base}/themes",
    }
    print("=== Endpoint Availability ===")
    available = {}
    for name, url in endpoints.items():
        r = requests.get(url, auth=AUTH)
        status = "OK" if r.status_code in (200, 201) else f"FAIL ({r.status_code})"
        print(f"  {name:20s} {status}")
        available[name] = r.status_code == 200
    return available


def check_theme():
    r = requests.get(f"{SITE_URL}/wp-json/wp/v2/themes", auth=AUTH,
                     params={"status": "active"})
    if r.status_code == 200:
        themes = r.json()
        for t in themes:
            print(f"\nActive theme: {t.get('name', {}).get('rendered', 'unknown')}")
            print(f"  Stylesheet: {t.get('stylesheet')}")
            print(f"  Template:   {t.get('template')}")
    else:
        print(f"\nCould not fetch theme info ({r.status_code})")


def check_plugins():
    r = requests.get(f"{SITE_URL}/wp-json/wp/v2/plugins", auth=AUTH)
    if r.status_code == 200:
        plugins = r.json()
        active = [p for p in plugins if p.get("status") == "active"]
        print(f"\nActive plugins ({len(active)}):")
        for p in active:
            name = p.get("name", "unknown")
            print(f"  - {name}")
    else:
        print(f"\nPlugin list not accessible ({r.status_code})")


def check_css_method(available):
    print("\n=== CSS Injection Method ===")
    if available.get("global-styles"):
        print("  Use: /wp/v2/global-styles (WP 5.9+) ✓")
        return "global-styles"
    elif available.get("settings"):
        print("  Use: /wp/v2/settings (custom_css field)")
        return "settings"
    else:
        print("  WARNING: No CSS endpoint found. Will inject via page <style> blocks.")
        return "inline"


if __name__ == "__main__":
    available = check_endpoints()
    check_theme()
    check_plugins()
    method = check_css_method(available)
    print(f"\nSave this: CSS_METHOD = '{method}'")
    print("Update config.py with CSS_METHOD before running Task 5.")
```

- [ ] **Step 4.2: Run discovery**

```bash
cd /root/ieee-gju
python3 tasks/02_discover.py
```

- [ ] **Step 4.3: Add CSS_METHOD to config.py based on discovery output**

Open `/root/ieee-gju/config.py` and add the line printed at the end of the discovery output:

```python
# /root/ieee-gju/config.py
SITE_URL = "https://edu.ieee.org/jo-gju"
WP_USER = "your_admin_username"
WP_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
CSS_METHOD = "global-styles"   # or "settings" or "inline" per discovery output
```

- [ ] **Step 4.4: Commit discovery script**

```bash
cd /root/ieee-gju
git add tasks/02_discover.py
git commit -m "feat: add WP environment discovery script"
```

---

## Task 5: Design System CSS

**Files:**
- Create: `/root/ieee-gju/assets/style.css`
- Create: `/root/ieee-gju/tasks/03_inject_css.py`

- [ ] **Step 5.1: Write the full design system CSS**

```css
/* /root/ieee-gju/assets/style.css */

/* ── Google Fonts ─────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,700;1,400&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Design Tokens ────────────────────────────────────── */
:root {
  --bg:         #0a0f1e;
  --bg-surface: #0d1a3a;
  --primary:    #003087;
  --accent:     #f7b500;
  --text:       #e8edf5;
  --text-muted: #8da0bb;
  --border:     rgba(247,181,0,0.2);
  --radius:     6px;
  --transition: 0.25s ease;
  --font-display: 'Bebas Neue', sans-serif;
  --font-body:    'DM Sans', sans-serif;
  --font-mono:    'JetBrains Mono', monospace;
}

/* ── Base ─────────────────────────────────────────────── */
body, .site {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: var(--font-body) !important;
}

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

h1, h2, h3, h4 {
  font-family: var(--font-display);
  letter-spacing: 0.04em;
  color: var(--text);
}

/* ── Navigation ───────────────────────────────────────── */
#masthead, .site-header, header.site-header {
  background: rgba(10,15,30,0.95) !important;
  border-bottom: 1px solid var(--border) !important;
  position: sticky !important;
  top: 0 !important;
  z-index: 1000 !important;
  backdrop-filter: blur(8px) !important;
}

.site-title a, .site-branding a {
  color: var(--text) !important;
  font-family: var(--font-display) !important;
  font-size: 1.5rem !important;
  letter-spacing: 0.06em !important;
}

/* Primary nav */
.main-navigation ul {
  background: transparent !important;
  gap: 0 !important;
}

.main-navigation ul li a {
  color: var(--text-muted) !important;
  font-family: var(--font-body) !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  padding: 1.5rem 1rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  transition: color var(--transition) !important;
  position: relative !important;
}

.main-navigation ul li a:hover,
.main-navigation ul li.current-menu-item > a {
  color: var(--accent) !important;
}

.main-navigation ul li.current-menu-item > a::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 1rem;
  right: 1rem;
  height: 2px;
  background: var(--accent);
}

/* Dropdown */
.main-navigation ul ul {
  background: var(--bg-surface) !important;
  border: 1px solid var(--border) !important;
  border-top: 2px solid var(--accent) !important;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
}

.main-navigation ul ul li a {
  color: var(--text-muted) !important;
  padding: 0.75rem 1.25rem !important;
  font-size: 0.8rem !important;
  border-left: 2px solid transparent !important;
  transition: all var(--transition) !important;
}

.main-navigation ul ul li a:hover {
  color: var(--accent) !important;
  border-left-color: var(--accent) !important;
  background: rgba(247,181,0,0.05) !important;
}

/* ── Hero Section ─────────────────────────────────────── */
.gju-hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  position: relative;
  overflow: hidden;
  background: var(--bg);
}

.gju-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(247,181,0,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(247,181,0,0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
}

.gju-hero::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 60%, rgba(0,48,135,0.35) 0%, transparent 70%);
  pointer-events: none;
}

.gju-hero-content {
  position: relative;
  z-index: 1;
  max-width: 900px;
  padding: 0 2rem;
}

.gju-hero-eyebrow {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--accent);
  letter-spacing: 0.2em;
  text-transform: uppercase;
  margin-bottom: 1rem;
}

.gju-hero h1 {
  font-family: var(--font-display);
  font-size: clamp(4rem, 10vw, 9rem);
  line-height: 0.9;
  color: var(--text);
  margin: 0 0 1.5rem;
}

.gju-hero h1 span {
  color: var(--accent);
}

.gju-hero-sub {
  font-size: 1.125rem;
  color: var(--text-muted);
  margin-bottom: 2.5rem;
  max-width: 560px;
  margin-left: auto;
  margin-right: auto;
}

.gju-btn {
  display: inline-block;
  padding: 0.875rem 2rem;
  font-family: var(--font-body);
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-radius: var(--radius);
  transition: all var(--transition);
  cursor: pointer;
}

.gju-btn-primary {
  background: var(--accent);
  color: #0a0f1e;
  border: 2px solid var(--accent);
}
.gju-btn-primary:hover {
  background: transparent;
  color: var(--accent);
  text-decoration: none;
}

.gju-btn-ghost {
  background: transparent;
  color: var(--text);
  border: 2px solid rgba(232,237,245,0.3);
  margin-left: 1rem;
}
.gju-btn-ghost:hover {
  border-color: var(--accent);
  color: var(--accent);
  text-decoration: none;
}

/* ── Section Shared ───────────────────────────────────── */
.gju-section {
  padding: 6rem 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.gju-section-label {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--accent);
  letter-spacing: 0.2em;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.gju-section-title {
  font-family: var(--font-display);
  font-size: clamp(2.5rem, 5vw, 4rem);
  color: var(--text);
  margin: 0 0 1rem;
}

.gju-divider {
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, var(--accent), transparent);
  margin: 4rem 0;
}

/* ── About Strip ──────────────────────────────────────── */
.gju-about-strip {
  background: var(--bg-surface);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  padding: 3rem 2rem;
  text-align: center;
}

.gju-about-strip blockquote {
  font-size: clamp(1.125rem, 2vw, 1.5rem);
  font-style: italic;
  color: var(--text-muted);
  max-width: 800px;
  margin: 0 auto 2rem;
  border: none;
  padding: 0;
}

.gju-stats {
  display: flex;
  justify-content: center;
  gap: 4rem;
  flex-wrap: wrap;
}

.gju-stat-number {
  font-family: var(--font-display);
  font-size: 3rem;
  color: var(--accent);
  line-height: 1;
}

.gju-stat-label {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-top: 0.25rem;
}

/* ── Communities Grid ─────────────────────────────────── */
.gju-communities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-top: 3rem;
}

.gju-society-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.75rem;
  transition: all var(--transition);
  position: relative;
  overflow: hidden;
}

.gju-society-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--accent);
  transform: scaleY(0);
  transition: transform var(--transition);
}

.gju-society-card:hover::before { transform: scaleY(1); }

.gju-society-card:hover {
  border-color: rgba(247,181,0,0.4);
  box-shadow: 0 0 24px rgba(247,181,0,0.08);
  transform: translateY(-2px);
}

.gju-society-abbr {
  font-family: var(--font-display);
  font-size: 2.5rem;
  color: var(--accent);
  line-height: 1;
  margin-bottom: 0.5rem;
}

.gju-society-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.75rem;
}

.gju-society-desc {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.6;
}

/* ── Event Cards ──────────────────────────────────────── */
.gju-events-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
  margin-top: 3rem;
}

.gju-event-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.75rem;
  display: flex;
  gap: 1.25rem;
  transition: all var(--transition);
}

.gju-event-card:hover {
  border-color: rgba(247,181,0,0.4);
  box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}

.gju-event-date {
  text-align: center;
  min-width: 56px;
}

.gju-event-day {
  font-family: var(--font-mono);
  font-size: 2.25rem;
  font-weight: 600;
  color: var(--accent);
  line-height: 1;
}

.gju-event-month {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.gju-event-body { flex: 1; }

.gju-event-tag {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 2px;
  padding: 0.1rem 0.4rem;
  margin-bottom: 0.5rem;
}

.gju-event-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.5rem;
}

.gju-event-meta {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

/* ── How to Join ──────────────────────────────────────── */
.gju-join-steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  margin-top: 3rem;
}

@media (max-width: 768px) {
  .gju-join-steps { grid-template-columns: 1fr; }
  .gju-communities-grid { grid-template-columns: 1fr 1fr; }
}

.gju-step-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 2rem;
  text-align: center;
}

.gju-step-number {
  font-family: var(--font-display);
  font-size: 4rem;
  color: var(--accent);
  opacity: 0.4;
  line-height: 1;
  margin-bottom: 1rem;
}

.gju-step-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  color: var(--text);
  margin-bottom: 0.75rem;
}

.gju-step-desc {
  font-size: 0.875rem;
  color: var(--text-muted);
  line-height: 1.6;
}

/* ── Contact Page ─────────────────────────────────────── */
.gju-contact-grid {
  display: grid;
  grid-template-columns: 2fr 3fr;
  gap: 4rem;
  align-items: start;
}

@media (max-width: 900px) {
  .gju-contact-grid { grid-template-columns: 1fr; }
}

.gju-contact-channels { margin-bottom: 2rem; }

.gju-channel-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 0;
  border-bottom: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 0.9rem;
  transition: color var(--transition);
}

.gju-channel-link:hover { color: var(--accent); text-decoration: none; }

.gju-channel-icon {
  width: 32px;
  height: 32px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  flex-shrink: 0;
}

/* Accordion for society contacts */
.gju-accordion-item {
  border-bottom: 1px solid var(--border);
}

.gju-accordion-trigger {
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  color: var(--text);
  font-family: var(--font-body);
  font-size: 0.875rem;
  font-weight: 600;
  padding: 1rem 0;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.gju-accordion-trigger:hover { color: var(--accent); }

.gju-accordion-content {
  display: none;
  padding: 0 0 1rem;
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.8;
}

.gju-accordion-item.open .gju-accordion-content { display: block; }
.gju-accordion-item.open .gju-accordion-trigger { color: var(--accent); }

/* Contact Form */
.gju-form input,
.gju-form select,
.gju-form textarea {
  width: 100%;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-family: var(--font-body);
  font-size: 0.9rem;
  padding: 0.875rem 1rem;
  margin-bottom: 1.25rem;
  outline: none;
  transition: border-color var(--transition);
  box-sizing: border-box;
}

.gju-form input:focus,
.gju-form select:focus,
.gju-form textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(247,181,0,0.1);
}

.gju-form textarea { min-height: 140px; resize: vertical; }

.gju-form label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  margin-bottom: 0.4rem;
}

/* ── Footer ───────────────────────────────────────────── */
.site-footer, #colophon {
  background: var(--bg-surface) !important;
  border-top: 1px solid var(--border) !important;
  color: var(--text-muted) !important;
  padding: 4rem 2rem 2rem !important;
}

.gju-footer-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 3rem;
  max-width: 1200px;
  margin: 0 auto 3rem;
}

@media (max-width: 768px) {
  .gju-footer-grid { grid-template-columns: 1fr; }
}

.gju-footer-brand-name {
  font-family: var(--font-display);
  font-size: 1.5rem;
  color: var(--text);
  margin-bottom: 0.5rem;
}

.gju-footer-tagline {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.gju-footer-heading {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--accent);
  margin-bottom: 1rem;
}

.gju-footer-links a {
  display: block;
  font-size: 0.875rem;
  color: var(--text-muted);
  padding: 0.25rem 0;
  transition: color var(--transition);
}

.gju-footer-links a:hover { color: var(--accent); text-decoration: none; }

.gju-social-row {
  display: flex;
  gap: 0.75rem;
}

.gju-social-btn {
  width: 40px;
  height: 40px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  color: var(--text-muted);
  transition: all var(--transition);
  text-decoration: none;
}

.gju-social-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  text-decoration: none;
}

.gju-footer-bar {
  border-top: 1px solid var(--border);
  padding-top: 2rem;
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-muted);
  max-width: 1200px;
  margin: 0 auto;
}

/* ── News Cards ───────────────────────────────────────── */
.gju-news-featured {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 3rem;
}

.gju-news-featured-body { padding: 2rem; }

.gju-category-tag {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 2px;
  padding: 0.15rem 0.5rem;
  margin-bottom: 0.75rem;
}

.gju-news-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.gju-news-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: all var(--transition);
}

.gju-news-card:hover {
  border-color: rgba(247,181,0,0.4);
  transform: translateY(-2px);
}

.gju-news-card-body { padding: 1.5rem; }

.gju-news-meta {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

/* ── Utility ──────────────────────────────────────────── */
.gju-cta-row {
  text-align: center;
  margin-top: 3rem;
}

.text-accent { color: var(--accent); }
.font-mono { font-family: var(--font-mono); }
.text-muted { color: var(--text-muted); }
```

- [ ] **Step 5.2: Write CSS injection script**

```python
# /root/ieee-gju/tasks/03_inject_css.py
import sys, json, requests
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL, WP_USER, WP_APP_PASSWORD, CSS_METHOD

AUTH = (WP_USER, WP_APP_PASSWORD)

with open("/root/ieee-gju/assets/style.css") as f:
    NEW_CSS = f.read()


def inject_via_global_styles():
    # Get current global styles ID
    r = requests.get(f"{SITE_URL}/wp-json/wp/v2/global-styles/themes",
                     auth=AUTH)
    r.raise_for_status()
    themes = r.json()

    # Get active theme global style
    r2 = requests.get(f"{SITE_URL}/wp-json/wp/v2/global-styles",
                      auth=AUTH)
    r2.raise_for_status()
    styles = r2.json()

    if not styles:
        print("No global styles found. Falling back to settings method.")
        inject_via_settings()
        return

    style_id = styles[0]["id"]
    current = styles[0]

    # Save original for undo
    wp_api.log_undo(
        "inject design system CSS via global-styles",
        "PUT",
        f"{SITE_URL}/wp-json/wp/v2/global-styles/{style_id}",
        {"styles": current.get("styles", {})}
    )

    # Inject new CSS
    existing_css = current.get("styles", {}).get("css", "")
    merged_css = f"/* === GJU REDESIGN === */\n{NEW_CSS}\n/* === END GJU REDESIGN === */"

    result = requests.put(
        f"{SITE_URL}/wp-json/wp/v2/global-styles/{style_id}",
        auth=AUTH,
        json={"styles": {**current.get("styles", {}), "css": merged_css}}
    )
    result.raise_for_status()
    print(f"CSS injected via global-styles (id={style_id})")


def inject_via_settings():
    settings = wp_api.get("/settings")
    original_css = settings.get("custom_css", "")

    wp_api.log_undo(
        "inject design system CSS via settings",
        "PUT",
        f"{SITE_URL}/wp-json/wp/v2/settings",
        {"custom_css": original_css}
    )

    merged = f"/* === GJU REDESIGN === */\n{NEW_CSS}\n/* === END GJU REDESIGN === */"
    result = wp_api.put("/settings", {"custom_css": merged})
    print("CSS injected via settings endpoint")


if __name__ == "__main__":
    if CSS_METHOD == "global-styles":
        inject_via_global_styles()
    elif CSS_METHOD == "settings":
        inject_via_settings()
    else:
        print("CSS_METHOD=inline — CSS will be embedded in each page's <style> block.")
        print("No global CSS to inject. Proceed to Task 6.")
```

- [ ] **Step 5.3: Run CSS injection**

```bash
cd /root/ieee-gju
python3 tasks/03_inject_css.py
```

Expected: `CSS injected via global-styles (id=...)` or `CSS injected via settings endpoint`

- [ ] **Step 5.4: Verify CSS is live**

Open https://edu.ieee.org/jo-gju/ in a browser. The page background should now appear dark navy (`#0a0f1e`). Navigation text should be visible in the new style. If nothing changed, check that the CSS_METHOD in config.py matches the discovery output from Task 4.

- [ ] **Step 5.5: Commit**

```bash
cd /root/ieee-gju
git add assets/style.css tasks/03_inject_css.py
git commit -m "feat: add design system CSS and injection script"
```

---

## Task 6: Update Navigation Menu

**Files:**
- Create: `/root/ieee-gju/tasks/04_update_nav.py`

- [ ] **Step 6.1: Write nav update script**

```python
# /root/ieee-gju/tasks/04_update_nav.py
import sys, json, requests
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL, WP_USER, WP_APP_PASSWORD

AUTH = (WP_USER, WP_APP_PASSWORD)

TOP_LEVEL_ITEMS = [
    {"title": "Home", "url": "/", "order": 1},
    {"title": "Communities", "url": "#", "order": 2},
    {"title": "Events", "url": "/events/", "order": 3},
    {"title": "News & Announcements", "url": "/news/", "order": 4},
    {"title": "How to Join", "url": "/how-to-join/", "order": 5},
    {"title": "Contact Us", "url": "/contact/", "order": 6},
]

SOCIETIES = [
    "Computer Society (CS)",
    "Industrial Electronics (IES)",
    "Engineering in Medicine & Biology (EMBS)",
    "Women in Engineering (WIE)",
    "Industry Applications (IAS)",
    "Robotics & Automation (RAS)",
    "Consumer Technology (CTSoc)",
    "Power & Energy (PES)",
    "Technology & Engineering Management (TEMS)",
    "Aerospace & Electronic Systems (AESS)",
    "SIGHT (Humanitarian Technology)",
]


def get_primary_menu_id():
    menus = wp_api.get("/menus")
    for m in menus:
        if "primary" in m.get("slug", "").lower() or "main" in m.get("slug", "").lower():
            return m["id"]
    if menus:
        print(f"Using first available menu: {menus[0]['name']} (id={menus[0]['id']})")
        return menus[0]["id"]
    raise RuntimeError("No menus found. Create a primary menu in wp-admin first.")


def add_menu_item(menu_id, title, url, parent=0, order=1):
    data = {
        "title": title,
        "url": f"{SITE_URL}{url}" if url.startswith("/") else url,
        "menus": menu_id,
        "menu_order": order,
    }
    if parent:
        data["parent"] = parent
    return wp_api.post("/menu-items", data)


if __name__ == "__main__":
    # Save current menu items for undo
    try:
        current_items = wp_api.get("/menu-items", params={"per_page": 100})
        wp_api.log_undo(
            "update navigation menu items",
            "DELETE",
            f"{SITE_URL}/wp-json/wp/v2/menu-items/BULK",
            {"restore": current_items}
        )
    except Exception as e:
        print(f"Warning: could not backup menu items: {e}")

    menu_id = get_primary_menu_id()
    print(f"Updating menu id={menu_id}")

    # Add top-level items
    communities_id = None
    for item in TOP_LEVEL_ITEMS:
        result = add_menu_item(menu_id, item["title"], item["url"], order=item["order"])
        print(f"  Added: {item['title']} (id={result['id']})")
        if item["title"] == "Communities":
            communities_id = result["id"]

    # Add society sub-items under Communities
    if communities_id:
        for i, society in enumerate(SOCIETIES, start=1):
            slug = society.lower().split("(")[0].strip().replace(" ", "-").replace("&", "and")
            result = add_menu_item(
                menu_id, society, f"/communities/{slug}/",
                parent=communities_id, order=i
            )
            print(f"    └── {society} (id={result['id']})")

    print("Navigation update complete.")
```

- [ ] **Step 6.2: Check if menus REST endpoint is available**

From Task 4 discovery output, confirm `menus: OK` was printed. If it showed `FAIL (404)`, the WP REST API Menus plugin may be needed — install it in wp-admin > Plugins > Add New > search "WP REST API Menus".

- [ ] **Step 6.3: Run nav update**

```bash
cd /root/ieee-gju
python3 tasks/04_update_nav.py
```

Expected:
```
Updating menu id=1
  Added: Home (id=10)
  Added: Communities (id=11)
    └── Computer Society (CS) (id=12)
    └── ...
  Added: Events (id=23)
  ...
Navigation update complete.
```

- [ ] **Step 6.4: Verify in browser**

Refresh https://edu.ieee.org/jo-gju/ — hover over Communities to confirm the dropdown shows all 11 societies.

- [ ] **Step 6.5: Commit**

```bash
cd /root/ieee-gju
git add tasks/04_update_nav.py
git commit -m "feat: add navigation menu update script"
```

---

## Task 7: Homepage Redesign

**Files:**
- Create: `/root/ieee-gju/tasks/05_homepage.py`

- [ ] **Step 7.1: Find the homepage post ID**

```bash
cd /root/ieee-gju
python3 -c "
import wp_api
pages = wp_api.get('/pages', params={'slug': 'home', 'per_page': 5})
if not pages:
    pages = wp_api.get('/pages', params={'per_page': 10})
for p in pages:
    print(p['id'], p['slug'], p['link'])
"
```

Note the ID of your homepage (the page set as front page in wp-admin > Settings > Reading).

- [ ] **Step 7.2: Write homepage update script**

```python
# /root/ieee-gju/tasks/05_homepage.py
import sys, json
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

# ← Replace with the homepage post ID from Step 7.1
HOMEPAGE_ID = 2

HOMEPAGE_HTML = """
<style>
/* Page-level overrides */
.entry-content, .page-content { max-width: 100% !important; padding: 0 !important; }
</style>

<!-- HERO -->
<section class="gju-hero">
  <div class="gju-hero-content">
    <p class="gju-hero-eyebrow">IEEE Student Branch · German Jordanian University</p>
    <h1>ENGINEERING<br><span>TOMORROW</span></h1>
    <p class="gju-hero-sub">Connecting engineers, fostering innovation, and building the technical community at GJU.</p>
    <div>
      <a href="/communities/" class="gju-btn gju-btn-primary">Explore Communities</a>
      <a href="/events/" class="gju-btn gju-btn-ghost">Upcoming Events</a>
    </div>
  </div>
</section>

<!-- ABOUT STRIP -->
<div class="gju-about-strip">
  <blockquote>"IEEE's mission is to foster technological innovation and excellence for the benefit of humanity."</blockquote>
  <div class="gju-stats">
    <div>
      <div class="gju-stat-number">11</div>
      <div class="gju-stat-label">Active Societies</div>
    </div>
    <div>
      <div class="gju-stat-number">400K+</div>
      <div class="gju-stat-label">IEEE Members Worldwide</div>
    </div>
    <div>
      <div class="gju-stat-number">160+</div>
      <div class="gju-stat-label">Countries Represented</div>
    </div>
  </div>
</div>

<!-- COMMUNITIES -->
<div style="background:var(--bg);">
<div class="gju-section">
  <p class="gju-section-label">Our Communities</p>
  <h2 class="gju-section-title">Find Your Society</h2>
  <div class="gju-communities-grid">
    <a href="/communities/computer-society/" class="gju-society-card" style="text-decoration:none;">
      <div class="gju-society-abbr">CS</div>
      <div class="gju-society-name">Computer Society</div>
      <div class="gju-society-desc">Cutting-edge software development, AI, cybersecurity, and more.</div>
    </a>
    <a href="/communities/industrial-electronics/" class="gju-society-card" style="text-decoration:none;">
      <div class="gju-society-abbr">IES</div>
      <div class="gju-society-name">Industrial Electronics Society</div>
      <div class="gju-society-desc">Practical applications of electrical engineering across industries.</div>
    </a>
    <a href="/communities/embs/" class="gju-society-card" style="text-decoration:none;">
      <div class="gju-society-abbr">EMBS</div>
      <div class="gju-society-name">Engineering in Medicine &amp; Biology</div>
      <div class="gju-society-desc">Where engineering meets healthcare to advance medical science.</div>
    </a>
    <a href="/communities/wie/" class="gju-society-card" style="text-decoration:none;">
      <div class="gju-society-abbr">WIE</div>
      <div class="gju-society-name">Women in Engineering</div>
      <div class="gju-society-desc">Diversity, inclusion, empowerment, and mentorship in engineering.</div>
    </a>
    <a href="/communities/ias/" class="gju-society-card" style="text-decoration:none;">
      <div class="gju-society-abbr">IAS</div>
      <div class="gju-society-name">Industry Applications Society</div>
      <div class="gju-society-desc">At the intersection of theory and practice for engineers and academics.</div>
    </a>
    <a href="/communities/ras/" class="gju-society-card" style="text-decoration:none;">
      <div class="gju-society-abbr">RAS</div>
      <div class="gju-society-name">Robotics &amp; Automation Society</div>
      <div class="gju-society-desc">Advancing theory and practice in robotics and automation.</div>
    </a>
    <a href="/communities/ctsoc/" class="gju-society-card" style="text-decoration:none;">
      <div class="gju-society-abbr">CTSoc</div>
      <div class="gju-society-name">Consumer Technology Society</div>
      <div class="gju-society-desc">Innovating consumer technologies through conferences and publications.</div>
    </a>
    <a href="/communities/pes/" class="gju-society-card" style="text-decoration:none;">
      <div class="gju-society-abbr">PES</div>
      <div class="gju-society-name">Power &amp; Energy Society</div>
      <div class="gju-society-desc">Scientific and engineering information on electric power and energy.</div>
    </a>
    <a href="/communities/tems/" class="gju-society-card" style="text-decoration:none;">
      <div class="gju-society-abbr">TEMS</div>
      <div class="gju-society-name">Technology &amp; Engineering Management</div>
      <div class="gju-society-desc">Bridging academia, industry, and government.</div>
    </a>
    <a href="/communities/aess/" class="gju-society-card" style="text-decoration:none;">
      <div class="gju-society-abbr">AESS</div>
      <div class="gju-society-name">Aerospace &amp; Electronic Systems</div>
      <div class="gju-society-desc">Advancing systems engineering in aerospace, radar, navigation, and avionics.</div>
    </a>
    <a href="/communities/sight/" class="gju-society-card" style="text-decoration:none;">
      <div class="gju-society-abbr">SIGHT</div>
      <div class="gju-society-name">Humanitarian Technology</div>
      <div class="gju-society-desc">Leveraging technology for sustainable development in underserved communities.</div>
    </a>
  </div>
</div>
</div>

<!-- EVENTS -->
<div style="background:var(--bg-surface); border-top:1px solid var(--border); border-bottom:1px solid var(--border);">
<div class="gju-section">
  <p class="gju-section-label">What's Happening</p>
  <h2 class="gju-section-title">Upcoming Events</h2>
  <div class="gju-events-grid">
    <div class="gju-event-card">
      <div class="gju-event-date">
        <div class="gju-event-day">—</div>
        <div class="gju-event-month">TBD</div>
      </div>
      <div class="gju-event-body">
        <span class="gju-event-tag">Workshop</span>
        <div class="gju-event-title">Add your first event here</div>
        <div class="gju-event-meta">📍 GJU Campus, Madaba</div>
        <a href="/events/" class="gju-btn gju-btn-ghost" style="font-size:0.75rem;padding:0.5rem 1rem;">View Details →</a>
      </div>
    </div>
  </div>
  <div class="gju-cta-row">
    <a href="/events/" class="gju-btn gju-btn-ghost">View All Events →</a>
  </div>
</div>
</div>

<!-- NEWS -->
<div style="background:var(--bg);">
<div class="gju-section">
  <p class="gju-section-label">Latest Updates</p>
  <h2 class="gju-section-title">News &amp; Announcements</h2>
  <div class="gju-news-grid" id="news-preview">
    <div class="gju-news-card">
      <div class="gju-news-card-body">
        <span class="gju-category-tag">Announcement</span>
        <div class="gju-news-meta font-mono">APR 2026</div>
        <h3 style="font-size:1rem;margin:0 0 0.5rem;color:var(--text);">Welcome to the new IEEE GJU website</h3>
        <p style="font-size:0.8rem;color:var(--text-muted);">We've launched our redesigned site. Stay tuned for updates from all our societies.</p>
        <a href="/news/" style="font-size:0.8rem;color:var(--accent);">Read More →</a>
      </div>
    </div>
  </div>
  <div class="gju-cta-row">
    <a href="/news/" class="gju-btn gju-btn-ghost">View All News →</a>
  </div>
</div>
</div>

<!-- HOW TO JOIN -->
<div style="background:var(--bg-surface); border-top:1px solid var(--border);">
<div class="gju-section" style="text-align:center;">
  <p class="gju-section-label">Get Involved</p>
  <h2 class="gju-section-title">How to Join IEEE</h2>
  <div class="gju-join-steps">
    <div class="gju-step-card">
      <div class="gju-step-number">01</div>
      <div class="gju-step-title">Discover</div>
      <p class="gju-step-desc">Explore our 11 active societies and find the one that matches your passion in engineering and technology.</p>
    </div>
    <div class="gju-step-card">
      <div class="gju-step-number">02</div>
      <div class="gju-step-title">Apply</div>
      <p class="gju-step-desc">Complete your IEEE membership application online. Student membership is available at a discounted rate.</p>
    </div>
    <div class="gju-step-card">
      <div class="gju-step-number">03</div>
      <div class="gju-step-title">Connect</div>
      <p class="gju-step-desc">Attend events, join society groups, collaborate on projects, and grow your professional network.</p>
    </div>
  </div>
  <div class="gju-cta-row" style="margin-top:2.5rem;">
    <a href="https://www.ieee.org/membership/join/index.html" target="_blank" class="gju-btn gju-btn-primary">Join IEEE Now →</a>
  </div>
</div>
</div>

<script>
// Accordion JS (for Contact page, loaded globally)
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.gju-accordion-trigger').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var item = this.closest('.gju-accordion-item');
      var isOpen = item.classList.contains('open');
      document.querySelectorAll('.gju-accordion-item').forEach(function(el) {
        el.classList.remove('open');
      });
      if (!isOpen) item.classList.add('open');
    });
  });
});
</script>
"""


if __name__ == "__main__":
    # Backup original
    original = wp_api.get(f"/pages/{HOMEPAGE_ID}")
    wp_api.log_undo(
        "rewrite homepage content",
        "PUT",
        f"{SITE_URL}/wp-json/wp/v2/pages/{HOMEPAGE_ID}",
        {
            "title": original["title"]["raw"],
            "content": original["content"]["raw"],
            "status": original["status"]
        }
    )

    result = wp_api.put(f"/pages/{HOMEPAGE_ID}", {
        "content": HOMEPAGE_HTML,
        "status": "publish"
    })
    print(f"Homepage updated. View at: {result['link']}")
```

- [ ] **Step 7.3: Update HOMEPAGE_ID in the script**

Replace `HOMEPAGE_ID = 2` on line 8 with the actual ID found in Step 7.1.

- [ ] **Step 7.4: Run homepage update**

```bash
cd /root/ieee-gju
python3 tasks/05_homepage.py
```

Expected: `Homepage updated. View at: https://edu.ieee.org/jo-gju/`

- [ ] **Step 7.5: Verify homepage in browser**

Open https://edu.ieee.org/jo-gju/ — you should see the hero, about strip, society grid, events placeholder, news section, and join steps all styled with the new dark design.

- [ ] **Step 7.6: Commit**

```bash
cd /root/ieee-gju
git add tasks/05_homepage.py
git commit -m "feat: add homepage redesign script"
```

---

## Task 8: Events Page

**Files:**
- Create: `/root/ieee-gju/tasks/06_events_page.py`

- [ ] **Step 8.1: Write events page creation script**

```python
# /root/ieee-gju/tasks/06_events_page.py
import sys
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

EVENTS_HTML = """
<style>
.entry-content, .page-content { max-width:100% !important; padding:0 !important; }
</style>

<!-- PAGE HEADER -->
<div style="background:var(--bg-surface);border-bottom:1px solid var(--border);padding:4rem 2rem 3rem;">
  <div style="max-width:1200px;margin:0 auto;">
    <p class="gju-section-label">IEEE GJU</p>
    <h1 style="font-family:var(--font-display);font-size:clamp(3rem,6vw,5rem);margin:0 0 1rem;color:var(--text);">Events</h1>
    <p style="color:var(--text-muted);max-width:560px;">Workshops, seminars, competitions, and networking events from the IEEE Jordan Section and IEEE GJU communities.</p>
  </div>
</div>

<!-- FILTERS -->
<div style="background:var(--bg);border-bottom:1px solid var(--border);position:sticky;top:72px;z-index:100;padding:1rem 2rem;">
  <div style="max-width:1200px;margin:0 auto;display:flex;gap:0.75rem;flex-wrap:wrap;align-items:center;">
    <span style="font-family:var(--font-mono);font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.1em;margin-right:0.5rem;">Filter:</span>
    <button class="gju-filter-btn active" data-filter="all" onclick="filterEvents(this,'all')">All</button>
    <button class="gju-filter-btn" data-filter="this-week" onclick="filterEvents(this,'this-week')">This Week</button>
    <button class="gju-filter-btn" data-filter="this-month" onclick="filterEvents(this,'this-month')">This Month</button>
    <div style="width:1px;height:20px;background:var(--border);margin:0 0.5rem;"></div>
    <button class="gju-filter-btn" data-type="Workshop" onclick="filterByType(this,'Workshop')">Workshop</button>
    <button class="gju-filter-btn" data-type="Seminar" onclick="filterByType(this,'Seminar')">Seminar</button>
    <button class="gju-filter-btn" data-type="Competition" onclick="filterByType(this,'Competition')">Competition</button>
    <button class="gju-filter-btn" data-type="Networking" onclick="filterByType(this,'Networking')">Networking</button>
  </div>
</div>

<style>
.gju-filter-btn {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 0.4rem 0.9rem;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
}
.gju-filter-btn.active, .gju-filter-btn:hover {
  background: var(--accent);
  border-color: var(--accent);
  color: #0a0f1e;
}
</style>

<!-- EVENTS GRID -->
<div style="background:var(--bg);">
<div class="gju-section">
  <div class="gju-events-grid" id="events-container">

    <!-- PLACEHOLDER EVENT 1 -->
    <div class="gju-event-card" data-type="Workshop" data-date="2026-04-20">
      <div class="gju-event-date">
        <div class="gju-event-day">20</div>
        <div class="gju-event-month">APR</div>
      </div>
      <div class="gju-event-body">
        <span class="gju-event-tag">Workshop</span>
        <div class="gju-event-title">[PLACEHOLDER] Add your first event title here</div>
        <div class="gju-event-meta">📍 GJU Campus, Madaba &nbsp;·&nbsp; 🕐 10:00 AM</div>
        <p style="font-size:0.8rem;color:var(--text-muted);margin:0.5rem 0 1rem;">Short description of the event goes here. Update this with actual event details.</p>
        <a href="https://events.vtools.ieee.org" target="_blank" class="gju-btn gju-btn-primary" style="font-size:0.75rem;padding:0.5rem 1rem;">Register →</a>
      </div>
    </div>

    <!-- EMPTY STATE (shown when no events match filter) -->
    <div id="empty-state" style="display:none;grid-column:1/-1;text-align:center;padding:4rem 2rem;">
      <div style="font-family:var(--font-display);font-size:3rem;color:var(--text-muted);margin-bottom:1rem;">NO EVENTS</div>
      <p style="color:var(--text-muted);">No upcoming events match your filter. Check back soon.</p>
      <a href="https://events.vtools.ieee.org" target="_blank" class="gju-btn gju-btn-ghost" style="margin-top:1rem;">Browse IEEE Jordan Events →</a>
    </div>

  </div>
</div>
</div>

<script>
function filterEvents(btn, filter) {
  document.querySelectorAll('[data-filter]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  // Basic filter logic — extend as needed
  var cards = document.querySelectorAll('#events-container .gju-event-card');
  cards.forEach(function(card) { card.style.display = 'flex'; });
}

function filterByType(btn, type) {
  document.querySelectorAll('[data-type]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  var cards = document.querySelectorAll('#events-container .gju-event-card');
  cards.forEach(function(card) {
    card.style.display = (card.dataset.type === type) ? 'flex' : 'none';
  });
  var visible = Array.from(cards).some(c => c.style.display !== 'none');
  document.getElementById('empty-state').style.display = visible ? 'none' : 'grid';
}
</script>
"""


if __name__ == "__main__":
    # Create as draft first
    result = wp_api.post("/pages", {
        "title": "Events",
        "slug": "events",
        "content": EVENTS_HTML,
        "status": "draft"
    })
    page_id = result["id"]

    wp_api.log_undo(
        "create Events page (draft)",
        "DELETE",
        f"{SITE_URL}/wp-json/wp/v2/pages/{page_id}?force=true",
        {}
    )

    print(f"Events page created as DRAFT (id={page_id})")
    print(f"Preview: {result.get('link', '')}?preview=true")
    print("Run publish step after reviewing the preview.")
    print(f"\nTo publish: python3 -c \"import sys; sys.path.insert(0,'/root/ieee-gju'); import wp_api; wp_api.put('/pages/{page_id}', {{'status':'publish'}}); print('Published.')\"")
```

- [ ] **Step 8.2: Run events page creation**

```bash
cd /root/ieee-gju
python3 tasks/06_events_page.py
```

Expected:
```
Events page created as DRAFT (id=XX)
Preview: https://edu.ieee.org/jo-gju/events/?preview=true
```

- [ ] **Step 8.3: Preview the draft in browser**

Open the preview URL printed above. Verify the layout, filters, and event card placeholder look correct.

- [ ] **Step 8.4: Publish events page (after approval)**

Replace `XX` with the actual page ID printed in Step 8.2:
```bash
python3 -c "
import sys; sys.path.insert(0,'/root/ieee-gju')
import wp_api
wp_api.put('/pages/XX', {'status': 'publish'})
print('Events page published.')
"
```

- [ ] **Step 8.5: Commit**

```bash
cd /root/ieee-gju
git add tasks/06_events_page.py
git commit -m "feat: add events page creation script"
```

---

## Task 9: Contact Page

**Files:**
- Create: `/root/ieee-gju/tasks/07_contact_page.py`

- [ ] **Step 9.1: Write contact page creation script**

```python
# /root/ieee-gju/tasks/07_contact_page.py
import sys
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

SOCIETIES_ACCORDION = "\n".join([
    f"""
    <div class="gju-accordion-item">
      <button class="gju-accordion-trigger">{name} <span>+</span></button>
      <div class="gju-accordion-content">
        <strong>Contact:</strong> [PLACEHOLDER Name]<br>
        <strong>Email:</strong> [PLACEHOLDER email@ieee.org]<br>
        <strong>WhatsApp:</strong> <a href="#" style="color:var(--accent);">[PLACEHOLDER link]</a>
      </div>
    </div>"""
    for name in [
        "Computer Society (CS)",
        "Industrial Electronics Society (IES)",
        "Engineering in Medicine & Biology (EMBS)",
        "Women in Engineering (WIE)",
        "Industry Applications Society (IAS)",
        "Robotics & Automation Society (RAS)",
        "Consumer Technology Society (CTSoc)",
        "Power & Energy Society (PES)",
        "Technology & Engineering Management (TEMS)",
        "Aerospace & Electronic Systems (AESS)",
        "SIGHT (Humanitarian Technology)",
    ]
])

CONTACT_HTML = f"""
<style>
.entry-content, .page-content {{ max-width:100% !important; padding:0 !important; }}
</style>

<!-- PAGE HEADER -->
<div style="background:var(--bg-surface);border-bottom:1px solid var(--border);padding:4rem 2rem 3rem;">
  <div style="max-width:1200px;margin:0 auto;">
    <p class="gju-section-label">IEEE GJU</p>
    <h1 style="font-family:var(--font-display);font-size:clamp(3rem,6vw,5rem);margin:0 0 1rem;color:var(--text);">Contact Us</h1>
    <p style="color:var(--text-muted);max-width:560px;">Have a question? Want to join a society? We'd love to hear from you.</p>
  </div>
</div>

<!-- CONTACT GRID -->
<div style="background:var(--bg);">
<div class="gju-section">
  <div class="gju-contact-grid">

    <!-- LEFT: Channels + Society Contacts -->
    <div>
      <p class="gju-section-label" style="margin-bottom:1rem;">Reach Us</p>
      <div class="gju-contact-channels">
        <a href="mailto:[PLACEHOLDER]@ieee.org" class="gju-channel-link">
          <div class="gju-channel-icon">✉</div>
          <span>[PLACEHOLDER]@ieee.org</span>
        </a>
        <a href="https://wa.me/[PLACEHOLDER]" target="_blank" class="gju-channel-link">
          <div class="gju-channel-icon">💬</div>
          <span>WhatsApp Group</span>
        </a>
        <a href="https://www.instagram.com/ieeegju/" target="_blank" class="gju-channel-link">
          <div class="gju-channel-icon">📸</div>
          <span>@ieeegju on Instagram</span>
        </a>
        <a href="[PLACEHOLDER LinkedIn URL]" target="_blank" class="gju-channel-link">
          <div class="gju-channel-icon">💼</div>
          <span>IEEE GJU on LinkedIn</span>
        </a>
      </div>

      <p class="gju-section-label" style="margin:2rem 0 1rem;">Society Contacts</p>
      <div class="gju-accordion">
        {SOCIETIES_ACCORDION}
      </div>
    </div>

    <!-- RIGHT: Contact Form -->
    <div>
      <p class="gju-section-label" style="margin-bottom:1.5rem;">Send a Message</p>
      <form class="gju-form" id="contact-form" onsubmit="handleSubmit(event)">
        <label>Full Name</label>
        <input type="text" name="name" placeholder="Your full name" required>

        <label>Email Address</label>
        <input type="email" name="email" placeholder="your@email.com" required>

        <label>Subject</label>
        <select name="subject" required>
          <option value="" disabled selected>Select a subject</option>
          <option>General Inquiry</option>
          <option>Join a Society</option>
          <option>Event Question</option>
          <option>Partnership</option>
          <option>Other</option>
        </select>

        <label>Message</label>
        <textarea name="message" placeholder="Write your message here..." required></textarea>

        <button type="submit" class="gju-btn gju-btn-primary" style="width:100%;justify-content:center;">
          Send Message
        </button>
      </form>

      <div id="form-success" style="display:none;text-align:center;padding:3rem;background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;">
        <div style="font-family:var(--font-display);font-size:3rem;color:var(--accent);margin-bottom:1rem;">✓</div>
        <h3 style="color:var(--text);margin-bottom:0.5rem;">Message Sent!</h3>
        <p style="color:var(--text-muted);">We'll get back to you soon.</p>
      </div>
    </div>

  </div>
</div>
</div>

<!-- MAP STRIP -->
<div style="background:var(--bg-surface);border-top:1px solid var(--border);padding:3rem 2rem;">
  <div style="max-width:1200px;margin:0 auto;">
    <p class="gju-section-label" style="margin-bottom:1rem;">Find Us</p>
    <div style="border-radius:6px;overflow:hidden;border:1px solid var(--border);">
      <iframe
        src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3391.3!2d35.7!3d31.7!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zGerman+Jordanian+University!5e0!3m2!1sen!2sjo!4v1"
        width="100%" height="320" style="border:0;display:block;filter:grayscale(0.3) invert(0.9) hue-rotate(180deg);"
        allowfullscreen="" loading="lazy">
      </iframe>
    </div>
    <p style="font-size:0.8rem;color:var(--text-muted);margin-top:0.75rem;">German Jordanian University, Mushaqar, Madaba, Jordan</p>
  </div>
</div>

<script>
function handleSubmit(e) {{
  e.preventDefault();
  document.getElementById('contact-form').style.display = 'none';
  document.getElementById('form-success').style.display = 'block';
  // TODO: Wire up to WPForms/CF7 or a mailto: link with actual form submission
}}
</script>
"""


if __name__ == "__main__":
    result = wp_api.post("/pages", {
        "title": "Contact Us",
        "slug": "contact",
        "content": CONTACT_HTML,
        "status": "draft"
    })
    page_id = result["id"]

    wp_api.log_undo(
        "create Contact Us page (draft)",
        "DELETE",
        f"{SITE_URL}/wp-json/wp/v2/pages/{page_id}?force=true",
        {}
    )

    print(f"Contact page created as DRAFT (id={page_id})")
    print(f"Preview: {result.get('link', '')}?preview=true")
    print(f"\nTo publish: python3 -c \"import sys; sys.path.insert(0,'/root/ieee-gju'); import wp_api; wp_api.put('/pages/{page_id}', {{'status':'publish'}}); print('Published.')\"")
```

- [ ] **Step 9.2: Run contact page creation**

```bash
cd /root/ieee-gju
python3 tasks/07_contact_page.py
```

- [ ] **Step 9.3: Preview, then publish**

Open the preview URL. Check the two-column layout, accordion, form, and map. When satisfied:
```bash
python3 -c "
import sys; sys.path.insert(0,'/root/ieee-gju')
import wp_api
wp_api.put('/pages/XX', {'status': 'publish'})
print('Contact page published.')
"
```
Replace `XX` with the actual page ID.

- [ ] **Step 9.4: Commit**

```bash
cd /root/ieee-gju
git add tasks/07_contact_page.py
git commit -m "feat: add contact page creation script"
```

---

## Task 10: News & Announcements Page

**Files:**
- Create: `/root/ieee-gju/tasks/08_news_page.py`

- [ ] **Step 10.1: Write news page creation script**

```python
# /root/ieee-gju/tasks/08_news_page.py
import sys
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

NEWS_HTML = """
<style>
.entry-content, .page-content { max-width:100% !important; padding:0 !important; }
</style>

<!-- PAGE HEADER -->
<div style="background:var(--bg-surface);border-bottom:1px solid var(--border);padding:4rem 2rem 3rem;">
  <div style="max-width:1200px;margin:0 auto;">
    <p class="gju-section-label">IEEE GJU</p>
    <h1 style="font-family:var(--font-display);font-size:clamp(3rem,6vw,5rem);margin:0 0 1rem;color:var(--text);">News &amp; Announcements</h1>
    <p style="color:var(--text-muted);max-width:560px;">The latest updates, achievements, and announcements from IEEE GJU and its societies.</p>
  </div>
</div>

<!-- MAIN CONTENT -->
<div style="background:var(--bg);">
<div style="max-width:1200px;margin:0 auto;padding:4rem 2rem;display:grid;grid-template-columns:1fr 280px;gap:4rem;align-items:start;">

  <!-- POSTS COLUMN -->
  <div>
    <!-- FEATURED POST -->
    <div class="gju-news-featured" style="margin-bottom:3rem;">
      <div style="height:240px;background:linear-gradient(135deg,var(--primary),var(--bg-surface));display:flex;align-items:flex-end;padding:2rem;">
        <div>
          <span class="gju-category-tag">Announcement</span>
          <h2 style="font-family:var(--font-display);font-size:2.5rem;color:var(--text);margin:0.5rem 0 0;">Welcome to the New IEEE GJU Website</h2>
        </div>
      </div>
      <div class="gju-news-featured-body">
        <div class="gju-news-meta font-mono">APR 13, 2026 &nbsp;·&nbsp; IEEE GJU Team</div>
        <p style="color:var(--text-muted);line-height:1.7;margin:0.75rem 0 1.5rem;">We've launched a completely redesigned website for IEEE GJU, featuring updated information about all our societies, upcoming events, and new ways to connect with us. Explore our 11 active communities and join the IEEE family.</p>
        <a href="#" class="gju-btn gju-btn-ghost" style="font-size:0.8rem;padding:0.6rem 1.25rem;">Read More →</a>
      </div>
    </div>

    <!-- POST GRID -->
    <div class="gju-news-grid">
      <div class="gju-news-card">
        <div class="gju-news-card-body">
          <span class="gju-category-tag">Society News</span>
          <div class="gju-news-meta font-mono" style="margin-top:0.5rem;">[PLACEHOLDER DATE]</div>
          <h3 style="font-size:1rem;color:var(--text);margin:0.5rem 0 0.5rem;">[PLACEHOLDER Post Title]</h3>
          <p style="font-size:0.8rem;color:var(--text-muted);">[PLACEHOLDER excerpt — short description of the post.]</p>
          <a href="#" style="font-size:0.8rem;color:var(--accent);">Read More →</a>
        </div>
      </div>
      <div class="gju-news-card">
        <div class="gju-news-card-body">
          <span class="gju-category-tag">Achievement</span>
          <div class="gju-news-meta font-mono" style="margin-top:0.5rem;">[PLACEHOLDER DATE]</div>
          <h3 style="font-size:1rem;color:var(--text);margin:0.5rem 0 0.5rem;">[PLACEHOLDER Post Title]</h3>
          <p style="font-size:0.8rem;color:var(--text-muted);">[PLACEHOLDER excerpt — short description of the post.]</p>
          <a href="#" style="font-size:0.8rem;color:var(--accent);">Read More →</a>
        </div>
      </div>
    </div>

    <!-- PAGINATION -->
    <div style="display:flex;justify-content:center;gap:0.5rem;margin-top:3rem;">
      <button class="gju-filter-btn active">1</button>
      <button class="gju-filter-btn">2</button>
      <button class="gju-filter-btn">3</button>
      <button class="gju-filter-btn">→</button>
    </div>
  </div>

  <!-- SIDEBAR -->
  <div style="position:sticky;top:100px;">
    <div style="background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;padding:1.5rem;margin-bottom:1.5rem;">
      <p class="gju-section-label" style="margin-bottom:0.75rem;">Search</p>
      <input type="search" placeholder="Search posts..." style="width:100%;background:var(--bg);border:1px solid var(--border);border-radius:4px;color:var(--text);font-family:var(--font-body);font-size:0.875rem;padding:0.6rem 0.875rem;box-sizing:border-box;outline:none;">
    </div>

    <div style="background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;padding:1.5rem;margin-bottom:1.5rem;">
      <p class="gju-section-label" style="margin-bottom:0.75rem;">Categories</p>
      <div style="display:flex;flex-direction:column;gap:0.5rem;">
        <a href="#" style="font-size:0.85rem;color:var(--text-muted);padding:0.25rem 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;">Announcements <span class="text-accent">—</span></a>
        <a href="#" style="font-size:0.85rem;color:var(--text-muted);padding:0.25rem 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;">Society News <span class="text-accent">—</span></a>
        <a href="#" style="font-size:0.85rem;color:var(--text-muted);padding:0.25rem 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;">Achievements <span class="text-accent">—</span></a>
        <a href="#" style="font-size:0.85rem;color:var(--text-muted);padding:0.25rem 0;display:flex;justify-content:space-between;">Workshop Recaps <span class="text-accent">—</span></a>
      </div>
    </div>

    <div style="background:var(--bg-surface);border:1px solid var(--border);border-radius:6px;padding:1.5rem;">
      <p class="gju-section-label" style="margin-bottom:0.75rem;">Upcoming Events</p>
      <a href="/events/" class="gju-btn gju-btn-ghost" style="width:100%;text-align:center;display:block;box-sizing:border-box;">View Events →</a>
    </div>
  </div>

</div>
</div>
"""


if __name__ == "__main__":
    result = wp_api.post("/pages", {
        "title": "News & Announcements",
        "slug": "news",
        "content": NEWS_HTML,
        "status": "draft"
    })
    page_id = result["id"]

    wp_api.log_undo(
        "create News & Announcements page (draft)",
        "DELETE",
        f"{SITE_URL}/wp-json/wp/v2/pages/{page_id}?force=true",
        {}
    )

    print(f"News page created as DRAFT (id={page_id})")
    print(f"Preview: {result.get('link', '')}?preview=true")
    print(f"\nTo publish: python3 -c \"import sys; sys.path.insert(0,'/root/ieee-gju'); import wp_api; wp_api.put('/pages/{page_id}', {{'status':'publish'}}); print('Published.')\"")
```

- [ ] **Step 10.2: Run news page creation**

```bash
cd /root/ieee-gju
python3 tasks/08_news_page.py
```

- [ ] **Step 10.3: Preview, then publish**

Open the preview URL. Verify featured post, news grid, and sidebar layout. Then publish:
```bash
python3 -c "
import sys; sys.path.insert(0,'/root/ieee-gju')
import wp_api
wp_api.put('/pages/XX', {'status': 'publish'})
print('News page published.')
"
```

- [ ] **Step 10.4: Commit**

```bash
cd /root/ieee-gju
git add tasks/08_news_page.py
git commit -m "feat: add news and announcements page creation script"
```

---

## Task 11: Final Review & Undo Verification

- [ ] **Step 11.1: Full site walkthrough**

Open each page and verify:
- [ ] Homepage: hero, about strip, society grid, events, news, join steps, footer
- [ ] Nav: sticky header, Communities dropdown with all 11 societies + AESS + SIGHT
- [ ] Events page: filter bar, event card placeholder, empty state logic
- [ ] Contact page: two-column layout, accordion, form, Google Map
- [ ] News page: featured post, grid, sidebar

- [ ] **Step 11.2: Test undo system**

Test that undo works for one change without breaking others:
```bash
cd /root/ieee-gju
# See what's in the undo log
python3 -c "import json; log=json.load(open('undo-log/undo-log.json')); [print(e['description']) for e in log]"

# Undo the last action
python3 undo.py 1

# Undo ALL changes (full rollback)
# python3 undo.py all
```

- [ ] **Step 11.3: Fill in placeholders**

Search all `[PLACEHOLDER]` markers in the live pages. Update them with real data:
- Contact email address
- WhatsApp link
- LinkedIn URL
- Society contact persons and emails
- Map embed with correct GJU coordinates

To find exact GJU coordinates:
```bash
python3 -c "
# GJU Madaba Campus approximate coordinates
# Lat: 31.7167, Lng: 35.7833
# Replace the iframe src in tasks/07_contact_page.py with the correct embed URL from Google Maps
print('Update map iframe src in Contact page via wp_api.put()')
"
```

- [ ] **Step 11.4: Final commit**

```bash
cd /root/ieee-gju
git add -A
git commit -m "feat: complete IEEE GJU website redesign via WP REST API"
```

---

## Undo Reference

| What to undo | Command |
|---|---|
| Last 1 change | `python3 undo.py 1` |
| Last N changes | `python3 undo.py N` |
| Everything | `python3 undo.py all` |
| See undo log | `python3 -c "import json; [print(e['description']) for e in json.load(open('undo-log/undo-log.json'))]"` |
