# 04 - Transports

A transport moves JSON-RPC messages between client and server. The protocol layer is identical across transports; only framing, connection setup, and auth differ.

## 4.1 stdio

### How it works
- Host spawns the server as a child process.
- Client writes JSON-RPC messages to the server's **stdin**, one per line (newline-delimited, no embedded newlines).
- Server writes responses to **stdout**.
- **stderr** is for logs only. Anything non-JSON on stdout breaks the connection.

### Config example (Claude Desktop / Claude Code)
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "server.py"],
      "env": { "API_KEY": "..." }
    }
  }
}
```

### Pros
- Zero network setup, no auth needed (same user, same machine).
- Fastest to build and debug.
- Process lifetime equals session lifetime; clean teardown.

### Cons
- Local only. One host per process.
- Environment issues (PATH, Python version, Node version) are the number one cause of "server failed to start".

### Gotchas
- Never `print()` to stdout in a Python stdio server. Use `logging` to stderr.
- Windows: prefer absolute paths to `python.exe` or `node.exe`; PATH inside the host may differ from your terminal.

## 4.2 Streamable HTTP (current standard, spec 2025-03-26 and later)

### How it works
- Single endpoint, e.g. `https://api.example.com/mcp`.
- Client sends each JSON-RPC message as an HTTP **POST**.
- Server replies either with a single JSON response, or upgrades that POST response to an **SSE stream** to send multiple messages (progress, server-initiated requests) before the final result.
- Client may also open a **GET** to the same endpoint to receive server-initiated notifications when no request is in flight.
- Session tracking via `Mcp-Session-Id` header returned on `initialize`; client echoes it on every later request. `DELETE` with that header ends the session.
- Resumability: events carry ids; client can reconnect with `Last-Event-ID`.

### Headers to know
| Header | Purpose |
|---|---|
| `Accept: application/json, text/event-stream` | Client must accept both |
| `Mcp-Session-Id` | Session correlation |
| `MCP-Protocol-Version` | Version negotiated at init |
| `Authorization: Bearer <token>` | OAuth 2.1 access token |
| `Origin` | Server must validate to block DNS rebinding |

### Pros
- Works for remote and multi-tenant servers.
- Serverless friendly (each POST can be stateless if you choose).
- Supports streaming and server push without a permanent connection.

### Cons
- Needs real auth.
- More moving parts: sessions, reconnection, event ids.

## 4.3 HTTP + SSE (legacy, spec 2024-11-05)

- Two endpoints: `GET /sse` (long-lived stream, server sends an `endpoint` event) and `POST /messages` (client sends requests).
- Deprecated in favour of Streamable HTTP but many servers and clients still support it. New servers should implement Streamable HTTP and optionally keep an SSE fallback.

## 4.4 In-process / custom transports

SDKs let you wire a client and server together in memory (useful for tests) or implement your own transport (WebSocket, Unix socket, message queue). The spec only mandates message ordering and framing guarantees, not the wire.

## 4.5 Choosing a transport

```
Runs on the user's machine and only that user needs it?   -> stdio
Shared service, SaaS, multiple users, needs auth?          -> Streamable HTTP
Must support an old client that only knows SSE?            -> Streamable HTTP + SSE fallback
Unit tests?                                                -> in-memory
```

## 4.6 Security notes per transport

- **stdio**: the server runs with the user's full OS permissions. Sandbox it if it executes untrusted input.
- **HTTP**: validate `Origin`, bind local dev servers to `127.0.0.1` not `0.0.0.0`, require TLS in production, verify token audience.

## 4.7 Debugging tools

- **MCP Inspector** (`npx @modelcontextprotocol/inspector`): web UI that connects over stdio or HTTP, lists primitives, lets you call tools, shows raw JSON-RPC.
- `claude mcp add` / `claude mcp list` / `claude mcp get` in Claude Code.
- Log to stderr with request ids so you can correlate.
