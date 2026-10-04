# 06 - Building a Custom MCP Server

Two official SDK paths shown side by side: **Python (`MCPServer` inside the `mcp` package; called FastMCP before mcp 2.0)** and **TypeScript (`@modelcontextprotocol/sdk`)**. Other SDKs exist (Java, Kotlin, C#, Go, Rust, Swift, Ruby) and follow the same shape.

## 6.1 Decide before coding

- Name and one-sentence purpose.
- Deployment: stdio (local) or Streamable HTTP (remote).
- Primitives: which tools, which resources, which prompts.
- Auth: none (stdio), API key env var, or OAuth.
- Roots: will it respect them?

## 6.2 Python: minimal stdio server

Install:
```bash
uv init my-server && cd my-server && uv add "mcp[cli]"
```

`server.py`:
```python
from mcp.server.mcpserver import MCPServer  # mcp>=2; in 1.x: from mcp.server.fastmcp import FastMCP

mcp = MCPServer("demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers. Use for exact arithmetic."""
    return a + b

@mcp.resource("greeting://{name}")
def greeting(name: str) -> str:
    """A personalised greeting resource."""
    return f"Hello, {name}!"

@mcp.prompt()
def review(code: str) -> str:
    """Ask for a code review."""
    return f"Please review this code and list bugs first:\n\n{code}"

if __name__ == "__main__":
    mcp.run()  # stdio by default
```

Run and inspect:
```bash
uv run mcp dev server.py
```

Register in Claude Code:
```bash
claude mcp add demo -- uv run --directory /abs/path/my-server server.py
```

Switch to HTTP:
```python
mcp.run(transport="streamable-http")  # serves on http://127.0.0.1:8000/mcp
```

## 6.3 TypeScript: minimal stdio server

Install:
```bash
mkdir my-server && cd my-server && npm init -y
npm i @modelcontextprotocol/sdk zod
npm i -D typescript @types/node
```

`src/index.ts`:
```ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({ name: "demo", version: "0.1.0" });

server.registerTool(
  "add",
  {
    title: "Add",
    description: "Add two integers. Use for exact arithmetic.",
    inputSchema: { a: z.number(), b: z.number() },
  },
  async ({ a, b }) => ({ content: [{ type: "text", text: String(a + b) }] })
);

server.registerResource(
  "greeting",
  "greeting://{name}",
  { title: "Greeting", description: "Personalised greeting" },
  async (uri) => ({ contents: [{ uri: uri.href, text: `Hello, ${uri.host}!` }] })
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

Build and run:
```bash
npx tsc && node dist/index.js
```

Switch to HTTP: use `StreamableHTTPServerTransport` with Express; one transport per session keyed by `Mcp-Session-Id`.

## 6.4 Anatomy of a good tool implementation

```python
@mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
async def search_docs(query: str, limit: int = 5) -> str:
    """Search internal docs. Use when the user asks how something works.
    Returns up to `limit` snippets with source URLs."""
    if not query.strip():
        raise ValueError("query must not be empty")  # becomes isError result
    results = await backend.search(query, limit)
    return "\n\n".join(f"[{r.title}]({r.url})\n{r.snippet}" for r in results)
```

Checklist:
- Docstring / description starts with what it does, then when to use it.
- Typed parameters generate the JSON Schema automatically.
- Return concise text the model can quote.
- Raise on bad input; the SDK converts to a tool error, not a crash.
- Async if it does I/O.

## 6.5 Adding progress, logging, and cancellation

Python MCPServer gives you a `Context`:
```python
from mcp.server.mcpserver import Context

@mcp.tool()
async def long_job(n: int, ctx: Context) -> str:
    for i in range(n):
        await ctx.report_progress(i, n)
        await ctx.info(f"step {i}")
    return "done"
```
TypeScript: the handler receives `extra` with `sendNotification`, `signal` (AbortSignal for cancellation), and `_meta.progressToken`.

## 6.6 Using client-side primitives from the server

- **Sampling**: `await ctx.session.create_message(messages=[...], max_tokens=200)` (Python) / `server.server.createMessage(...)` (TS). Check the client declared `sampling` first.
- **Roots**: `await ctx.session.list_roots()`.
- **Elicitation**: `await ctx.elicit(message="Which env?", schema=EnvChoice)`.

## 6.7 Testing

1. **MCP Inspector**: `npx @modelcontextprotocol/inspector uv run server.py`.
2. **In-memory client test** (Python):
```python
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def test_add():
    params = StdioServerParameters(command="uv", args=["run", "server.py"])
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool("add", {"a": 2, "b": 3})
            assert res.content[0].text == "5"
```
3. **Golden JSON**: snapshot `tools/list` output so schema drift is caught in CI.

## 6.8 Packaging and distribution

| Target | How |
|---|---|
| PyPI | `uv build && uv publish`; users run `uvx my-server` |
| npm | `npm publish`; users run `npx my-server` |
| Docker | Expose stdio via `docker run -i`, or HTTP port |
| Desktop Extension (.mcpb / .dxt) | Bundle for one-click install in Claude Desktop |
| Registry | Publish `server.json` to the MCP registry |

## 6.9 Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Server "failed to start" | Wrong PATH or interpreter in host | Absolute paths; test with the same env |
| Tools never appear | Forgot `notifications/initialized` or crashed before `initialize` | Check stderr logs |
| JSON parse error | `print()` to stdout | Log to stderr |
| Tool called with wrong args | Vague description or schema | Tighten types, add examples in description |
| Hangs on long tool | No progress, host timeout | Report progress; chunk work |
| Works in Inspector, not in Claude | Env vars missing in host config | Add `env` block |

## 6.10 Project template

```
my-server/
  README.md          # what it does, install, tools table
  pyproject.toml     # or package.json
  src/my_server/
    __init__.py
    server.py        # MCPServer instance + entry point
    tools/           # one module per tool group
    resources/
  tests/
    test_tools.py
  server.json        # registry manifest
```
