# 05 - Types of MCP Servers (taxonomy)

MCP does not define "types" formally; every server is just a set of primitives over a transport. In practice, servers fall into recognisable categories. Knowing them helps you pick patterns and spot risks.

## 5.1 By deployment

| Type | Where it runs | Transport | Auth | Examples |
|---|---|---|---|---|
| Local | User's machine, spawned by host | stdio | None (OS user) | filesystem, git, sqlite, puppeteer |
| Remote (hosted) | Vendor cloud | Streamable HTTP | OAuth 2.1 | GitHub, Linear, Notion, Supabase, Figma |
| Self-hosted remote | Your VPS or Workers | Streamable HTTP | OAuth or API key | Internal company tools |
| Embedded / in-process | Same process as host | in-memory | N/A | Tests, Agent SDK custom tools |

## 5.2 By what they wrap

### Filesystem servers
- Expose read, write, search, list over a set of roots.
- Should honour `roots/list` and refuse paths outside.
- Risk: path traversal, symlink escape.

### Database servers
- Tools like `query`, `list_tables`, `describe_table`; resources for schemas.
- Read-only mode by default; separate `execute` tool with `destructiveHint`.
- Examples: sqlite, postgres, Supabase, BigQuery.

### API wrapper servers
- Thin adapters over a REST or GraphQL API (Slack, GitHub, Stripe, Jira).
- Pattern: one tool per meaningful action, not one per endpoint.
- Watch out for pagination, rate limits, and token scopes.

### Browser and automation servers
- Puppeteer, Playwright, Chrome extensions, computer use.
- High power, high risk. Hosts usually gate every action.

### Knowledge and retrieval servers
- Vector search, docs search, RAG. Return chunks with source URIs as `resource_link`.
- Good fit for resources plus a `search` tool.

### Code and dev tool servers
- Language servers, linters, test runners, git, Docker.
- Often use roots to scope to the open project.

### Agent-as-server
- The server itself runs an LLM loop (maybe via sampling) and exposes one high-level tool like `research(topic)`.
- Enables agent-to-agent composition through MCP.

### Aggregator / gateway servers
- One server that connects to many upstream servers and re-exposes their tools, possibly with namespacing, filtering, auth injection, logging.
- Solves the "host has 30 servers configured" problem.
- Examples: mcp-proxy, enterprise gateways, Zapier MCP (9000+ apps behind one server).

### Meta / registry servers
- Let the model discover and install other servers. E.g. a registry search tool.

## 5.3 By primitive mix

| Profile | Tools | Resources | Prompts | Typical |
|---|---|---|---|---|
| Action server | many | none | few | Slack, GitHub |
| Data server | few | many | none | docs, logs |
| Workflow server | some | some | many | onboarding, review bots |
| Pure prompt pack | none | none | many | style guides |

## 5.4 By statefulness

- **Stateless**: every `tools/call` is independent. Easiest to scale; works with serverless.
- **Session-stateful**: keeps per-session context (open DB connection, browser tab). Needs `Mcp-Session-Id` and cleanup on `DELETE`.
- **Globally stateful**: shared state across all users (a queue, a cache). Needs locking and auth.

## 5.5 By trust level

| Level | Description | Host behaviour |
|---|---|---|
| First-party | You wrote it | Auto-allow reads |
| Verified vendor | Official connector | Allow with scopes |
| Community | Unknown author | Prompt on every write; sandbox |
| Untrusted input inside a trusted server | e.g. a web-fetch server returning a page | Treat returned text as data, never instructions |

## 5.6 Real-world reference list

Official reference servers (modelcontextprotocol/servers): filesystem, git, fetch, memory, sequential-thinking, time, everything (test server).
Popular third-party: GitHub, Slack, Notion, Linear, Supabase, Postgres, Playwright, Puppeteer, Brave Search, Cloudflare, Sentry, Stripe, Figma, Blender, Apify, Zapier.

## 5.7 Picking a design for your own server

1. Decide deployment (local vs remote) from who needs it.
2. Decide primitive mix from what the model needs to *do* vs *see*.
3. Decide statefulness; default to stateless.
4. Write annotations honestly; hosts trust them for confirmation prompts.
5. If it wraps external content, document injection risk in the README.
