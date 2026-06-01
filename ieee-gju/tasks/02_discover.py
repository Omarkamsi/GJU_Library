# /root/ieee-gju/tasks/02_discover.py
import sys, requests
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

def check_endpoints():
    s = wp_api._get_session()
    base = f"{SITE_URL}/wp-json/wp/v2"
    endpoints = {
        "pages":          f"{base}/pages",
        "posts":          f"{base}/posts",
        "menus":          f"{base}/menus",
        "menu-items":     f"{base}/menu-items",
        "global-styles":  f"{base}/global-styles",
        "settings":       f"{base}/settings",
        "themes":         f"{base}/themes",
        "plugins":        f"{base}/plugins",
    }
    print("=== Endpoint Availability ===")
    available = {}
    for name, url in endpoints.items():
        r = s.get(url)
        ok = r.status_code == 200
        available[name] = ok
        print(f"  {name:20s} {'OK' if ok else f'FAIL ({r.status_code})'}")
    return available

def check_theme():
    s = wp_api._get_session()
    r = s.get(f"{SITE_URL}/wp-json/wp/v2/themes", params={"status": "active"})
    if r.status_code == 200 and r.json():
        for t in r.json():
            print(f"\nActive theme: {t.get('name', {}).get('rendered', 'unknown')}")
            print(f"  Stylesheet: {t.get('stylesheet')}")
    else:
        print(f"\nTheme info: {r.status_code}")

def check_css_method(available):
    print("\n=== CSS Injection Method ===")
    if available.get("global-styles"):
        # Check if we can actually write to it
        s = wp_api._get_session()
        r = s.get(f"{SITE_URL}/wp-json/wp/v2/global-styles")
        if r.status_code == 200 and r.json():
            print("  Method: global-styles (WP 5.9+)")
            return "global-styles"
    if available.get("settings"):
        s = wp_api._get_session()
        r = s.get(f"{SITE_URL}/wp-json/wp/v2/settings")
        if r.status_code == 200:
            settings = r.json()
            if "custom_css" in settings:
                print("  Method: settings (custom_css field)")
                return "settings"
    print("  Method: inline (CSS embedded in page content)")
    return "inline"

def get_homepage_id():
    print("\n=== Homepage ===")
    try:
        settings = wp_api.get("/settings")
        page_on_front = settings.get("page_on_front", 0)
        show_on_front = settings.get("show_on_front", "posts")
        print(f"  show_on_front: {show_on_front}")
        print(f"  page_on_front: {page_on_front}")
        if page_on_front:
            page = wp_api.get(f"/pages/{page_on_front}")
            print(f"  Homepage page: [{page_on_front}] {page.get('slug')} — {page['title']['rendered']}")
        return page_on_front
    except Exception as e:
        print(f"  Could not get homepage settings: {e}")
        return None

if __name__ == "__main__":
    available = check_endpoints()
    check_theme()
    css_method = check_css_method(available)
    homepage_id = get_homepage_id()
    print(f"\n=== Summary ===")
    print(f"CSS_METHOD = '{css_method}'")
    print(f"HOMEPAGE_ID = {homepage_id}")
    print("\nUpdate /root/ieee-gju/config.py with these values.")
