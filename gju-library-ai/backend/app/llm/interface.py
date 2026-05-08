from dataclasses import dataclass
from typing import Protocol


@dataclass
class ChatMessage:
    role: str  # system | user | assistant
    content: str


@dataclass
class ChatResponse:
    text: str
    model: str
    latency_ms: int


class LLMClient(Protocol):
    def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> ChatResponse: ...
