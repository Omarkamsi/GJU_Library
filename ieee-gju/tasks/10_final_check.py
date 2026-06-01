"""
Final verification: check all pages are published and CSS is applied.
"""
import sys, re
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

s = wp_api._get_session()

PAGES = [
    (2, "Homepage", SITE_URL + "/"),
    (471, "Events Page (our custom content)", SITE_URL + "/events/"),
    (476, "News & Announcements", SITE_URL + "/news/"),
]

print("=" * 60)
print("IEEE GJU Website — Final Status Check")
print("=" * 60)

# Check page publication status
print("\n── Page Status ──")
for pid, label, url in PAGES:
    page = wp_api.get(f"/pages/{pid}", params={"context": "edit"})
    status = page.get("status")
    link = page.get("link")
    title = page["title"].get("rendered", "")
    content_len = len(page["content"].get("raw", ""))
    has_vc = "[vc_raw_html]" in page["content"].get("raw", "")
    print(f"  [{status}] {label}")
    print(f"     URL: {link}")
    print(f"     Title: {title} | Content: {content_len} chars | CSS shortcode: {has_vc}")

# Check nav menu items
print("\n── Navigation Menu ──")
try:
    menus = wp_api.get("/menus")
    if menus:
        m = menus[0] if isinstance(menus, list) else menus
        print(f"  Menu: {m.get('name')} (ID={m.get('id')})")
        items = wp_api.get(f"/menu-items", params={"menus": m.get('id'), "per_page": 50})
        top_level = [i for i in items if not i.get("parent")]
        for item in top_level:
            print(f"    • {item.get('title', {}).get('rendered', '')} → {item.get('url', '')}")
            children = [c for c in items if c.get("parent") == item.get("id")]
            for child in children:
                print(f"        - {child.get('title', {}).get('rendered', '')} → {child.get('url', '')}")
except Exception as e:
    print(f"  Menu check failed: {e}")

# Check frontend rendering
print("\n── Frontend CSS Check ──")
css_markers = ["--bg:", "gju-hero", "#0a0f1e", "Bebas Neue", "ENGINEERING"]

for pid, label, url in PAGES:
    try:
        r = s.get(url, timeout=15)
        html = r.text
        found = [m for m in css_markers if m in html]
        css_ok = len(found) >= 2
        print(f"  {label} ({r.status_code}): {'✅ CSS applied' if css_ok else '⚠️  CSS not detected'}")
        if found:
            print(f"     Markers found: {found}")
        else:
            # Show first 300 chars of body for debugging
            body_match = re.search(r'<body[^>]*>([\s\S]{0,300})', html)
            if body_match:
                print(f"     Body start: {body_match.group(1)[:100]}")
    except Exception as e:
        print(f"  {label}: Error — {e}")

# Events Calendar check
print("\n── Events Calendar at /events/ ──")
try:
    r = s.get(SITE_URL + "/events/", timeout=15)
    html = r.text
    is_tribe = "tribe_events" in html or "tribe-events" in html
    has_events_list = "tribe-events-list" in html or "tribe-event" in html
    print(f"  Status: {r.status_code}")
    print(f"  Events Calendar template: {is_tribe}")
    print(f"  Has event listings: {has_events_list}")
    # Find event titles
    event_titles = re.findall(r'class="tribe-event-url"[^>]*>([^<]+)', html)
    if event_titles:
        print(f"  Events found: {event_titles[:3]}")
except Exception as e:
    print(f"  Events check failed: {e}")

print("\n── Undo Log ──")
import json, os
undo_log_path = "/root/ieee-gju/undo-log/undo-log.json"
if os.path.exists(undo_log_path):
    with open(undo_log_path) as f:
        log = json.load(f)
    print(f"  {len(log)} reversible actions recorded")
    for entry in log[-5:]:
        print(f"  [{entry['timestamp'][:16]}] {entry['description']}")
else:
    print("  No undo log found")

print("\n=" * 60)
print("Check complete.")
