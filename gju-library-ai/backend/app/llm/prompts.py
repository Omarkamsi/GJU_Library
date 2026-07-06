import urllib.parse
import urllib.request
import json as _json

from app.retrieval.interface import RetrievalResult

from .interface import ChatMessage

GJU_OPAC_BASE = "http://hip.jopuls.org.jo/web/gju"
OPEN_LIBRARY_API = "https://openlibrary.org/search.json"


def _opac_url(title: str) -> str:
    """Build a direct search URL for a specific book title in the GJU OPAC."""
    return f"{GJU_OPAC_BASE}?q={urllib.parse.quote_plus(title)}"


def _fetch_open_library(title: str, author: str = "") -> str | None:
    """Fetch a short book description from Open Library (no API key needed)."""
    try:
        params = urllib.parse.urlencode({"title": title, "author": author, "limit": 1, "fields": "title,author_name,first_sentence,subject"})
        req = urllib.request.Request(
            f"{OPEN_LIBRARY_API}?{params}",
            headers={"User-Agent": "GJULibraryAI/1.0"}
        )
        with urllib.request.urlopen(req, timeout=4) as r:
            data = _json.loads(r.read())
        docs = data.get("docs", [])
        if not docs:
            return None
        doc = docs[0]
        parts = []
        if doc.get("first_sentence"):
            fs = doc["first_sentence"]
            if isinstance(fs, dict):
                fs = fs.get("value", "")
            if fs:
                parts.append(f"Summary: {str(fs)[:300]}")
        if doc.get("subject"):
            parts.append(f"Topics: {', '.join(doc['subject'][:5])}")
        return " | ".join(parts) if parts else None
    except Exception:
        return None

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
        " - For a SPECIFIC book's availability, location, or call number, direct "
        "the user to the GJU Library Catalog (OPAC) using the passage that "
        "describes it — do not guess.\n"
        " - For Turnitin or digital-account questions, route the user to the "
        "Digital Library Division Head as described in the relevant passage.\n"
        " - For borrowing questions, distinguish undergraduate, graduate, and "
        "faculty borrowing limits using the appropriate passages.\n"
        " - When a passage is from the physical catalog (source=catalog), confirm "
        "availability and present ALL book details using EXACTLY this format "
        "(substitute real values from the passage — never copy placeholder text):\n"
        "  Yes, GJU Library holds this book in its physical collection [Pxx].\n"
        "  📖 Title: TITLE_FROM_PASSAGE\n"
        "  ✍️ Author: AUTHOR_FROM_PASSAGE\n"
        "  🏷️ Genre / Subject: SUBJECT_FROM_PASSAGE\n"
        "  🔢 Call Number: CALL_NUMBER_FROM_PASSAGE\n"
        "  📅 Publication Year: YEAR_FROM_PASSAGE\n"
        "  📝 About: SUMMARY_FROM_WEB_INFO_OR_PASSAGE\n"
        "  🔍 Direct catalog link: OPAC_URL_VALUE_FROM_PASSAGE\n"
        " - The OPAC_URL value appears in the passage as 'OPAC_URL: <url>'. Copy that "
        "URL verbatim as the direct catalog link. Never write the label 'OPAC_URL' or "
        "any instruction text in your answer — only the actual URL.\n"
        " - If multiple catalog books match or the user asks for a list of books, "
        "list up to 5 books, each using the same format.\n"
        " - For follow-up questions about a book (what is it about, who wrote it, etc.), "
        "answer conversationally using the passage details and any WEB_INFO provided — "
        "do not repeat the full book card format for follow-ups.\n"
        " - If the user asks about a book NOT in the passages, say it is not currently "
        "in the GJU catalog and suggest they search at http://hip.jopuls.org.jo/web/gju\n"
        "LANGUAGE: respond ONLY in English. Do not include words from any other "
        "language or script. For book catalog answers give full details; for other "
        "answers keep responses concise (under ~150 words)."
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
        " - للاستفسار عن توفر كتاب معيّن أو موقعه أو رقم تصنيفه، وجِّه المستخدم إلى "
        "فهرس المكتبة (OPAC) من خلال المقطع المخصّص لذلك.\n"
        " - للاستفسارات حول تيرنيتن (Turnitin) أو الحسابات الرقمية، أَحِل المستخدم "
        "إلى رئيس قسم المكتبة الرقمية وفق المقطع المخصّص.\n"
        " - في أسئلة الإعارة، فرّق بين البكالوريوس والدراسات العليا وأعضاء هيئة "
        "التدريس باستخدام المقاطع المناسبة.\n"
        " - عند الإجابة عن كتاب من المجموعة الفعلية للمكتبة (المصدر: catalog)، اذكر "
        "تفاصيل الكتاب كاملةً في أسطر منفصلة: العنوان، المؤلف، التصنيف الموضوعي، "
        "رقم التصنيف، وسنة النشر. ثم أَحِل المستخدم للتحقق من التوفر والموقع عبر "
        "الرابط OPAC_URL المُدرج في المقطع — استخدم الرابط المُقدَّم مباشرةً ولا تستخدم الصفحة الرئيسية.\n"
        " - إذا سأل المستخدم عن حداثة المعلومات، يمكنك الإشارة إلى أن النظام قادر "
        "على تحديث البيانات من موقع المكتبة الرسمي عند الطلب.\n"
        "اللغة: أجب باللغة العربية فقط. لا تستخدم الإنجليزية أو الصينية أو أي لغة "
        "أخرى. لأسئلة الكتب أعطِ التفاصيل كاملة؛ لغيرها أجب باختصار (أقل من 100 كلمة)."
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
        " - Für die Verfügbarkeit oder Signatur eines bestimmten Buches verweise "
        "auf den GJU-Bibliothekskatalog (OPAC) gemäß der entsprechenden Passage.\n"
        " - Für Fragen zu Turnitin oder digitalen Konten verweise auf die Leitung "
        "der Digital Library Division.\n"
        " - Bei Ausleihfragen unterscheide zwischen Bachelor-, Master- und "
        "Lehrenden-Ausleihregeln mithilfe der jeweiligen Passagen.\n"
        f" - Bei einem Katalogeintrag aus dem physischen Bestand (source=catalog) "
        "gib alle Buchdetails in separaten Zeilen aus: Titel, Autor, Genre/Fachgebiet, "
        "Signatur und Erscheinungsjahr. Verweise dann auf den GJU-Bibliothekskatalog "
        "zur Verfügbarkeits- und Standortprüfung den OPAC_URL-Link aus dem Abschnitt — nutze den direkten Link, nicht die Startseite.\n"
        " - Bei Fragen zur Aktualität kannst du erwähnen, dass das System bei "
        "Bedarf eine Aktualisierung von der offiziellen GJU-Bibliothekswebsite "
        "auslösen kann.\n"
        "SPRACHE: Antworte AUSSCHLIESSLICH auf Deutsch. Keine englischen Wörter, "
        "keine arabischen oder chinesischen Zeichen. Bei Buchanfragen vollständige "
        "Details; sonst knapp (unter ~100 Wörter)."
    ),
}


def build_messages(
    query: str,
    result: RetrievalResult,
    lang: str,
    history: list[tuple[str, str]] | None = None,
) -> list[ChatMessage]:
    """Build the message list for the LLM.

    history: list of (role, content) pairs from previous turns, oldest first.
             Capped at the last 6 messages (3 user+assistant pairs) to control context size.
    """
    sys_text = SYSTEM.get(lang, SYSTEM["en"])
    messages: list[ChatMessage] = [ChatMessage("system", sys_text)]

    # Inject up to 3 prior turns so the LLM has conversational context
    if history:
        for role, content in history[-6:]:
            messages.append(ChatMessage(role, content))

    parts: list[str] = ["PASSAGES:"]
    BODY_CAP = 300
    seen_titles: set[str] = set()
    for p in result.passages:
        head = (p.title or p.source_ref).strip()
        body = p.body if len(p.body) <= BODY_CAP else p.body[:BODY_CAP].rstrip() + "…"
        genre = f"Genre/Subject: {', '.join(p.subjects)}.\n" if p.subjects else ""

        # For catalog passages, embed a direct OPAC search URL and Open Library info
        extra = ""
        if p.source == "catalog" and p.title and p.title not in seen_titles:
            seen_titles.add(p.title)
            opac_link = _opac_url(p.title)
            extra += f"\nOPAC_URL: {opac_link}"
            # Extract author from body for Open Library lookup
            author = ""
            if "Author:" in p.body:
                author = p.body.split("Author:")[1].split(".")[0].strip()
            web_info = _fetch_open_library(p.title, author)
            if web_info:
                extra += f"\nWEB_INFO: {web_info}"

        parts.append(f"[P{p.id}] ({p.lang}) {head}\n{genre}{body}{extra}")
    if result.databases:
        tokens = " ".join(f"[DB:{d.slug}]" for d in result.databases)
        parts.append(
            f"\nDATABASES (include ALL of these tokens verbatim in your answer):\n{tokens}"
        )
    parts.append(f"\nQUESTION:\n{query}")
    messages.append(ChatMessage("user", "\n\n".join(parts)))
    return messages
