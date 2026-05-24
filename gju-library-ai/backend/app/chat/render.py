import re
import secrets
from dataclasses import dataclass
from typing import Any

CLICK_ID_LEN = 12


@dataclass
class PendingClick:
    id: str
    target_type: str  # database | external | passage
    target_ref: str | None
    target_url: str


@dataclass
class RenderInput:
    answer_raw: str
    databases: list[tuple[str, str, str]]  # (slug, name, url)
    passages: list[int]
    base_url: str


@dataclass
class RenderOutput:
    segments: list[dict[str, Any]]
    answer_text: str
    clicks: list[PendingClick]


DB_TOKEN_RE = re.compile(r"\[DB:([a-z0-9_-]+)\]")
# Tolerate model misbehavior: [P12], [P12, P34], [P 12, P34], [P12،P34] (Arabic comma).
P_TOKEN_RE = re.compile(r"\[P\s*(\d+(?:\s*[,،]\s*P?\s*\d+)*)\]")
URL_RE = re.compile(r"https?://[^\s)\]]+")

# Matches the book card block the LLM produces per the system prompt template.
# Uses [^\n]*? after each emoji to absorb optional variation selectors (U+FE0F).
CARD_RE = re.compile(
    r"Yes,\s+GJU Library holds this book[^\n]*?\[P\s*(\d+(?:\s*[,،]\s*P?\s*\d+)*)\][^\n]*\n"
    r"\s*📖[^\n]*?Title:\s*([^\n]+)\n"
    r"\s*✍[^\n]*?Author:\s*([^\n]+)\n"
    r"\s*🏷[^\n]*?Genre[^\n]*?Subject:\s*([^\n]+)\n"
    r"\s*🔢[^\n]*?Call Number:\s*([^\n]+)\n"
    r"\s*📅[^\n]*?Publication Year:\s*([^\n]+)\n"
    r"\s*🔍[^\n]*?Check availability[^\n]*?:\s*(https?://[^\s\n]+)",
    re.UNICODE,
)


def _new_click_id() -> str:
    return "c_" + secrets.token_urlsafe(9)[:CLICK_ID_LEN]


def _push_text(segments: list[dict], buf: str) -> None:
    if not buf:
        return
    if segments and segments[-1]["type"] == "text":
        segments[-1]["value"] += buf
    else:
        segments.append({"type": "text", "value": buf})


def render_answer(inp: RenderInput) -> RenderOutput:
    # Pre-pass: locate all book card blocks
    _card_spans: dict[int, tuple[int, dict, PendingClick]] = {}
    for m in CARD_RE.finditer(inp.answer_raw):
        cid = _new_click_id()
        opac_url = m.group(7).strip()
        _card_spans[m.start()] = (
            m.end(),
            {
                "type": "book_card",
                "title": m.group(2).strip().rstrip(" ."),
                "author": m.group(3).strip().rstrip(" ."),
                "genre": m.group(4).strip().rstrip(" ."),
                "call_number": m.group(5).strip(),
                "year": m.group(6).strip().rstrip(" ."),
                "opac_url": opac_url,
                "passage_ids": [int(x) for x in re.findall(r"\d+", m.group(1))],
                "click_id": cid,
            },
            PendingClick(cid, "external", None, opac_url),
        )

    db_by_slug = {slug: (name, url) for slug, name, url in inp.databases}
    known_passages = set(inp.passages)
    segments: list[dict[str, Any]] = []
    clicks: list[PendingClick] = []

    s = inp.answer_raw
    pos = 0
    while pos < len(s):
        # Card takes priority over all other token types
        if pos in _card_spans:
            end, seg, click = _card_spans[pos]
            segments.append(seg)
            clicks.append(click)
            pos = end
            continue

        next_card = min((k for k in _card_spans if k > pos), default=len(s))

        m_db = DB_TOKEN_RE.search(s, pos)
        m_p = P_TOKEN_RE.search(s, pos)
        m_u = URL_RE.search(s, pos)
        # Only consider matches before the next card block
        candidates = [m for m in (m_db, m_p, m_u) if m and m.start() < next_card]
        if not candidates:
            _push_text(segments, s[pos:next_card])
            pos = next_card
            continue
        m = min(candidates, key=lambda x: x.start())
        if m.start() > pos:
            _push_text(segments, s[pos:m.start()])

        if m is m_db:
            slug = m.group(1)
            if slug in db_by_slug:
                name, url = db_by_slug[slug]
                cid = _new_click_id()
                clicks.append(PendingClick(cid, "database", slug, url))
                segments.append(
                    {
                        "type": "link",
                        "click_id": cid,
                        "label": name,
                        "kind": "database",
                        "ref": slug,
                    }
                )
            # unknown slug → silently drop the token
        elif m is m_p:
            ids = [int(x) for x in re.findall(r"\d+", m.group(1))]
            any_pushed = False
            for pid in ids:
                if pid in known_passages:
                    segments.append({"type": "passage_ref", "passage_id": pid})
                    any_pushed = True
            if not any_pushed:
                _push_text(segments, m.group(0))
        else:  # raw URL
            url = m.group(0)
            cid = _new_click_id()
            clicks.append(PendingClick(cid, "external", None, url))
            segments.append(
                {
                    "type": "link",
                    "click_id": cid,
                    "label": url,
                    "kind": "external",
                    "ref": None,
                }
            )
        pos = m.end()

    return RenderOutput(segments=segments, answer_text=inp.answer_raw, clicks=clicks)
