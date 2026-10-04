"""Dollar cost of a response from its usage block.

Prices are USD per million tokens (Claude API list prices, Oct 2026). Cache
writes use the 5-minute TTL rate (1.25x input). If a refusal fallback served
the turn, message.model names the fallback model, so it is priced at its own rate.
"""

from __future__ import annotations

from typing import Any

from .llm import MODEL, cache_tokens

# model: (input, output, cache read)
PRICES: dict[str, tuple[float, float, float]] = {
    "claude-fable-5-1": (10.0, 50.0, 1.0),
    "claude-opus-5-5": (4.0, 20.0, 0.20),
    "claude-opus-5": (5.0, 25.0, 0.50),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20),
    "claude-haiku-4-5": (1.0, 5.0, 0.10),
}


def cost_usd(message: Any) -> float:
    model = getattr(message, "model", None) or MODEL
    inp, out, read_rate = PRICES.get(model, PRICES[MODEL])
    read, write = cache_tokens(message)
    u = message.usage
    return (
        (u.input_tokens or 0) * inp
        + write * inp * 1.25
        + read * read_rate
        + (u.output_tokens or 0) * out
    ) / 1_000_000
