import time
from typing import Iterator

from google import genai
from google.genai import types

from .interface import ChatMessage, ChatResponse, LLMClient


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def _build_contents(
        self, messages: list[ChatMessage]
    ) -> tuple[list[types.Content], str | None]:
        system_parts = [m.content for m in messages if m.role == "system"]
        system_instruction = "\n\n".join(system_parts) if system_parts else None
        contents = [
            types.Content(
                role="user" if m.role == "user" else "model",
                parts=[types.Part.from_text(text=m.content)],
            )
            for m in messages
            if m.role != "system"
        ]
        return contents, system_instruction

    def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> ChatResponse:
        contents, system_instruction = self._build_contents(messages)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        start = time.perf_counter()
        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )
        elapsed = int((time.perf_counter() - start) * 1000)
        return ChatResponse(text=response.text or "", model=self._model, latency_ms=elapsed)

    def stream(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> Iterator[str]:
        contents, system_instruction = self._build_contents(messages)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        for chunk in self._client.models.generate_content_stream(
            model=self._model,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text
