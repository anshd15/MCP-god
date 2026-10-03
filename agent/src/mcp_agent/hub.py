"""MCP hub: one client session per server, all tools in one namespace.

Tool names are exposed to the model as `<server>__<tool>` so two servers can
ship a tool with the same name without colliding, and so guardrail patterns
can target a whole server (`fs__*`).
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anyio
from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.types import ToolAnnotations

SEP = "__"


class TransientToolError(Exception):
    """Transport-level failure (timeout, dead server). Safe to retry."""


@dataclass(frozen=True)
class ServerSpec:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] | None = None
    cwd: str | None = None


@dataclass(frozen=True)
class HubTool:
    name: str
    server: str
    remote_name: str
    description: str
    input_schema: dict[str, Any]
    annotations: ToolAnnotations | None

    @property
    def read_only(self) -> bool:
        return bool(self.annotations and self.annotations.read_only_hint)

    @property
    def destructive(self) -> bool:
        # The MCP spec defaults destructiveHint to true for non-read-only tools.
        if self.read_only:
            return False
        if self.annotations is None or self.annotations.destructive_hint is None:
            return True
        return self.annotations.destructive_hint

    def to_anthropic(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}


@dataclass(frozen=True)
class ToolOutcome:
    text: str
    is_error: bool = False


def load_config(path: str | Path) -> tuple[list[ServerSpec], dict[str, list[str]]]:
    """Read servers.json. Returns server specs and the raw policy block."""
    path = Path(path)
    cfg = json.loads(path.read_text("utf-8"))
    base = path.parent.resolve()
    specs = []
    for name, s in cfg["servers"].items():
        if SEP in name:
            raise ValueError(f"server name {name!r} must not contain {SEP!r}")
        # "python" means the interpreter running the agent, so servers share its venv.
        command = sys.executable if s["command"] == "python" else s["command"]
        specs.append(ServerSpec(name, command, s.get("args", []), s.get("env"), s.get("cwd", str(base))))
    return specs, cfg.get("policy", {})


def _render(result: Any) -> str:
    parts: list[str] = []
    for item in result.content or []:
        kind = getattr(item, "type", None)
        if kind == "text":
            parts.append(item.text)
        elif kind == "resource" and hasattr(item.resource, "text"):
            parts.append(item.resource.text)
        else:
            parts.append(f"[{kind} content omitted]")
    if not parts and result.structured_content is not None:
        parts.append(json.dumps(result.structured_content, sort_keys=True))
    return "\n".join(parts)


class MCPHub:
    def __init__(self, specs: list[ServerSpec], call_timeout: float = 30.0):
        self.specs = specs
        self.call_timeout = call_timeout
        self.tools: dict[str, HubTool] = {}
        self._sessions: dict[str, ClientSession] = {}
        self._stack = AsyncExitStack()

    async def __aenter__(self) -> MCPHub:
        try:
            for spec in self.specs:
                await self._connect(spec)
        except BaseException:
            await self._stack.aclose()
            raise
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._stack.aclose()

    async def _connect(self, spec: ServerSpec) -> None:
        params = StdioServerParameters(
            command=spec.command,
            args=spec.args,
            env={**os.environ, **(spec.env or {})},
            cwd=spec.cwd,
        )
        read, write = await self._stack.enter_async_context(stdio_client(params, errlog=open(os.devnull, "w")))
        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self._sessions[spec.name] = session

        listing = await session.list_tools()
        for t in listing.tools:
            hub_tool = HubTool(
                name=f"{spec.name}{SEP}{t.name}",
                server=spec.name,
                remote_name=t.name,
                description=t.description or t.title or t.name,
                input_schema=t.input_schema,
                annotations=t.annotations,
            )
            self.tools[hub_tool.name] = hub_tool

    def anthropic_tools(self, names: list[str] | None = None) -> list[dict[str, Any]]:
        """Tool definitions for the Claude API, in a stable order (keeps the prompt cache warm)."""
        chosen = sorted(names) if names is not None else sorted(self.tools)
        return [self.tools[n].to_anthropic() for n in chosen]

    async def call(self, name: str, arguments: dict[str, Any]) -> ToolOutcome:
        tool = self.tools.get(name)
        if tool is None:
            return ToolOutcome(f"unknown tool {name!r}", is_error=True)
        session = self._sessions[tool.server]
        try:
            with anyio.fail_after(self.call_timeout):
                result = await session.call_tool(tool.remote_name, arguments)
        except TimeoutError as e:
            raise TransientToolError(f"{name} timed out after {self.call_timeout}s") from e
        except (anyio.ClosedResourceError, anyio.BrokenResourceError, OSError) as e:
            raise TransientToolError(f"{name}: transport failed: {e}") from e
        return ToolOutcome(_render(result), is_error=bool(result.is_error))
