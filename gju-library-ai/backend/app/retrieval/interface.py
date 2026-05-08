from dataclasses import dataclass, field
from typing import Optional, Protocol


@dataclass
class PassageHit:
    id: int
    source: str
    source_ref: str
    lang: str
    title: Optional[str]
    body: str
    subjects: list[str]
    score: float


@dataclass
class DatabaseHit:
    slug: str
    name: str
    url: str
    subjects: list[str]
    description: str
    score: float


@dataclass
class RetrievalResult:
    passages: list[PassageHit]
    databases: list[DatabaseHit]
    debug: dict = field(default_factory=dict)


class Retriever(Protocol):
    def search(self, query: str, lang: str, k: int = 5) -> RetrievalResult: ...
