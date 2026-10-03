"""Exponential backoff with full jitter for transient tool failures.

Only TransientToolError is retried. A tool that returns is_error is a real
answer the model should see, not something to hammer again. Claude API
calls are retried by the anthropic SDK itself (max_retries).
"""

from __future__ import annotations

import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

import anyio

from .hub import TransientToolError

T = TypeVar("T")


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> T:
    for attempt in range(1, attempts + 1):
        try:
            return await fn()
        except TransientToolError as e:
            if attempt == attempts:
                raise
            if on_retry:
                on_retry(attempt, e)
            await anyio.sleep(random.uniform(0, min(max_delay, base_delay * 2 ** (attempt - 1))))
    raise AssertionError("unreachable")
