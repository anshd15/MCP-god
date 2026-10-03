"""Read-only SQLite MCP server.

The database is opened with SQLite's `mode=ro` URI flag and a statement
authorizer that only allows reads, so even a crafted query cannot write.
A small demo database is created on first run if MCP_SQLITE_DB is missing.

Run: uv run servers/sqlite_server.py
"""

import os
import sqlite3
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

DB_PATH = Path(os.environ.get("MCP_SQLITE_DB", Path(__file__).parent.parent / "data" / "demo.db")).resolve()
MAX_ROWS = 200

mcp = MCPServer("sqlite", instructions="Read-only SQL over a demo sales database.")

READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False)

_ALLOWED = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}


def _seed(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, country TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(id),
                             product TEXT, amount REAL, ordered_at TEXT);
        INSERT INTO customers VALUES (1,'Asha','IN'),(2,'Ben','US'),(3,'Chloe','FR'),(4,'Dev','IN');
        INSERT INTO orders VALUES
          (1,1,'razor',24.0,'2026-07-02'),(2,1,'blades',12.5,'2026-08-11'),
          (3,2,'razor',24.0,'2026-08-15'),(4,3,'trimmer',59.0,'2026-08-20'),
          (5,4,'blades',12.5,'2026-09-01'),(6,4,'trimmer',59.0,'2026-09-03'),
          (7,2,'blades',12.5,'2026-09-14');
        """
    )
    con.commit()
    con.close()


def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        _seed(DB_PATH)
    con = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    con.set_authorizer(lambda action, *_: sqlite3.SQLITE_OK if action in _ALLOWED else sqlite3.SQLITE_DENY)
    return con


@mcp.tool(annotations=READ_ONLY)
def list_tables() -> str:
    """List tables with their CREATE statements."""
    with _connect() as con:
        rows = con.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    return "\n\n".join(f"-- {name}\n{sql};" for name, sql in rows)


@mcp.tool(annotations=READ_ONLY)
def query(sql: str) -> str:
    """Run one read-only SELECT. Returns a pipe-separated table, max 200 rows."""
    with _connect() as con:
        try:
            cur = con.execute(sql)
        except sqlite3.DatabaseError as e:
            raise ToolError(f"query rejected: {e}") from e
        cols = [d[0] for d in cur.description or []]
        rows = cur.fetchmany(MAX_ROWS + 1)
    out = [" | ".join(cols)] + [" | ".join(str(v) for v in r) for r in rows[:MAX_ROWS]]
    if len(rows) > MAX_ROWS:
        out.append(f"(truncated at {MAX_ROWS} rows)")
    return "\n".join(out)


if __name__ == "__main__":
    mcp.run()
