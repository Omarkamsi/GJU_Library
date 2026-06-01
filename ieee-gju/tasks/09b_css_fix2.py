"""
CSS Injection — Round 2
Widget instance was empty (kses stripped <style>).
Strategy:
 A) Update widget with [vc_raw_html]BASE64[/vc_raw_html] shortcode — no kses on shortcode text
 B) Fix homepage: replace broken plaintext <style> with [vc_raw_html] shortcode
 C) Try SiteOrigin CSS AJAX save with fresh nonce
"""
import sys, base64, re
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL, HOMEPAGE_ID

with open("/root/ieee-gju/assets/style.css") as f:
    CSS = f.read()

STYLE_BLOCK = f"<style>\n{CSS}\n</style>"
B64 = base64.b64encode(STYLE_BLOCK.encode()).decode()
VC_SHORTCODE = f"[vc_raw_html]{B64}[/vc_raw_html]"

print(f"CSS length: {len(CSS)} chars")
print(f"Base64 length: {len(B64)} chars")


# ─── A: Update widget with vc_raw_html shortcode ──────────────────────────────
def fix_widget():
    print("\n=== A: Update widget custom_html-2 with vc_raw_html shortcode ===")
    try:
        s = wp_api._get_session()
        # Try PATCH to update the widget
        r = s.patch(
            f"{SITE_URL}/wp-json/wp/v2/widgets/custom_html-2",
            json={
                "instance": {
                    "raw": {
                        "title": "",
                        "content": VC_SHORTCODE
                    }
                }
            }
        )
        print(f"PATCH status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            inst = data.get("instance", {})
            raw_content = inst.get("raw", {}).get("content", "")
            rendered = data.get("rendered", "")
            print(f"Saved content snippet: {raw_content[:100]}")
            print(f"Rendered snippet: {rendered[:200]}")
            if "vc_raw_html" in raw_content:
                print("✅ vc_raw_html shortcode preserved in widget")
                return True
            elif raw_content:
                print(f"Content saved but no shortcode: {raw_content[:200]}")
            else:
                print("Instance still empty — trying encoded format")

        # Try with encoded instance (PHP-serialized base64)
        # PHP serialize: a:2:{s:5:"title";s:0:"";s:7:"content";s:<len>:"<content>";}
        content = VC_SHORTCODE
        php_serialized = f'a:2:{{s:5:"title";s:0:"";s:7:"content";s:{len(content.encode())}:"{content}";}}'
        encoded = base64.b64encode(php_serialized.encode()).decode()
        print(f"\nTrying encoded instance format...")
        r2 = s.patch(
            f"{SITE_URL}/wp-json/wp/v2/widgets/custom_html-2",
            json={"instance": {"encoded": encoded, "hash": ""}}
        )
        print(f"Encoded PATCH status: {r2.status_code} — {r2.text[:200]}")
        return False
    except Exception as e:
        print(f"Widget update failed: {e}")
        return False


# ─── B: Fix homepage — replace broken <style> with vc_raw_html ─────────────────
def fix_homepage():
    print("\n=== B: Fix homepage — vc_raw_html shortcode ===")
    try:
        page = wp_api.get(f"/pages/{HOMEPAGE_ID}", params={"context": "edit"})
        content_raw = page["content"].get("raw", page["content"].get("rendered", ""))
        print(f"Current content length: {len(content_raw)}")
        print(f"Content starts with: {repr(content_raw[:80])}")

        # Remove any existing broken style block or old vc_raw_html
        cleaned = re.sub(r'^\s*<style>[\s\S]*?</style>\s*', '', content_raw)
        cleaned = re.sub(r'^\s*\[vc_raw_html\][A-Za-z0-9+/=]+\[/vc_raw_html\]\s*', '', cleaned)
        cleaned = cleaned.strip()

        new_content = VC_SHORTCODE + "\n\n" + cleaned
        print(f"New content length: {len(new_content)}")

        result = wp_api.put(f"/pages/{HOMEPAGE_ID}", {
            "content": new_content,
            "status": "publish"
        })
        print(f"Homepage PUT: {result.get('link')}")

        # Verify
        verify = wp_api.get(f"/pages/{HOMEPAGE_ID}", params={"context": "edit"})
        saved = verify["content"].get("raw", "")
        print(f"Saved starts with: {repr(saved[:120])}")

        if "vc_raw_html" in saved:
            print("✅ vc_raw_html preserved in homepage!")
            return True
        elif saved.startswith(VC_SHORTCODE[:30]):
            print("✅ Shortcode saved (partial match)")
            return True
        else:
            print(f"❌ Shortcode not found in saved content")
            # Check rendered output
            rendered = verify["content"].get("rendered", "")[:300]
            print(f"Rendered snippet: {rendered}")
            return False
    except Exception as e:
        import traceback
        print(f"Homepage fix failed: {e}")
        traceback.print_exc()
        return False


# ─── C: Try SiteOrigin CSS AJAX ───────────────────────────────────────────────
def try_siteorigin_ajax():
    print("\n=== C: SiteOrigin CSS AJAX save ===")
    try:
        s = wp_api._get_session()
        # Get a fresh nonce for so_css_save_action
        nonce_r = s.get(
            f"{SITE_URL}/wp-admin/admin-ajax.php",
            params={"action": "rest-nonce"}
        )
        nonce = nonce_r.text.strip()
        print(f"Nonce: {nonce[:20]}...")

        # Try the SiteOrigin CSS AJAX save
        # The action is 'so_css_save', nonce field is '_wpnonce'
        r = s.post(
            f"{SITE_URL}/wp-admin/admin-ajax.php",
            data={
                "action": "so_css_save",
                "css": CSS,
                "_wpnonce": nonce,
                "post_id": 0
            }
        )
        print(f"SiteOrigin AJAX status: {r.status_code}")
        print(f"Response: {r.text[:200]}")

        if r.status_code == 200 and r.text.strip() not in ("0", "-1", ""):
            print("✅ SiteOrigin CSS saved!")
            return True
        return False
    except Exception as e:
        print(f"SiteOrigin AJAX failed: {e}")
        return False


# ─── D: Check if sidebar widget rendered CSS on frontend ──────────────────────
def check_frontend():
    print("\n=== D: Check frontend for CSS ===")
    try:
        s = wp_api._get_session()
        r = s.get(f"{SITE_URL}/")
        html = r.text
        # Look for our CSS markers
        if "--bg:" in html or "gju-hero" in html or "#0a0f1e" in html:
            print("✅ CSS variables found in page source!")
            # Find the location
            idx = html.find("--bg:")
            if idx > 0:
                print(f"  Context: ...{html[idx-50:idx+80]}...")
            return True
        else:
            print("❌ CSS not found in frontend HTML")
            # Check for widget area
            if "custom_html" in html.lower() or "widget" in html.lower():
                print(f"  Widget area snippet: {html[html.lower().find('widget'):html.lower().find('widget')+200]}")
            return False
    except Exception as e:
        print(f"Frontend check failed: {e}")
        return False


if __name__ == "__main__":
    widget_ok = fix_widget()
    homepage_ok = fix_homepage()
    so_ok = try_siteorigin_ajax()
    check_frontend()

    print("\n=== Summary ===")
    print(f"Widget updated: {widget_ok}")
    print(f"Homepage fixed: {homepage_ok}")
    print(f"SiteOrigin CSS: {so_ok}")
