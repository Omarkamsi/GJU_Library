from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Passage:
    source: str
    source_ref: str
    lang: str
    body: str
    title: Optional[str] = None
    subjects: list[str] = field(default_factory=list)

    def embedding_text(self) -> str:
        parts: list[str] = []
        if self.title:
            parts.append(f"Title: {self.title}")
        if self.subjects:
            parts.append("Subjects: " + ", ".join(self.subjects))
        parts.append(self.body)
        return " | ".join(parts) if (self.title or self.subjects) else self.body
