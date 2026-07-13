import json
import time
from typing import Iterator

from groq import Groq

from .interface import ChatMessage, ChatResponse, LLMClient


def _to_groq_messages(messages: list[ChatMessage]) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in messages]


class GroqClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        self._groq = Groq(api_key=api_key)
        self._model = model

    def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> ChatResponse:
        start = time.perf_counter()
        resp = self._groq.chat.completions.create(
            model=self._model,
            messages=_to_groq_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        return ChatResponse(
            text=resp.choices[0].message.content or "",
            model=self._model,
            latency_ms=elapsed,
        )

    def stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> Iterator[str]:
        stream = self._groq.chat.completions.create(
            model=self._model,
            messages=_to_groq_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 600,
    ):
        """Return a raw Groq completion response (used by the ReAct agent)."""
        kwargs = dict(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return self._groq.chat.completions.create(**kwargs)
