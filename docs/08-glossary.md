# 08 - Glossary

Short definitions, alphabetical. Each links to the guide that explains it.

| Term | Definition | See |
|---|---|---|
| Annotation | Hint on a tool (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) that hosts use for confirmation policy | [03 §3.1](03-primitives.md) |
| Capability | A feature a client or server declares during `initialize`; requests for undeclared capabilities are invalid | [02 §2.5](02-architecture.md) |
| Client | The protocol implementation inside a host; one per server session | [02 §2.1](02-architecture.md) |
| Completion | `completion/complete`, autocomplete for prompt arguments and resource template variables | [03 §3.7](03-primitives.md) |
| Elicitation | Server asks the user for structured input mid-request via `elicitation/create` | [03 §3.6](03-primitives.md) |
| Host | The AI application that owns the LLM loop, UI, and permissions | [02 §2.1](02-architecture.md) |
| Hub | An aggregator that connects to many servers and re-exposes their tools under namespaces | [05 §5.2](05-server-types.md) |
| `isError` | Flag on a tool result marking a tool-level failure, distinct from a JSON-RPC error | [03 §3.1](03-primitives.md) |
| JSON-RPC 2.0 | The message format: request, response, notification | [02 §2.2](02-architecture.md) |
| `Mcp-Session-Id` | HTTP header carrying the session id for Streamable HTTP | [04 §4.2](04-transports.md) |
| Notification | A JSON-RPC message with no `id` and no response | [02 §2.2](02-architecture.md) |
| Primitive | One of the six capability categories: tools, resources, prompts, sampling, roots, elicitation | [03](03-primitives.md) |
| Progress token | `_meta.progressToken` on a request; the worker emits `notifications/progress` with it | [02 §2.6](02-architecture.md) |
| Prompt | A user-controlled, parameterised message template exposed by a server | [03 §3.3](03-primitives.md) |
| Prompt injection | Untrusted content in tool output that tries to steer the model | [07 §7.1](07-security-and-auth.md) |
| Resource | App-controlled read-only data at a URI | [03 §3.2](03-primitives.md) |
| Resource template | RFC 6570 URI template like `note://{key}` | [03 §3.2](03-primitives.md) |
| Roots | Directories the host grants a server; its sandbox boundary | [03 §3.5](03-primitives.md) |
| Sampling | Server asks the host to run the LLM via `sampling/createMessage` | [03 §3.4](03-primitives.md) |
| Server | A process or service exposing primitives over a transport | [02 §2.1](02-architecture.md) |
| SSE | Server-Sent Events; the streaming half of Streamable HTTP and the legacy transport | [04 §4.3](04-transports.md) |
| stdio | Transport where the host spawns the server and talks over stdin/stdout | [04 §4.1](04-transports.md) |
| Streamable HTTP | Current remote transport: one endpoint, POST per message, optional SSE upgrade | [04 §4.2](04-transports.md) |
| Tool | A model-controlled function with a JSON Schema input | [03 §3.1](03-primitives.md) |
| Tool poisoning | Malicious instructions hidden in a tool description | [07 §7.1](07-security-and-auth.md) |
| Transport | How bytes move between client and server | [04](04-transports.md) |
