# MCP-god

A personal knowledge base and build lab for the **Model Context Protocol (MCP)**.
Goal: understand every kind of MCP server/client/transport deeply enough to build, audit, and ship custom ones.

## What is in here

| Section | File | Purpose |
|---|---|---|
| Fundamentals | [docs/01-fundamentals.md](docs/01-fundamentals.md) | What MCP is, why it exists, mental model |
| Architecture | [docs/02-architecture.md](docs/02-architecture.md) | Host / Client / Server, lifecycle, JSON-RPC |
| Primitives | [docs/03-primitives.md](docs/03-primitives.md) | Tools, Resources, Prompts, Sampling, Roots, Elicitation |
| Transports | [docs/04-transports.md](docs/04-transports.md) | stdio, Streamable HTTP, legacy SSE, in-process |
| Server types | [docs/05-server-types.md](docs/05-server-types.md) | Taxonomy of MCP servers with real examples |
| Build custom | [docs/06-build-custom-mcp.md](docs/06-build-custom-mcp.md) | Step-by-step: Python + TypeScript, testing, publishing |
| Security | [docs/07-security-and-auth.md](docs/07-security-and-auth.md) | OAuth, prompt injection, sandboxing, trust boundaries |
| Examples | [examples/](examples/) | Minimal runnable servers |
| Roadmap | [ROADMAP.md](ROADMAP.md) | Where this project goes next |

## Outline (Phase 1 = this repo's first 6 commits)

1. Scaffold repo, outline, roadmap
2. Fundamentals + architecture docs
3. Primitives deep-dive
4. Transports + server taxonomy
5. Custom MCP build guide + security
6. Runnable Python and TypeScript starter servers

## How to use this repo

- Read `docs/` in order. Each file is self-contained with subsections you can skim or dig into.
- Run `examples/` to see the concepts live in Claude Desktop / Claude Code / any MCP client.
- Track progress and next steps in `ROADMAP.md`.

## Quick glossary

- **Host**: the AI app (Claude Desktop, Claude Code, Cursor, an agent you wrote).
- **Client**: the connector inside the host; one client per server connection.
- **Server**: the program that exposes tools/resources/prompts over MCP.
- **Transport**: how bytes move between client and server (stdio, HTTP).
- **Primitive**: a capability type the protocol defines (tool, resource, prompt, ...).
