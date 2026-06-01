"""
Add [vc_raw_html] CSS shortcode to Events and News pages.
Homepage already has it. Contact page skipped per user request.
"""
import sys, base64, re
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

with open("/root/ieee-gju/assets/style.css") as f:
    CSS = f.read()

STYLE_BLOCK = f"<style>\n{CSS}\n</style>"
B64 = base64.b64encode(STYLE_BLOCK.encode()).decode()
VC_SHORTCODE = f"[vc_raw_html]{B64}[/vc_raw_html]"

# Pages to update: (page_id, description)
PAGES = [
    (471, "Events"),
    (476, "News & Announcements"),
]


def add_css_to_page(page_id, label):
    print(f"\n=== Adding CSS to {label} (ID={page_id}) ===")
    try:
        page = wp_api.get(f"/pages/{page_id}", params={"context": "edit"})
        content_raw = page["content"].get("raw", page["content"].get("rendered", ""))
        print(f"  Current length: {len(content_raw)}")

        # Strip any existing broken style block or old vc_raw_html
        cleaned = re.sub(r'^\s*<style>[\s\S]*?</style>\s*', '', content_raw)
        cleaned = re.sub(r'^\s*\[vc_raw_html\][A-Za-z0-9+/=]+\[/vc_raw_html\]\s*', '', cleaned)
        cleaned = cleaned.strip()

        new_content = VC_SHORTCODE + "\n\n" + cleaned

        result = wp_api.put(f"/pages/{page_id}", {
            "content": new_content,
            "status": "publish"
        })
        print(f"  Updated: {result.get('link')}")

        # Verify
        verify = wp_api.get(f"/pages/{page_id}", params={"context": "edit"})
        saved = verify["content"].get("raw", "")
        if "vc_raw_html" in saved:
            print(f"  ✅ CSS shortcode preserved")
            return True
        else:
            print(f"  ❌ Shortcode not found. Saved: {saved[:100]}")
            return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def check_page_frontend(page_id, label, slug):
    """Check if CSS appears in the page's frontend HTML."""
    print(f"\n=== Frontend check: {label} ===")
    try:
        s = wp_api._get_session()
        r = s.get(f"{SITE_URL}/{slug}/")
        html = r.text
        if "--bg:" in html or "gju-hero" in html or "#0a0f1e" in html:
            print(f"  ✅ CSS found on {label} frontend")
            return True
        else:
            print(f"  ❌ CSS not found on {label} frontend (status: {r.status_code})")
            # Print rendered content snippet to debug
            idx = html.find("vc_raw_html")
            if idx >= 0:
                print(f"  vc_raw_html in source at {idx}: {html[idx:idx+100]}")
            return False
    except Exception as e:
        print(f"  Check failed: {e}")
        return False


if __name__ == "__main__":
    results = {}
    for pid, lbl in PAGES:
        results[lbl] = add_css_to_page(pid, lbl)

    # Also delete the empty CSS widget since it's not working for global CSS
    print("\n=== Cleaning up empty widget ===")
    try:
        s = wp_api._get_session()
        r = s.delete(f"{SITE_URL}/wp-json/wp/v2/widgets/custom_html-2?force=true")
        print(f"Widget delete: {r.status_code}")
    except Exception as e:
        print(f"Widget cleanup: {e}")

    # Frontend checks
    check_page_frontend(2, "Homepage", "jo-gju")
    check_page_frontend(471, "Events", "jo-gju/events")
    check_page_frontend(476, "News", "jo-gju/news")

    print("\n=== Summary ===")
    for lbl, ok in results.items():
        print(f"  {lbl}: {'✅' if ok else '❌'}")
