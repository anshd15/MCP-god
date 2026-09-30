# Examples

Two identical starter servers, one per SDK. Each exposes:

| Primitive | Name | Notes |
|---|---|---|
| tool | `now` | read-only |
| tool | `add` | pure function |
| tool | `save_note` | idempotent write |
| tool | `list_notes` | read-only |
| resource | `note://{key}` | template resource |
| prompt | `summarize_notes` | zero-arg prompt |
| tool (py only) | `count_to` | progress + logging demo |

## Python

```bash
cd examples/python-basic
uv sync
uv run server.py
```

## TypeScript

```bash
cd examples/typescript-basic
npm install
npm run build
node dist/index.js
```

## Try in Inspector

```bash
npx @modelcontextprotocol/inspector uv run --directory examples/python-basic server.py
```

## Add to Claude Code

```bash
claude mcp add mcp-god-py -- uv run --directory "D:/general _claudecode/MCP-god/examples/python-basic" server.py
```
