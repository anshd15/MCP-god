# 02 - Architecture

## 2.1 The three roles

### Host
- Owns the user interface and the LLM loop.
- Spawns or connects to one client per server.
- Enforces user consent and permission policy.
- Aggregates tools from all servers into one list shown to the model.

### Client
- Lives inside the host. One client equals one server connection.
- Handles `initialize`, capability negotiation, request/response correlation, cancellation, and progress.
- Can *serve* client-side primitives back to the server: sampling, roots, elicitation.

### Server
- Standalone process or remote service.
- Declares capabilities, then answers requests.
- Stateless per-request is the norm; stateful sessions are allowed (Streamable HTTP has a session id header).

## 2.2 Message layer: JSON-RPC 2.0

Three message shapes:

```jsonc
// Request (expects a response)
{ "jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": { "name": "add", "arguments": { "a": 1, "b": 2 } } }

// Response
{ "jsonrpc": "2.0", "id": 1, "result": { "content": [ { "type": "text", "text": "3" } ] } }

// Notification (no id, no response)
{ "jsonrpc": "2.0", "method": "notifications/progress", "params": { "progressToken": "abc", "progress": 40, "total": 100 } }
```

Errors use the standard `error: { code, message, data }` object. Reserved codes: `-32700` parse, `-32600` invalid request, `-32601` method not found, `-32602` invalid params, `-32603` internal.

## 2.3 Session lifecycle

```
Client                                  Server
  |-- initialize (version, capabilities) -->|
  |<-- result (version, capabilities, info) |
  |-- notifications/initialized ----------->|
  |                                         |
  |-- tools/list -------------------------->|
  |<-- tools ------------------------------- |
  |-- tools/call -------------------------->|
  |<-- result / error ---------------------- |
  |                                         |
  |<-- notifications/tools/list_changed ----|   (server can push)
  |-- tools/list -------------------------->|   (client refetches)
  |                                         |
  |-- (transport close) ------------------->|
```

### `initialize` request params
- `protocolVersion`: the newest version the client supports.
- `capabilities`: what the client offers (`roots`, `sampling`, `elicitation`).
- `clientInfo`: `{ name, version }`.

### `initialize` result
- `protocolVersion`: the version the server chose (must be one the client supports or the client disconnects).
- `capabilities`: `{ tools: { listChanged }, resources: { subscribe, listChanged }, prompts: { listChanged }, logging: {}, completions: {} }`.
- `serverInfo`, optional `instructions` (a system-prompt-style hint the host may show the model).

## 2.4 Full method catalogue

| Direction | Method | Purpose |
|---|---|---|
| C to S | `initialize` | Handshake |
| either | `ping` | Liveness |
| C to S | `tools/list`, `tools/call` | Discover and invoke tools |
| C to S | `resources/list`, `resources/read`, `resources/templates/list`, `resources/subscribe`, `resources/unsubscribe` | Read-only data |
| C to S | `prompts/list`, `prompts/get` | Reusable prompt templates |
| C to S | `completion/complete` | Autocomplete for prompt or resource arguments |
| C to S | `logging/setLevel` | Control server log verbosity |
| S to C | `sampling/createMessage` | Server asks host to run the LLM |
| S to C | `roots/list` | Server asks which directories it may touch |
| S to C | `elicitation/create` | Server asks the user for structured input |
| either | `notifications/cancelled`, `notifications/progress` | Long-running call control |
| S to C | `notifications/message` | Log line |
| S to C | `notifications/resources/updated`, `notifications/*/list_changed` | Change signals |

## 2.5 Capability negotiation rules

- A party must not send a request for a capability the other side did not declare.
- Optional sub-flags (`listChanged`, `subscribe`) gate the related notifications.
- Unknown capabilities are ignored, which is how the protocol stays forward compatible.

## 2.6 Concurrency, cancellation, progress

- Requests carry unique ids; responses may arrive out of order.
- Either side may send `notifications/cancelled` with the request id. The receiver should stop work and may still send a late response, which the sender ignores.
- Long tasks: the requester includes `_meta.progressToken`; the worker emits `notifications/progress` with the same token.

## 2.7 Where state lives

| State | Lives in |
|---|---|
| Conversation history | Host only |
| Tool list cache | Client (refreshed on `list_changed`) |
| Session id (HTTP) | Client stores, sends as `Mcp-Session-Id` header |
| Auth tokens | Client or host secure storage |
| Server-side data | Server (DB, files) |

## 2.8 Diagram: multi-server host

```
                 +---------------------------+
                 |          Host             |
                 |  LLM loop + permissions   |
                 |  +--------+  +--------+   |
                 |  |Client A|  |Client B|   |
                 +--+---+----+--+---+----+---+
                        |            |
                  stdio |            | Streamable HTTP
                        v            v
                 +-----------+  +---------------+
                 | Local FS  |  | Remote GitHub |
                 | server    |  | server (OAuth)|
                 +-----------+  +---------------+
```

## 2.9 Design principles baked into the spec

1. **Servers are easy to build.** Hosts handle orchestration; servers focus on one thing.
2. **Servers are composable.** Many small servers beat one giant one.
3. **Servers cannot read the whole conversation.** Isolation is by design.
4. **Features are added progressively.** Capability flags let old and new versions coexist.
