# /root/ieee-gju/tasks/04_update_nav.py
import sys, json
sys.path.insert(0, "/root/ieee-gju")
import wp_api
from config import SITE_URL

def get_primary_menu():
    """Find the primary/main navigation menu."""
    s = wp_api._get_session()
    r = s.get(f"{SITE_URL}/wp-json/wp/v2/menus")
    r.raise_for_status()
    menus = r.json()
    print(f"Found {len(menus)} menu(s):")
    for m in menus:
        print(f"  [{m['id']}] {m['name']} (slug: {m['slug']})")
    # Pick the primary/main menu
    for m in menus:
        if any(k in m.get('slug','').lower() for k in ['primary','main','header','nav']):
            return m['id'], m['name']
    # Fallback: first menu
    if menus:
        return menus[0]['id'], menus[0]['name']
    raise RuntimeError("No menus found")

def get_menu_items(menu_id):
    """Get current items in a menu."""
    s = wp_api._get_session()
    r = s.get(f"{SITE_URL}/wp-json/wp/v2/menu-items", params={"menus": menu_id, "per_page": 100})
    r.raise_for_status()
    items = r.json()
    print(f"  Current items: {len(items)}")
    for item in items:
        parent = f" (parent={item['parent']})" if item['parent'] else ""
        print(f"    [{item['id']}] order={item['menu_order']} '{item['title']['rendered']}' → {item['url']}{parent}")
    return items

def add_menu_item(menu_id, title, url, parent=0, order=99):
    """Add a new menu item."""
    s = wp_api._get_session()
    data = {
        "title": title,
        "url": url if url.startswith('http') else f"{SITE_URL}{url}",
        "menus": menu_id,
        "menu_order": order,
        "status": "publish",
    }
    if parent:
        data["parent"] = parent
    r = s.post(f"{SITE_URL}/wp-json/wp/v2/menu-items", json=data)
    if r.status_code in (200, 201):
        item = r.json()
        print(f"  + Added: '{title}' (id={item['id']})")
        return item
    else:
        print(f"  ! Failed to add '{title}': {r.status_code} — {r.text[:200]}")
        return None

if __name__ == "__main__":
    menu_id, menu_name = get_primary_menu()
    print(f"\nUpdating menu: '{menu_name}' (id={menu_id})")

    current_items = get_menu_items(menu_id)
    existing_titles = [i['title']['rendered'].lower() for i in current_items]

    # Log undo — save current state
    wp_api.log_undo(
        "update navigation menu — add Events, News, AESS, SIGHT items",
        "PUT",
        f"{SITE_URL}/wp-json/wp/v2/menus/{menu_id}",
        {"items": current_items}
    )

    # Find the "Communities" parent item
    communities_item = next(
        (i for i in current_items if 'communit' in i['title']['rendered'].lower()),
        None
    )
    communities_id = communities_item['id'] if communities_item else 0
    print(f"\nCommunities parent item: {communities_id}")

    # Get max current order
    max_order = max((i['menu_order'] for i in current_items), default=10)

    # Add top-level items if missing
    added = []
    if not any('event' in t for t in existing_titles):
        item = add_menu_item(menu_id, "Events", "/events/", order=max_order+1)
        if item: added.append(item)
    else:
        print("  Events already exists, skipping")

    if not any('news' in t or 'announcement' in t for t in existing_titles):
        item = add_menu_item(menu_id, "News & Announcements", "/news/", order=max_order+2)
        if item: added.append(item)
    else:
        print("  News already exists, skipping")

    # Add missing society sub-items under Communities
    societies_to_add = []
    if not any('aess' in t or 'aerospace' in t for t in existing_titles):
        societies_to_add.append(("Aerospace & Electronic Systems (AESS)", "/communities/aess/"))
    if not any('sight' in t or 'humanitarian' in t for t in existing_titles):
        societies_to_add.append(("SIGHT (Humanitarian Technology)", "/communities/sight/"))

    for title, url in societies_to_add:
        item = add_menu_item(menu_id, title, url, parent=communities_id, order=max_order+10)
        if item: added.append(item)

    print(f"\nDone. Added {len(added)} new menu item(s).")
    print("\nFinal menu state:")
    get_menu_items(menu_id)
