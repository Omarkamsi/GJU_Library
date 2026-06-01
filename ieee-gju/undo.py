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
