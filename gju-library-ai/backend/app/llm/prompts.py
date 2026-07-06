import urllib.parse
import urllib.request
import json as _json

from app.retrieval.interface import RetrievalResult

from .interface import ChatMessage

GJU_OPAC_BASE = "http://hip.jopuls.org.jo/web/gju"
OL_SEARCH = "https://openlibrary.org/search.json"
OL_BOOKS  = "https://openlibrary.org/api/books"
OL_BASE   = "https://openlibrary.org"


def _opac_url(title: str, isbn: str = "", author: str = "") -> str:
    """ISBN search is most precise; fall back to title+author."""
    if isbn:
        q = f"ISBN:{isbn}"
    else:
        q = f"{title} {author}".strip() if author else title
    return f"{GJU_OPAC_BASE}?q={urllib.parse.quote_plus(q)}"


def _ol_request(url: str, timeout: int = 5):
    req = urllib.request.Request(url, headers={"User-Agent": "GJULibraryAI/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return _json.loads(r.read())


def _fetch_book_info(title: str, author: str = "") -> dict | None:
    """
    Fetch rich book metadata from Open Library (free, no key).
    Step 1: search.json  → get ISBN + work key
    Step 2: api/books?jscmd=data → publisher, pages, cover, subjects
    Step 3: works/{key}.json → description (if available)
    Returns a dict of whatever was found; None if nothing.
    """
    try:
        # Strip MARC-style birth year suffix: "Fowler, Martin, 1963" → "Fowler, Martin"
        import re as _re
        clean_author = _re.sub(r",?\s*\d{4}[-–]?\d{0,4}\.?\s*$", "", author).strip(" ,.")

        # Step 1 — search for the book to get ISBN and work key
        q = f"{title} {clean_author}".strip() if clean_author else title
        params = urllib.parse.urlencode({
            "q": q, "limit": 1,
            "fields": "key,isbn,publisher,publish_year,number_of_pages_median,subject,first_sentence",
        })
        doc = _ol_request(f"{OL_SEARCH}?{params}").get("docs", [None])[0]
        if not doc:
            return None

        info: dict = {}

        # Pick best ISBN
        isbns = doc.get("isbn", [])
        isbn13 = next((i for i in isbns if len(i) == 13), None)
        isbn10 = next((i for i in isbns if len(i) == 10), None)
        isbn = isbn13 or isbn10
        if isbn:
            info["isbn"] = isbn

        if doc.get("publisher"):
            info["publisher"] = doc["publisher"][0]

        if doc.get("number_of_pages_median"):
            info["pageCount"] = doc["number_of_pages_median"]

        if doc.get("subject"):
            info["categories"] = ", ".join(doc["subject"][:4])

        # Step 2 — richer edition data via jscmd=data (needs ISBN)
        if isbn:
            try:
                bdata = _ol_request(
                    f"{OL_BOOKS}?bibkeys=ISBN:{isbn}&format=json&jscmd=data",
                    timeout=4,
                )
                ed = bdata.get(f"ISBN:{isbn}", {})
                if ed.get("publishers"):
                    info["publisher"] = ed["publishers"][0].get("name", info.get("publisher", ""))
                if ed.get("number_of_pages"):
                    info["pageCount"] = ed["number_of_pages"]
                if ed.get("cover"):
                    info["cover"] = ed["cover"].get("medium") or ed["cover"].get("large") or ""
            except Exception:
                pass

        # Step 3 — description from the work record
        fs = doc.get("first_sentence", "")
        if isinstance(fs, dict):
            fs = fs.get("value", "")
        if fs:
            info["description"] = str(fs)[:420]
        else:
            work_key = doc.get("key")
            if work_key:
                try:
                    work = _ol_request(f"{OL_BASE}{work_key}.json", timeout=4)
                    desc = work.get("description", "")
                    if isinstance(desc, dict):
                        desc = desc.get("value", "")
                    if desc:
                        info["description"] = str(desc)[:420].rstrip() + ("…" if len(str(desc)) > 420 else "")
                except Exception:
                    pass

        return info if info else None
    except Exception:
        return None


def build_book_card(passage: "PassageHit", info: dict | None, opac_link: str, lang: str) -> str:
    """
    Build a formatted book card string from a catalog passage and optional web info.
    The card is generated in Python so the LLM only needs to write a short comment.
    """
    import re as _re

    # Parse MARC-style fields from passage body
    raw_author = ""
    if "Author:" in passage.body:
        raw_author = passage.body.split("Author:")[1].split("Call Number:")[0].strip().rstrip(".")

    call_num = ""
    if "Call Number:" in passage.body:
        after = passage.body.split("Call Number:")[1]
        # Split on next MARC field tag, not on "." (call numbers contain dots)
        for tag in [" Year:", " Author:", " Available"]:
            if tag in after:
                after = after.split(tag)[0]
                break
        call_num = after.strip().rstrip(".")

    year = ""
    if "Year:" in passage.body:
        year = passage.body.split("Year:")[1].split(".")[0].strip()

    genre = ", ".join(passage.subjects) if passage.subjects else ""
    title = (passage.title or passage.source_ref).strip()
    pid = passage.id

    if lang == "ar":
        lines = [f"📖 **{title}** [P{pid}]"]
        if raw_author:
            lines.append(f"✍️ المؤلف: {raw_author}")
        if genre:
            lines.append(f"🏷️ التصنيف: {genre}")
        if call_num:
            lines.append(f"🔢 رقم التصنيف: {call_num}")
        if year:
            lines.append(f"📅 سنة النشر: {year}")
        if info:
            if info.get("publisher"):
                lines.append(f"🏢 الناشر: {info['publisher']}")
            if info.get("pageCount"):
                lines.append(f"📄 عدد الصفحات: {info['pageCount']}")
            if info.get("isbn"):
                lines.append(f"🔖 ISBN: {info['isbn']}")
            if info.get("description") and info["description"].strip():
                lines.append(f"📝 نبذة: {info['description'].strip()}")
        lines.append(f"🔍 {opac_link}")
    else:
        lines = [f"📖 **{title}** [P{pid}]"]
        if raw_author:
            lines.append(f"✍️ Author: {raw_author}")
        if genre:
            lines.append(f"🏷️ Genre: {genre}")
        if call_num:
            lines.append(f"🔢 Call Number: {call_num}")
        if year:
            lines.append(f"📅 Year: {year}")
        if info:
            if info.get("publisher"):
                lines.append(f"🏢 Publisher: {info['publisher']}")
            if info.get("pageCount"):
                lines.append(f"📄 Pages: {info['pageCount']}")
            if info.get("isbn"):
                lines.append(f"🔖 ISBN: {info['isbn']}")
            if info.get("description") and info["description"].strip():
                lines.append(f"📝 About: {info['description'].strip()}")
        lines.append(f"🔍 {opac_link}")

    return "\n".join(lines)


# PassageHit type is imported at runtime inside build_book_card; forward-declare for type checkers.
try:
    from app.retrieval.interface import PassageHit as _PassageHit  # noqa: F401
except ImportError:
    pass


SYSTEM = {
    "en": (
        "You are the official GJU Library AI assistant — professional, supportive, "
        "and aligned with the library's mission as a vibrant center for knowledge "
        "and innovation. Answer the user's question using ONLY the PASSAGES "
        "provided.\n"
        "CITATION RULES (strict):\n"
        " - Cite each supporting passage as a separate token, e.g. [P12] [P34].\n"
        " - NEVER combine ids: do NOT write [P12, P34] or [P12,P34] — write [P12] [P34].\n"
        " - If DATABASES are listed in your context, you MUST include every one in "
        "your answer using its [DB:<slug>] token. Write the token only — do NOT "
        "repeat the database name or subjects after it. NEVER write a raw URL.\n"
        " - If the PASSAGES do not contain the answer, reply briefly that the "
        "information is not available and suggest contacting the library. Do NOT "
        "invent facts.\n"
        "ROUTING RULES:\n"
        " - For Turnitin or digital-account questions, route the user to the "
        "Digital Library Division Head as described in the relevant passage.\n"
        " - For borrowing questions, distinguish undergraduate, graduate, and "
        "faculty borrowing limits using the appropriate passages.\n"
        " - When a passage is from the physical catalog (source=catalog): the full "
        "book card is already shown to the user by the system. Write 1-2 natural "
        "sentences introducing the book or answering the user's question about it "
        "(topic, significance, who it is recommended for). Cite with [Pxx]. "
        "Do NOT reproduce the card fields (title, author, call number, etc.).\n"
        " - If multiple catalog books match, write a brief sentence for each.\n"
        " - For follow-up questions (what is it about, who wrote it, etc.), answer "
        "conversationally using passage details and WEB_INFO — do not repeat the card.\n"
        " - If the user asks about a book NOT in the passages, say it is not currently "
        "in the GJU catalog and suggest searching at http://hip.jopuls.org.jo/web/gju\n"
        "LANGUAGE: respond ONLY in English. Do not include words from any other "
        "language or script. Keep responses concise (under ~120 words)."
    ),
    "ar": (
        "أنت المساعد الذكي الرسمي لمكتبة الجامعة الألمانية الأردنية — بأسلوب مهني "
        "وداعم، يعكس رسالة المكتبة بوصفها مركزاً نابضاً بالمعرفة والابتكار. أجب عن "
        "سؤال المستخدم باستخدام المقاطع (PASSAGES) المُقدَّمة فقط.\n"
        "قواعد الاستشهاد (إلزامية):\n"
        " - اذكر كل مقطع بصيغة منفصلة، مثلاً: [P12] [P34].\n"
        " - لا تكتب أبداً [P12, P34] أو [P12،P34]. اكتب كل رقم في وسم مستقل.\n"
        " - إذا وردت قواعد بيانات في سياقك، يجب أن تُدرج كلَّ واحدة في إجابتك "
        "باستخدام وسمها [DB:<slug>] فقط، دون تكرار الاسم أو المواضيع بعده. "
        "لا تكتب الروابط مباشرة.\n"
        " - إذا لم تتضمن المقاطع الإجابة، اذكر ذلك بإيجاز واقترح التواصل مع المكتبة "
        "ولا تختلق معلومات.\n"
        "قواعد التوجيه:\n"
        " - للاستفسارات حول تيرنيتن (Turnitin) أو الحسابات الرقمية، أَحِل المستخدم "
        "إلى رئيس قسم المكتبة الرقمية وفق المقطع المخصّص.\n"
        " - في أسئلة الإعارة، فرّق بين البكالوريوس والدراسات العليا وأعضاء هيئة "
        "التدريس باستخدام المقاطع المناسبة.\n"
        " - عند الإجابة عن كتاب من المجموعة الفعلية للمكتبة (المصدر: catalog): "
        "بطاقة الكتاب الكاملة تُعرض للمستخدم تلقائياً من النظام. اكتب جملة أو جملتين "
        "بأسلوب محادثة تُعرِّف بالكتاب أو تجيب عن سؤال المستخدم (موضوعه، أهميته، "
        "لمن يُنصح به). استشهد بـ [Pxx]. لا تُعيد كتابة حقول البطاقة (العنوان، "
        "المؤلف، رقم التصنيف وغيرها).\n"
        " - إذا تطابق أكثر من كتاب، اكتب جملة مختصرة عن كل منهما.\n"
        " - لأسئلة المتابعة (ما محتواه، من كتبه...)، أجب بأسلوب محادثة مستخدماً "
        "تفاصيل المقطع وWEB_INFO.\n"
        " - إذا سأل المستخدم عن كتاب غير موجود في المقاطع، أخبره بأنه غير متوفر حالياً "
        "واقترح البحث مباشرةً على http://hip.jopuls.org.jo/web/gju\n"
        "اللغة: أجب باللغة العربية فقط. لا تستخدم الإنجليزية أو أي لغة أخرى. "
        "أجب باختصار (أقل من 100 كلمة)."
    ),
    "de": (
        "Du bist die offizielle KI-Assistenz der GJU-Bibliothek — professionell, "
        "unterstützend, im Einklang mit dem Auftrag der Bibliothek als lebendiges "
        "Zentrum für Wissen und Innovation. Beantworte die Nutzerfrage "
        "AUSSCHLIESSLICH anhand der bereitgestellten PASSAGES.\n"
        "ZITIERREGELN (verbindlich):\n"
        " - Zitiere jede unterstützende Passage als separates Token, z. B. [P12] [P34].\n"
        " - Schreibe NIEMALS [P12, P34]; jede ID kommt in ein eigenes Token.\n"
        " - Wenn DATABASES in deinem Kontext aufgeführt sind, MUSST du jede davon "
        "in deiner Antwort mit ihrem [DB:<slug>]-Token nennen. Schreibe nur das "
        "Token — wiederhole NICHT den Datenbanknamen oder die Fachgebiete danach. "
        "NIEMALS eine Roh-URL.\n"
        " - Wenn die PASSAGES die Antwort nicht enthalten, sage das knapp und "
        "empfiehl, die Bibliothek zu kontaktieren. Erfinde keine Fakten.\n"
        "ROUTING-REGELN:\n"
        " - Für Fragen zu Turnitin oder digitalen Konten verweise auf die Leitung "
        "der Digital Library Division.\n"
        " - Bei Ausleihfragen unterscheide zwischen Bachelor-, Master- und "
        "Lehrenden-Ausleihregeln mithilfe der jeweiligen Passagen.\n"
        " - Bei einem Katalogeintrag (source=catalog): Die vollständige Buchkarte "
        "wird dem Nutzer automatisch vom System angezeigt. Schreibe 1-2 natürliche "
        "Sätze, die das Buch vorstellen oder die Frage des Nutzers beantworten "
        "(Thema, Bedeutung, Zielgruppe). Zitiere mit [Pxx]. Wiederhole NICHT die "
        "Kartenfelder (Titel, Autor, Signatur usw.).\n"
        " - Bei mehreren passenden Büchern einen kurzen Satz pro Buch.\n"
        "SPRACHE: Antworte AUSSCHLIESSLICH auf Deutsch. Antworten kurz halten (unter ~100 Wörter)."
    ),
}


def build_messages(
    query: str,
    result: RetrievalResult,
    lang: str,
    history: list[tuple[str, str]] | None = None,
) -> list[ChatMessage]:
    sys_text = SYSTEM.get(lang, SYSTEM["en"])
    messages: list[ChatMessage] = [ChatMessage("system", sys_text)]

    if history:
        for role, content in history[-6:]:
            messages.append(ChatMessage(role, content))

    import re as _re

    parts: list[str] = ["PASSAGES:"]
    BODY_CAP = 300
    seen_titles: set[str] = set()
    for p in result.passages:
        head = (p.title or p.source_ref).strip()
        body = p.body if len(p.body) <= BODY_CAP else p.body[:BODY_CAP].rstrip() + "…"
        genre = f"Genre/Subject: {', '.join(p.subjects)}.\n" if p.subjects else ""

        extra = ""
        if p.source == "catalog" and p.title and p.title not in seen_titles:
            seen_titles.add(p.title)

            raw_author = ""
            if "Author:" in p.body:
                raw_author = p.body.split("Author:")[1].split("Call Number:")[0].strip().rstrip(".")
            clean_author = _re.sub(r",?\s*\d{4}[-–]?\d{0,4}\.?\s*$", "", raw_author).strip(" ,.")

            info = _fetch_book_info(p.title, clean_author)
            isbn = info.get("isbn", "") if info else ""
            opac_link = _opac_url(p.title, isbn=isbn, author=clean_author)

            # Provide the OPAC link so the LLM can reference it if asked
            extra += f"\n🔍 {opac_link}"
            # Provide a brief description for conversational follow-ups
            if info and info.get("description"):
                desc = info["description"][:200]
                extra += f"\nWEB_INFO: {desc}"

        parts.append(f"[P{p.id}] ({p.lang}) {head}\n{genre}{body}{extra}")

    if result.databases:
        tokens = " ".join(f"[DB:{d.slug}]" for d in result.databases)
        parts.append(
            f"\nDATABASES (include ALL of these tokens verbatim in your answer):\n{tokens}"
        )
    parts.append(f"\nQUESTION:\n{query}")
    messages.append(ChatMessage("user", "\n\n".join(parts)))
    return messages
