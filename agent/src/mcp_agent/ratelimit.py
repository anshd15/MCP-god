"""Per-tool token-bucket rate limits, configured as {"glob": calls_per_minute}."""

from __future__ import annotations

import fnmatch
import time
from dataclasses import dataclass, field


@dataclass
class _Bucket:
    rate: float
    tokens: float
    last: float = field(default_factory=time.monotonic)


class RateLimiter:
    def __init__(self, limits: dict[str, float]):
        self.limits = limits
        self._buckets: dict[str, _Bucket] = {}

    def allow(self, tool: str) -> bool:
        per_min = next((v for p, v in self.limits.items() if fnmatch.fnmatchcase(tool, p)), None)
        if per_min is None:
            return True
        b = self._buckets.setdefault(tool, _Bucket(per_min / 60, per_min))
        now = time.monotonic()
        b.tokens = min(per_min, b.tokens + (now - b.last) * b.rate)
        b.last = now
        if b.tokens < 1:
            return False
        b.tokens -= 1
        return True
