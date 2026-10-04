"""Minimal MCP server in Python using MCPServer (mcp 2.x; FastMCP in 1.x).

Run:   uv run server.py            (stdio)
Test:  npx @modelcontextprotocol/inspector uv run server.py
Add:   claude mcp add mcp-god-py -- uv run --directory <abs path> server.py
"""

from datetime import datetime, timezone

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

mcp = MCPServer("mcp-god-python")

NOTES: dict[str, str] = {}


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def now() -> str:
    """Current UTC time in ISO 8601. Use when the user asks the time or date."""
    return datetime.now(timezone.utc).isoformat()


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers exactly. Use instead of mental arithmetic."""
    return a + b


@mcp.tool(annotations=ToolAnnotations(idempotent_hint=True))
def save_note(key: str, text: str) -> str:
    """Save a short note under a key. Overwrites if the key exists."""
    if not key.strip():
        raise ToolError("key must not be empty")  # ToolError text reaches the client
    NOTES[key] = text
    return f"saved {key!r} ({len(text)} chars)"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def list_notes() -> str:
    """List saved note keys."""
    return "\n".join(sorted(NOTES)) or "(no notes)"


@mcp.resource("note://{key}")
def read_note(key: str) -> str:
    """Read one note by key."""
    return NOTES.get(key, f"no note named {key!r}")


@mcp.prompt()
def summarize_notes() -> str:
    """Ask the model to summarise all saved notes."""
    body = "\n\n".join(f"## {k}\n{v}" for k, v in sorted(NOTES.items()))
    return f"Summarise these notes in three bullets:\n\n{body or '(empty)'}"


@mcp.tool()
async def count_to(n: int, ctx: Context) -> str:
    """Count to n with progress updates. Demonstrates progress + logging."""
    for i in range(1, n + 1):
        await ctx.report_progress(i, n)
        await ctx.info(f"at {i}")
    return f"counted to {n}"


if __name__ == "__main__":
    mcp.run()
