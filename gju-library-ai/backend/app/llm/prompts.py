from app.retrieval.interface import RetrievalResult

from .interface import ChatMessage

SYSTEM = {
    "en": (
        "You are the GJU Library assistant. Answer the user's question using ONLY the "
        "PASSAGES provided. If a passage supports a fact, cite it inline as [P<id>]. "
        "If you recommend a subscription database, mention it using [DB:<slug>] tokens "
        "(NEVER write a raw URL — the system replaces tokens with tracked links). If "
        "the passages do not contain the answer, say so briefly and suggest contacting "
        "the library. Answer in English."
    ),
    "ar": (
        "أنت المساعد الذكي لمكتبة الجامعة الألمانية الأردنية. أجب عن سؤال المستخدم "
        "باستخدام المقاطع (PASSAGES) المُقدَّمة فقط. اذكر استشهادك بصيغة [P<id>] داخل "
        "النص. عند التوصية بقاعدة بيانات استخدم [DB:<slug>] ولا تكتب الروابط مباشرة "
        "(يستبدلها النظام بروابط متتبَّعة). إذا لم تتضمن المقاطع الإجابة، اذكر ذلك "
        "بإيجاز واقترح التواصل مع المكتبة. أجب باللغة العربية."
    ),
    "de": (
        "Du bist die KI-Assistenz der GJU-Bibliothek. Beantworte die Nutzerfrage "
        "AUSSCHLIESSLICH anhand der bereitgestellten PASSAGES. Belege jede Aussage "
        "inline mit [P<id>]. Wenn du eine Abonnement-Datenbank empfiehlst, verwende "
        "ausschließlich [DB:<slug>] – schreibe NIEMALS Roh-URLs (das System ersetzt "
        "die Tokens durch nachverfolgte Links). Wenn die Passages die Frage nicht "
        "beantworten, sage das knapp und empfiehl, die Bibliothek zu kontaktieren. "
        "Antworte auf Deutsch."
    ),
}


def build_messages(
    query: str, result: RetrievalResult, lang: str
) -> list[ChatMessage]:
    sys_text = SYSTEM.get(lang, SYSTEM["en"])
    parts: list[str] = ["PASSAGES:"]
    for p in result.passages:
        head = (p.title or p.source_ref).strip()
        parts.append(f"[P{p.id}] ({p.lang}) {head}\n{p.body}")
    if result.databases:
        parts.append("\nDATABASES:")
        for d in result.databases:
            parts.append(
                f"[DB:{d.slug}] {d.name} — subjects: {', '.join(d.subjects)}\n"
                f"{d.description}"
            )
    parts.append(f"\nQUESTION:\n{query}")
    return [
        ChatMessage("system", sys_text),
        ChatMessage("user", "\n\n".join(parts)),
    ]
