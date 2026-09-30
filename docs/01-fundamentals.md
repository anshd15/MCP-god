# 01 - MCP Fundamentals

## 1.1 What MCP is

The **Model Context Protocol** is an open standard (released by Anthropic in Nov 2024, now run as an open project with a steering committee) that defines how an AI application talks to external systems. Think of it as **USB-C for AI tools**: one plug shape, any device.

Before MCP, every AI app wrote bespoke integrations for every data source. With MCP:

- A **server** exposes capabilities once.
- Any **host** that speaks MCP can use them.
- N apps x M tools becomes N + M integrations.

## 1.2 The core problem it solves

| Without MCP | With MCP |
|---|---|
| Each app hard-codes tool schemas | Servers self-describe via `tools/list` |
| Data access logic lives inside the app | Logic lives in a separate, reusable process |
| Vendor lock-in per app | Portable across Claude, Cursor, VS Code, custom agents |
| No standard for auth, streaming, cancellation | Spec covers all of these |

## 1.3 Mental model

```
+-----------+      +----------+      +-----------+
|   Host    | <--> |  Client  | <--> |  Server   |
| (AI app)  |      | (1 per   |      | (your     |
|           |      |  server) |      |  code)    |
+-----------+      +----------+      +-----------+
      ^                                     |
      |          JSON-RPC 2.0 messages      |
      +----- over a transport (stdio/HTTP) -+
```

- The **LLM** never talks to the server directly. The host decides when to call a tool, based on the tool descriptions the client fetched.
- The server never sees the conversation. It only sees the request it is sent.

## 1.4 What MCP is NOT

- Not an agent framework. It does not decide *when* to call tools.
- Not a model API. It does not replace the Messages API or OpenAI API.
- Not only for Claude. Any client that implements the spec works.
- Not a security boundary by itself. You still need sandboxing and auth.

## 1.5 Key vocabulary

| Term | Meaning |
|---|---|
| Host | The application containing the LLM loop (Claude Desktop, Claude Code, Cursor, your agent) |
| Client | The protocol implementation inside the host; maintains one session with one server |
| Server | A process exposing tools, resources, prompts |
| Transport | stdio or Streamable HTTP; carries JSON-RPC |
| Capability | Something a party declares during `initialize` (e.g. `tools`, `resources`, `sampling`) |
| Primitive | A category of thing a server or client exposes (tool, resource, prompt, sampling, roots, elicitation) |
| Session | One initialized connection; has a lifecycle and negotiated protocol version |

## 1.6 Protocol versions

The spec is dated: `2024-11-05`, `2025-03-26`, `2025-06-18`, and later revisions. Client and server negotiate the version during `initialize`. Newer versions added Streamable HTTP, OAuth 2.1 resource-server semantics, elicitation, structured tool output, and tool annotations.

## 1.7 Where MCP is used today

- Claude Desktop and Claude Code (local stdio servers + remote connectors)
- IDEs: Cursor, Windsurf, VS Code (Copilot agent mode), Zed, JetBrains
- Agent SDKs: Claude Agent SDK, OpenAI Agents SDK, LangChain, CrewAI adapters
- Hosted connectors: GitHub, Slack, Notion, Linear, Supabase, Figma, Zapier, Apify, Blender, etc.

## 1.8 One-paragraph summary to memorise

MCP is a JSON-RPC 2.0 based protocol where a host application (via a client) connects to servers that advertise tools, resources, and prompts. The host fetches those descriptions, lets the LLM choose actions, and the client forwards calls to the server over stdio or HTTP. Servers can also ask the client for things (sampling, roots, elicitation). Everything is capability-negotiated at session start.
