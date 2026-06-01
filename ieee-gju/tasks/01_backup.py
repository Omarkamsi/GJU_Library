# /root/ieee-gju/tasks/01_backup.py
import sys, json, os, requests
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

UNDO_DIR = "/root/ieee-gju/undo-log"
os.makedirs(f"{UNDO_DIR}/pages", exist_ok=True)


def backup_pages():
    all_pages = []
    page_num = 1
    while True:
        try:
            batch = wp_api.get("/pages", params={"per_page": 100, "page": page_num, "context": "edit"})
            if not batch:
                break
            all_pages.extend(batch)
            page_num += 1
        except Exception:
            # No more pages or API error
            break
    for page in all_pages:
        pid = page["id"]
        slug = page["slug"]
        path = f"{UNDO_DIR}/pages/{pid}-{slug}.json"
        with open(path, "w") as f:
            json.dump({
                "id": pid,
                "content": page["content"]["raw"],
                "title": page["title"]["raw"],
                "status": page["status"],
                "slug": slug,
                "link": page.get("link", "")
            }, f, indent=2)
        print(f"  Backed up page: [{pid}] {slug}")
    return all_pages


def backup_menus():
    try:
        s = wp_api._get_session()
        base = f"{SITE_URL}/wp-json/wp/v2"
        menus_r = s.get(f"{base}/menus")
        items_r = s.get(f"{base}/menu-items", params={"per_page": 100})
        if menus_r.status_code == 200 and items_r.status_code == 200:
            with open(f"{UNDO_DIR}/menus.json", "w") as f:
                json.dump({"menus": menus_r.json(), "items": items_r.json()}, f, indent=2)
            print(f"  Backed up {len(menus_r.json())} menu(s), {len(items_r.json())} item(s)")
        else:
            print(f"  Menu backup: {menus_r.status_code} / {items_r.status_code}")
    except Exception as e:
        print(f"  Menu backup skipped: {e}")


def backup_custom_css():
    try:
        s = wp_api._get_session()
        # Try global styles (WP 5.9+)
        r = s.get(f"{SITE_URL}/wp-json/wp/v2/global-styles", params={"per_page": 10})
        if r.status_code == 200 and r.json():
            with open(f"{UNDO_DIR}/global-styles.json", "w") as f:
                json.dump(r.json(), f, indent=2)
            print(f"  Backed up global styles ({len(r.json())} entries)")
            return
    except Exception:
        pass
    try:
        settings = wp_api.get("/settings")
        css = settings.get("custom_css", "")
        with open(f"{UNDO_DIR}/original-css.txt", "w") as f:
            f.write(css or "")
        print(f"  Backed up custom CSS ({len(css or '')} chars)")
    except Exception as e:
        print(f"  CSS backup skipped: {e}")


if __name__ == "__main__":
    print("=== Backing up site state ===")
    pages = backup_pages()
    print(f"  Total pages backed up: {len(pages)}")
    backup_menus()
    backup_custom_css()
    print("=== Backup complete ===")
    print(f"Files saved to: {UNDO_DIR}/")
