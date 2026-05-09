#!/usr/bin/env python3
"""Hit /chat for each eval query, print compact audit row.
Run: python3 evals/run_eval.py
"""
import json
import re
import sys
import time
import urllib.request

BASE = "http://localhost:8080"
EMAIL = "alkilanymustafa@gju.edu.jo"
COOKIE_FILE = "/tmp/gju.cookies.eval"


def post(path, body, cookie=None, return_headers=False):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **({"Cookie": cookie} if cookie else {})},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        h = r.headers
        body = r.read()
        return body, h


def login():
    _, h = post("/auth/login", {"email": EMAIL}, return_headers=True)
    set_cookie = h.get("set-cookie") or ""
    return set_cookie.split(";", 1)[0]


def main():
    cookie = login()
    queries = [json.loads(l) for l in open("evals/queries.jsonl")]
    n_total = len(queries)
    cite_ok = 0
    db_ok = 0
    refuse_ok = 0
    lang_ok = 0
    refusal_words = {
        "en": [
            "contact the library", "do not contain", "don't contain",
            "not available", "couldn't find", "do not have", "i don't have",
            "reach out to the library", "recommend reaching out",
        ],
        "ar": [
            "تواصل مع المكتبة", "لا أملك", "لم أجد", "لا تتضمن", "ليست متوفرة",
            "ليست متاحة", "اتصل بالمكتبة",
        ],
        "de": [
            "bibliothek kontaktieren", "habe ich nicht", "keine information",
            "nicht verfügbar", "nicht enthalten",
        ],
    }
    print(f"{'Q':<48}{'lang':<5}{'kind':<8}{'cite':<6}{'db':<6}{'refuse':<8}{'lat_ms':<8}answer")
    print("-" * 130)
    for q in queries:
        body, _ = post("/chat", {"query": q["q"]}, cookie=cookie)
        d = json.loads(body)
        ans = d.get("answer_text", "") or ""
        lang_resp = d.get("lang", "?")
        lat = d.get("latency_ms", 0)
        cites = re.findall(r"\[P\d+\]", ans)
        dbs = re.findall(r"\[DB:[a-z0-9-]+\]", ans)
        # for kind in ('hours','location','contact','remote','db','refuse')
        kind = q.get("expect_kind", "?")
        # citation expectation
        cite_pass = (len(cites) > 0) if q.get("needs_passage") else True
        # db expectation
        if q.get("expect_db"):
            db_pass = q["expect_db"] in ans or q["expect_db"] in [s.get("slug") for s in d.get("suggested_databases", [])]
        else:
            db_pass = True
        # refusal expectation
        if kind == "refuse":
            refuse_pass = any(w.lower() in ans.lower() for w in refusal_words.get(lang_resp, []))
        else:
            refuse_pass = True
        # language match
        lang_pass = (lang_resp == q["lang"])
        cite_ok += int(cite_pass)
        db_ok += int(db_pass)
        refuse_ok += int(refuse_pass)
        lang_ok += int(lang_pass)
        print(f"{q['q'][:46]:<48}{lang_resp:<5}{kind:<8}{'✓' if cite_pass else '✗':<6}{'✓' if db_pass else '✗':<6}{'✓' if refuse_pass else '✗':<8}{lat:<8}{ans[:80]}")
    print("-" * 130)
    print(f"Totals: cite {cite_ok}/{n_total}  db {db_ok}/{n_total}  refuse {refuse_ok}/{n_total}  lang {lang_ok}/{n_total}")


if __name__ == "__main__":
    main()
