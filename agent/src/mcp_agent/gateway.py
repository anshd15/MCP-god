"""Gateway: serve every hub tool as one MCP server, with the agent policy applied.

Point any MCP host at this one server instead of N upstream servers:
    claude mcp add mcp-god-gateway -- uv run --directory <agent dir> python -m mcp_agent.gateway
Denied tools are hidden. Tools that need approval are refused, since there is no human in the loop here.
"""

from __future__ import annotations

import sys
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .guardrails import Decision, Policy, validate_args, wrap_untrusted
from .hub import MCPHub, load_config


async def serve(config: str = "servers.json") -> None:
    specs, policy_cfg = load_config(config)
    policy = Policy.from_config(policy_cfg)
    async with MCPHub(specs) as hub:
        gateway = MCPServer("mcp-god-gateway", instructions="Aggregated tools from every server in servers.json.")
        allowed = {n: t for n, t in hub.tools.items() if policy.decide(t) == Decision.ALLOW}

        @gateway.tool(annotations=None)
        async def call(tool: str, arguments: dict[str, Any] | None = None) -> str:
            """Call an upstream tool by its namespaced name (see list_upstream_tools)."""
            t = allowed.get(tool)
            if t is None:
                raise ToolError(f"{tool} is not allowed through the gateway")
            args = arguments or {}
            if err := validate_args(t, args):
                raise ToolError(err)
            out = await hub.call(tool, args)
            if out.is_error:
                raise ToolError(out.text)
            return wrap_untrusted(tool, out.text)[0]

        @gateway.tool()
        def list_upstream_tools() -> str:
            """List upstream tools the gateway will forward, with their input schemas."""
            import json

            return "\n\n".join(
                f"{t.name}: {t.description}\n{json.dumps(t.input_schema)}" for t in sorted(allowed.values(), key=lambda t: t.name)
            )

        await gateway.run_stdio_async()


if __name__ == "__main__":
    import anyio

    anyio.run(serve, *(sys.argv[1:2] or ["servers.json"]))
