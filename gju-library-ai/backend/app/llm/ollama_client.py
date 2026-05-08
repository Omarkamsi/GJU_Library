import time

from ollama import Client

from .interface import ChatMessage, ChatResponse, LLMClient


class OllamaClient(LLMClient):
    def __init__(self, host: str, model: str):
        self._client = Client(host=host)
        self._model = model

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
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        return ChatResponse(
            text=resp["message"]["content"],
            model=self._model,
            latency_ms=elapsed,
        )
