"""Persistent key-value memory MCP server, so agent runs can share facts.

Stored in MCP_MEMORY_DB (default ../data/memory.db). Run: uv run servers/memory_server.py
"""

import os
import sqlite3
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

DB = Path(os.environ.get("MCP_MEMORY_DB", Path(__file__).parent.parent / "data" / "memory.db"))
mcp = MCPServer("memory", instructions="Long-term notes that persist across agent runs.")


def _db() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute(
        "CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT, updated TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    return con


@mcp.tool(annotations=ToolAnnotations(idempotent_hint=True, destructive_hint=False))
def remember(key: str, value: str) -> str:
    """Store or update a fact under a short key."""
    if not key.strip():
        raise ToolError("key must not be empty")
    with _db() as con:
        con.execute(
            "INSERT INTO memory(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=CURRENT_TIMESTAMP",
            (key, value),
        )
    return f"remembered {key!r}"


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def recall(query: str = "") -> str:
    """Return stored facts whose key or value contains query (all facts if empty)."""
    like = f"%{query}%"
    with _db() as con:
        rows = con.execute(
            "SELECT key, value FROM memory WHERE key LIKE ? OR value LIKE ? ORDER BY updated DESC LIMIT 50",
            (like, like),
        ).fetchall()
    return "\n".join(f"{k}: {v}" for k, v in rows) or "(nothing remembered)"


if __name__ == "__main__":
    mcp.run()
