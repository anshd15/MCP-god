"""No-LLM MCP client: list every tool in servers.json, or call one directly.

    uv run clients/list_tools.py
    uv run clients/list_tools.py sqlite__query '{"sql": "select count(*) from orders"}'
"""

import json
import sys

import anyio

from mcp_agent.hub import MCPHub, load_config


async def main(argv: list[str]) -> None:
    async with MCPHub(load_config("servers.json")[0]) as hub:
        if not argv:
            for t in sorted(hub.tools.values(), key=lambda t: t.name):
                flag = "ro" if t.read_only else ("destructive" if t.destructive else "write")
                print(f"{t.name:28} [{flag}] {t.description.splitlines()[0]}")
            return
        out = await hub.call(argv[0], json.loads(argv[1]) if len(argv) > 1 else {})
        print(("ERROR: " if out.is_error else "") + out.text)


if __name__ == "__main__":
    anyio.run(main, sys.argv[1:])
