"""Sandboxed filesystem MCP server.

Every path is resolved against MCP_FS_ROOT (default: ../workspace) and
rejected if it escapes it. Read tools are marked read-only; write_file is
marked destructive so the agent's guardrails ask before running it.

Run: uv run servers/fs_server.py              (stdio)
     MCP_HTTP_PORT=8765 uv run servers/fs_server.py   (Streamable HTTP at /mcp)
"""

import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

ROOT = Path(os.environ.get("MCP_FS_ROOT", Path(__file__).parent.parent / "workspace")).resolve()
MAX_READ_BYTES = 200_000

mcp = MCPServer("fs", instructions=f"Files under the sandbox root {ROOT.name}/. Paths are relative.")

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)


def _resolve(rel: str) -> Path:
    p = (ROOT / rel).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ToolError(f"path {rel!r} escapes the sandbox")
    return p


@mcp.tool(annotations=READ_ONLY)
def list_dir(path: str = ".") -> str:
    """List entries in a directory (relative to the sandbox root). Directories end with '/'."""
    d = _resolve(path)
    if not d.is_dir():
        raise ToolError(f"{path!r} is not a directory")
    entries = sorted(e.name + ("/" if e.is_dir() else "") for e in d.iterdir())
    return "\n".join(entries) or "(empty)"


@mcp.tool(annotations=READ_ONLY)
def read_file(path: str) -> str:
    """Read a UTF-8 text file (relative to the sandbox root)."""
    f = _resolve(path)
    if not f.is_file():
        raise ToolError(f"{path!r} is not a file")
    data = f.read_bytes()[:MAX_READ_BYTES]
    return data.decode("utf-8", errors="replace")


@mcp.tool(annotations=READ_ONLY)
def search_text(query: str, path: str = ".") -> str:
    """Case-insensitive substring search across text files. Returns path:line: text matches."""
    base = _resolve(path)
    q = query.lower()
    hits: list[str] = []
    for f in sorted(base.rglob("*")):
        if not f.is_file() or f.stat().st_size > MAX_READ_BYTES:
            continue
        try:
            lines = f.read_text("utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(lines, 1):
            if q in line.lower():
                hits.append(f"{f.relative_to(ROOT).as_posix()}:{i}: {line.strip()}")
                if len(hits) >= 50:
                    return "\n".join(hits) + "\n(truncated at 50 matches)"
    return "\n".join(hits) or "(no matches)"


@mcp.tool(annotations=ToolAnnotations(destructive_hint=True, idempotent_hint=True, open_world_hint=False))
def write_file(path: str, content: str) -> str:
    """Create or overwrite a UTF-8 text file (relative to the sandbox root)."""
    f = _resolve(path)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, "utf-8")
    return f"wrote {len(content)} chars to {path}"


if __name__ == "__main__":
    if port := os.environ.get("MCP_HTTP_PORT"):
        mcp.run("streamable-http", host="127.0.0.1", port=int(port))
    else:
        mcp.run()
