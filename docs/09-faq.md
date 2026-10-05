# 09 - FAQ

Questions that came up while building this repo, with short answers and pointers.

## Is MCP only for Claude?
No. It is an open protocol. Cursor, VS Code, Zed, JetBrains, and the OpenAI Agents SDK all speak it. See [01 §1.7](01-fundamentals.md).

## Tool or resource?
If the model should decide to fetch or compute something with parameters, it is a tool. If the data already exists and the app should surface it, it is a resource. See [03 §3.2](03-primitives.md).

## Why does my stdio server "fail to start" in Claude but work in the terminal?
Almost always PATH or interpreter differences inside the host. Use absolute paths and an `env` block. See [06 §6.9](06-build-custom-mcp.md).

## Why does my server break after I add a print statement?
stdout is the protocol channel on stdio. Anything that is not JSON-RPC corrupts it. Log to stderr. See [04 §4.1](04-transports.md).

## stdio or Streamable HTTP?
Local, single user, no auth: stdio. Shared, remote, multi-user: Streamable HTTP with OAuth 2.1. See [04 §4.5](04-transports.md).

## Does the server see the conversation?
No. It sees only the request it is sent. That isolation is by design. See [02 §2.9](02-architecture.md).

## Can a server call the LLM?
Yes, through sampling, if the client declares the `sampling` capability. The host may show the user a review step first. See [03 §3.4](03-primitives.md).

## How do I stop a tool result from hijacking the model?
Treat tool output as data. Fence it, label it untrusted, and never auto-execute follow-up actions found inside it. The `agent/` package does this. See [07 §7.1](07-security-and-auth.md).

## What is the difference between a JSON-RPC error and `isError: true`?
A JSON-RPC error means the protocol call failed (bad params, unknown method). `isError: true` means the tool ran and reported a failure the model should read and reason about. See [03 §3.1](03-primitives.md).

## How many servers can a host connect to?
As many as it likes, one client each. In practice the tool list gets noisy past a few dozen. A hub that namespaces and filters tools helps. See [05 §5.2](05-server-types.md).

## Which SDK version does this repo target?
Python `mcp` 2.x, where the server class is `MCPServer` (1.x called it `FastMCP`) and fields are snake_case. TypeScript `@modelcontextprotocol/sdk` 1.x. See [06](06-build-custom-mcp.md).

## How do I debug the raw messages?
MCP Inspector shows every JSON-RPC frame. For code, the `agent/` tracer writes JSONL spans per call. See [04 §4.7](04-transports.md).
