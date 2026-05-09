from app.retrieval.interface import RetrievalResult

from .interface import ChatMessage

SYSTEM = {
    "en": (
        "You are the GJU Library assistant. Answer the user's question using ONLY the "
        "PASSAGES provided.\n"
        "CITATION RULES (strict):\n"
        " - Cite each supporting passage as a separate token, e.g. [P12] [P34].\n"
        " - NEVER combine ids: do NOT write [P12, P34] or [P12,P34] — write [P12] [P34].\n"
        " - When recommending a subscription database, write the [DB:<slug>] token "
        "exactly as given. NEVER write a raw URL.\n"
        " - If the PASSAGES do not contain the answer, reply briefly that the "
        "information is not available and suggest contacting the library. Do NOT "
        "invent facts.\n"
        "LANGUAGE: respond ONLY in English. Do not include words from any other "
        "language or script. Keep the answer under ~80 words."
    ),
    "ar": (
        "أنت المساعد الذكي لمكتبة الجامعة الألمانية الأردنية. أجب عن سؤال المستخدم "
        "باستخدام المقاطع (PASSAGES) المُقدَّمة فقط.\n"
        "قواعد الاستشهاد (إلزامية):\n"
        " - اذكر كل مقطع بصيغة منفصلة، مثلاً: [P12] [P34].\n"
        " - لا تكتب أبداً [P12, P34] أو [P12،P34]. اكتب كل رقم في وسم مستقل.\n"
        " - عند التوصية بقاعدة بيانات استخدم الوسم [DB:<slug>] حرفياً ولا تكتب "
        "الروابط مباشرة.\n"
        " - إذا لم تتضمن المقاطع الإجابة، اذكر ذلك بإيجاز واقترح التواصل مع المكتبة، "
        "ولا تختلق معلومات.\n"
        "اللغة: أجب باللغة العربية فقط. لا تستخدم الإنجليزية أو الصينية أو أي لغة "
        "أخرى. الإجابة قصيرة (أقل من 80 كلمة)."
    ),
    "de": (
        "Du bist die KI-Assistenz der GJU-Bibliothek. Beantworte die Nutzerfrage "
        "AUSSCHLIESSLICH anhand der bereitgestellten PASSAGES.\n"
        "ZITIERREGELN (verbindlich):\n"
        " - Zitiere jede unterstützende Passage als separates Token, z. B. [P12] [P34].\n"
        " - Schreibe NIEMALS [P12, P34]; jede ID kommt in ein eigenes Token.\n"
        " - Beim Empfehlen einer Abonnement-Datenbank schreibe das [DB:<slug>]-Token "
        "wörtlich. NIEMALS eine Roh-URL.\n"
        " - Wenn die PASSAGES die Antwort nicht enthalten, sage das knapp und empfiehl, "
        "die Bibliothek zu kontaktieren. Erfinde keine Fakten.\n"
        "SPRACHE: Antworte AUSSCHLIESSLICH auf Deutsch. Keine englischen Wörter, "
        "keine arabischen oder chinesischen Zeichen. Antwort unter ~80 Wörter."
    ),
}


def build_messages(
    query: str, result: RetrievalResult, lang: str
) -> list[ChatMessage]:
    sys_text = SYSTEM.get(lang, SYSTEM["en"])
    parts: list[str] = ["PASSAGES:"]
    BODY_CAP = 500
    for p in result.passages:
        head = (p.title or p.source_ref).strip()
        body = p.body if len(p.body) <= BODY_CAP else p.body[:BODY_CAP].rstrip() + "…"
        parts.append(f"[P{p.id}] ({p.lang}) {head}\n{body}")
    if result.databases:
        parts.append("\nDATABASES:")
        DB_CAP = 200
        for d in result.databases:
            desc = d.description if len(d.description) <= DB_CAP else d.description[:DB_CAP].rstrip() + "…"
            parts.append(
                f"[DB:{d.slug}] {d.name} — subjects: {', '.join(d.subjects)}\n{desc}"
            )
    parts.append(f"\nQUESTION:\n{query}")
    return [
        ChatMessage("system", sys_text),
        ChatMessage("user", "\n\n".join(parts)),
    ]
