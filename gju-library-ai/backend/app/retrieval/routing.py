import re
from dataclasses import dataclass

SUBJECT_KEYWORDS: dict[str, list[str]] = {
    "Engineering": [
        "engineering", "هندسة", "robotics", "circuit",
        "ingenieur", "maschinenbau", "elektro",
    ],
    "Computer Science": [
        "computer", "software", "ai", "ml", "informatik",
        "حاسوب", "برمجة", "ذكاء اصطناعي",
    ],
    "Business": [
        "business", "management", "marketing", "finance",
        "wirtschaft", "إدارة", "تسويق", "أعمال",
    ],
    "Law": ["law", "legal", "قانون", "تشريع", "recht"],
    "Medicine": ["medicine", "health", "طب", "medizin"],
    "German Studies": ["german", "deutsch", "ألمانية"],
    "Statistics": ["statistics", "statista", "إحصاء", "statistik"],
}


@dataclass
class Route:
    lang: str
    subjects: list[str]


class RuleBasedRouter:
    def route(self, q: str) -> Route:
        return Route(lang=self._lang(q), subjects=self._subjects(q))

    def _lang(self, q: str) -> str:
        if any("؀" <= c <= "ۿ" for c in q):
            return "ar"
        ql = q.lower()
        if (
            re.search(r"\b(der|die|das|und|wo|wie|ist|für|mit|nicht)\b", ql)
            or any(c in q for c in "äöüß")
        ):
            return "de"
        return "en"

    def _subjects(self, q: str) -> list[str]:
        ql = q.lower()
        return [
            subj
            for subj, kws in SUBJECT_KEYWORDS.items()
            if any(k in ql for k in kws)
        ]
