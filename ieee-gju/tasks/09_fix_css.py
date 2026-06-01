"""
CSS Injection Fix — tries multiple approaches in order:
1. WordPress Widgets REST API (global sidebar → all pages)
2. WordPress Plugins REST API (install custom-css-js plugin)
3. WPBakery vc_raw_html shortcode in homepage (page-level fallback)
"""
import sys, base64, json
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

with open("/root/ieee-gju/assets/style.css") as f:
    CSS = f.read()


# ─── Approach 1: Widgets REST API ─────────────────────────────────────────────
def try_widgets():
    print("\n=== Approach 1: Widgets REST API ===")
    try:
        sidebars = wp_api.get("/sidebars")
        print(f"Sidebars found: {[s['id'] for s in sidebars]}")
        # Pick the first active sidebar
        active = [s for s in sidebars if s.get("status") == "active"]
        if not active:
            active = sidebars  # try all
        if not active:
            print("No sidebars found.")
            return False

        # Use footer sidebar if available, else first
        target = next((s for s in active if "footer" in s["id"].lower()), active[0])
        print(f"Using sidebar: {target['id']}")

        # Create a Custom HTML widget with style block
        style_block = f"<style>\n{CSS}\n</style>"
        payload = {
            "id_base": "custom_html",
            "sidebar": target["id"],
            "instance": {
                "raw": {
                    "title": "",
                    "content": style_block
                }
            }
        }
        result = wp_api.post("/widgets", payload)
        print(f"Widget created: {result.get('id')}")
        wp_api.log_undo(
            "added CSS via Custom HTML widget",
            "DELETE",
            f"{SITE_URL}/wp-json/wp/v2/widgets/{result['id']}",
            {}
        )
        return True
    except Exception as e:
        print(f"Widgets API failed: {e}")
        return False


# ─── Approach 2: Install custom-css-js plugin ──────────────────────────────────
def try_plugin_install():
    print("\n=== Approach 2: Plugins REST API (install custom-css-js) ===")
    try:
        s = wp_api._get_session()
        # Check if endpoint exists
        r = s.get(f"{SITE_URL}/wp-json/wp/v2/plugins")
        print(f"Plugin list status: {r.status_code}")
        if r.status_code == 404:
            print("Plugins endpoint not available (WP < 5.5 or disabled).")
            return False

        # Check if custom-css-js is already installed
        plugins = r.json() if r.status_code == 200 else []
        if isinstance(plugins, list):
            for p in plugins:
                if "custom-css-js" in p.get("plugin", ""):
                    print(f"Plugin already installed: {p.get('plugin')}, status: {p.get('status')}")
                    if p.get("status") != "active":
                        # Activate it
                        slug = p["plugin"]
                        ar = s.put(
                            f"{SITE_URL}/wp-json/wp/v2/plugins/{slug}",
                            json={"status": "active"},
                            headers={"Content-Type": "application/json"}
                        )
                        print(f"Activate result: {ar.status_code} — {ar.text[:200]}")
                    return _inject_via_custom_css_js()

        # Install it
        ir = s.post(
            f"{SITE_URL}/wp-json/wp/v2/plugins",
            json={"slug": "custom-css-js", "status": "active"},
            headers={"Content-Type": "application/json"}
        )
        print(f"Install result: {ir.status_code} — {ir.text[:300]}")
        if ir.status_code in (200, 201):
            return _inject_via_custom_css_js()
        return False
    except Exception as e:
        print(f"Plugin install failed: {e}")
        return False


def _inject_via_custom_css_js():
    """Create a CSS record via the custom-css-js custom post type."""
    print("Injecting CSS via ccss post type...")
    try:
        s = wp_api._get_session()
        r = s.post(
            f"{SITE_URL}/wp-json/wp/v2/ccss",
            json={
                "title": "IEEE GJU Design System",
                "content": CSS,
                "status": "publish",
                "meta": {"ccj_type": "css", "ccj_where": "frontend", "ccj_location": "head"}
            },
            headers={"Content-Type": "application/json"}
        )
        print(f"ccss post result: {r.status_code} — {r.text[:200]}")
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"ccss injection failed: {e}")
        return False


# ─── Approach 3: WPBakery vc_raw_html in homepage ─────────────────────────────
def try_wpbakery_homepage():
    """
    WPBakery's [vc_raw_html] shortcode base64-decodes its content and echoes
    it without kses filtering. Put the style block there.
    """
    print("\n=== Approach 3: WPBakery vc_raw_html shortcode in homepage ===")
    try:
        from config import HOMEPAGE_ID

        # Build the vc_raw_html shortcode with base64-encoded style block
        style_block = f"<style>\n{CSS}\n</style>"
        b64 = base64.b64encode(style_block.encode()).decode()
        css_shortcode = f"[vc_raw_html]{b64}[/vc_raw_html]"

        # Read current homepage to strip any existing broken CSS_BLOCK / shortcode
        page = wp_api.get(f"/pages/{HOMEPAGE_ID}", params={"context": "edit"})
        content_raw = page["content"].get("raw", page["content"].get("rendered", ""))

        # Remove any existing <style>...</style> blob or vc_raw_html at top
        import re
        # Strip inline style block that was injected previously (shows as plaintext)
        content_raw = re.sub(r'^<style>[\s\S]*?</style>\s*', '', content_raw.strip())
        # Strip any existing vc_raw_html CSS shortcode
        content_raw = re.sub(r'^\[vc_raw_html\][A-Za-z0-9+/=]+\[/vc_raw_html\]\s*', '', content_raw.strip())

        new_content = css_shortcode + "\n\n" + content_raw

        wp_api.log_undo(
            "homepage: replaced CSS block with vc_raw_html shortcode",
            "PUT",
            f"{SITE_URL}/wp-json/wp/v2/pages/{HOMEPAGE_ID}",
            {"content": content_raw, "status": page["status"]}
        )

        result = wp_api.put(f"/pages/{HOMEPAGE_ID}", {
            "content": new_content,
            "status": "publish"
        })
        print(f"Homepage updated with vc_raw_html: {result.get('link')}")

        # Verify the shortcode survived
        verify = wp_api.get(f"/pages/{HOMEPAGE_ID}", params={"context": "edit"})
        saved = verify["content"].get("raw", "")
        if "vc_raw_html" in saved:
            print("SUCCESS: vc_raw_html shortcode preserved in content.")
            return True
        else:
            print(f"FAIL: shortcode stripped. Saved content starts with: {saved[:200]}")
            return False
    except Exception as e:
        print(f"WPBakery approach failed: {e}")
        return False


# ─── Approach 4: SiteOrigin CSS via wp_options REST ────────────────────────────
def try_siteorigin_options():
    """
    SiteOrigin CSS stores CSS in wp_options as 'siteorigin_custom_css[<theme>]'.
    Try to write it via the settings REST endpoint.
    """
    print("\n=== Approach 4: SiteOrigin CSS via settings endpoint ===")
    try:
        settings = wp_api.get("/settings")
        print(f"Available settings keys: {list(settings.keys())[:20]}")
        # Look for siteorigin-related key
        so_key = next((k for k in settings if "siteorigin" in k.lower() or "so_css" in k.lower()), None)
        if so_key:
            print(f"Found SiteOrigin key: {so_key}")
            result = wp_api.put("/settings", {so_key: CSS})
            print(f"Settings update result: {result}")
            return True
        else:
            print("No SiteOrigin CSS settings key found via REST.")
            return False
    except Exception as e:
        print(f"Settings approach failed: {e}")
        return False


# ─── Approach 5: Try wp-json/so-css ────────────────────────────────────────────
def try_siteorigin_rest():
    """SiteOrigin CSS may register its own REST namespace."""
    print("\n=== Approach 5: SiteOrigin CSS custom REST endpoint ===")
    try:
        s = wp_api._get_session()
        # Discover namespaces
        r = s.get(f"{SITE_URL}/wp-json/")
        namespaces = r.json().get("namespaces", [])
        print(f"REST namespaces: {namespaces}")

        so_ns = [n for n in namespaces if "siteorigin" in n.lower() or "so-css" in n.lower() or "so_css" in n.lower()]
        print(f"SiteOrigin namespaces: {so_ns}")

        if not so_ns:
            print("No SiteOrigin REST namespace found.")
            return False

        for ns in so_ns:
            r2 = s.get(f"{SITE_URL}/wp-json/{ns}")
            print(f"{ns}: {r2.status_code} — {r2.text[:300]}")
        return False
    except Exception as e:
        print(f"SiteOrigin REST discovery failed: {e}")
        return False


if __name__ == "__main__":
    success = False

    # Try each approach in order
    if not success:
        success = try_widgets()
        if success:
            print("\n✅ SUCCESS via Widgets REST API")

    if not success:
        success = try_plugin_install()
        if success:
            print("\n✅ SUCCESS via Plugin Install")

    if not success:
        success = try_siteorigin_options()

    if not success:
        success = try_siteorigin_rest()

    if not success:
        success = try_wpbakery_homepage()
        if success:
            print("\n✅ SUCCESS via WPBakery vc_raw_html (page-level — homepage only)")

    if not success:
        print("\n❌ All CSS injection approaches failed.")
        print("Manual intervention required — contact IEEE hosting support for Additional CSS access.")
    else:
        print("\n=== Done ===")
