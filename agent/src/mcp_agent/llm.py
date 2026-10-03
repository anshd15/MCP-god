"""Thin async wrapper over the Claude Messages API.

Agents depend on the LLM protocol, not the SDK, so tests can swap in a
scripted model that returns canned anthropic Message objects.
"""

from __future__ import annotations

from typing import Any, Protocol

import anthropic

MODEL = "claude-opus-5-5"


class LLM(Protocol):
    async def create(self, **kwargs: Any) -> Any: ...


class ClaudeLLM:
    def __init__(self, model: str = MODEL, max_retries: int = 4):
        # The SDK retries 408/409/429/5xx and connection errors with backoff.
        self.client = anthropic.AsyncAnthropic(max_retries=max_retries)
        self.model = model

    async def create(self, **kwargs: Any) -> Any:
        return await self.client.beta.messages.create(
            model=self.model,
            # On a safety decline, the API reruns the request on a fallback model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            **kwargs,
        )


def text_of(message: Any) -> str:
    return "\n".join(b.text for b in message.content if b.type == "text").strip()


def usage_tokens(message: Any) -> tuple[int, int]:
    u = message.usage
    cached = getattr(u, "cache_read_input_tokens", 0) or 0
    return (u.input_tokens or 0) + cached, u.output_tokens or 0
