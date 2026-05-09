import time
from typing import Iterator

from ollama import Client

from .interface import ChatMessage, ChatResponse, LLMClient


class OllamaClient(LLMClient):
    def __init__(self, host: str, model: str, keep_alive: str = "30m"):
        self._client = Client(host=host)
        self._model = model
        self._keep_alive = keep_alive

    def warmup(self) -> None:
        try:
            self._client.chat(
                model=self._model,
                messages=[{"role": "user", "content": "ok"}],
                options={"num_predict": 1},
                keep_alive=self._keep_alive,
            )
        except Exception:
            pass

    def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> ChatResponse:
        start = time.perf_counter()
        resp = self._client.chat(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            options={"temperature": temperature, "num_predict": max_tokens},
            keep_alive=self._keep_alive,
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        return ChatResponse(
            text=resp["message"]["content"],
            model=self._model,
            latency_ms=elapsed,
        )

    def stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> Iterator[str]:
        for chunk in self._client.chat(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            options={"temperature": temperature, "num_predict": max_tokens},
            keep_alive=self._keep_alive,
            stream=True,
        ):
            piece = chunk.get("message", {}).get("content", "")
            if piece:
                yield piece
