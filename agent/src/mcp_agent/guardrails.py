"""Guardrails between the model and the tools.

Policy: every tool call resolves to allow / ask / deny. Explicit config
patterns win (deny > ask > allow); otherwise read-only tools are allowed and
anything that may mutate state needs approval.

Arguments are validated against the tool's JSON schema before the call, and
budgets cap how much a single run can do.
"""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import jsonschema

from .hub import HubTool


class Decision(str, Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


class BudgetExceeded(Exception):
    pass


Approver = Callable[[HubTool, dict[str, Any]], Awaitable[bool]]


async def deny_all(tool: HubTool, args: dict[str, Any]) -> bool:
    return False


@dataclass
class Policy:
    deny: list[str] = field(default_factory=list)
    ask: list[str] = field(default_factory=list)
    allow: list[str] = field(default_factory=list)

    @classmethod
    def from_config(cls, cfg: dict[str, list[str]]) -> Policy:
        return cls(cfg.get("deny", []), cfg.get("ask", []), cfg.get("allow", []))

    def decide(self, tool: HubTool) -> Decision:
        def hit(patterns: list[str]) -> bool:
            return any(fnmatch.fnmatchcase(tool.name, p) for p in patterns)

        if hit(self.deny):
            return Decision.DENY
        if hit(self.ask):
            return Decision.ASK
        if hit(self.allow) or tool.read_only:
            return Decision.ALLOW
        return Decision.ASK


def validate_args(tool: HubTool, args: dict[str, Any]) -> str | None:
    """Return an error message if args don't match the tool's schema."""
    try:
        jsonschema.validate(args, tool.input_schema)
    except jsonschema.ValidationError as e:
        return f"invalid arguments for {tool.name}: {e.message}"
    return None


@dataclass
class Budget:
    max_steps: int = 8
    max_tool_calls: int = 30
    max_tokens: int = 400_000
    steps: int = 0
    tool_calls: int = 0
    tokens: int = 0

    def charge_step(self) -> None:
        self.steps += 1
        if self.steps > self.max_steps:
            raise BudgetExceeded(f"step budget {self.max_steps} exceeded")

    def charge_tool(self) -> None:
        self.tool_calls += 1
        if self.tool_calls > self.max_tool_calls:
            raise BudgetExceeded(f"tool-call budget {self.max_tool_calls} exceeded")

    def charge_tokens(self, n: int) -> None:
        self.tokens += n
        if self.tokens > self.max_tokens:
            raise BudgetExceeded(f"token budget {self.max_tokens} exceeded")
