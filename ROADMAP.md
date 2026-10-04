# Roadmap

## Phase 1 - Knowledge base (DONE in this commit series)
- [x] Repo scaffold and outline
- [x] Fundamentals, architecture, primitives, transports, server taxonomy
- [x] Custom MCP build guide (Python + TypeScript)
- [x] Security and auth notes
- [x] Two runnable starter servers
- [x] Animated companion site (site/) deployed on Vercel

## Phase 2 - Hands-on lab (next)
- [ ] Build 5 servers of increasing complexity: echo -> filesystem -> SQLite -> REST wrapper -> stateful agent tool
- [ ] Add a `clients/` folder with a tiny Python MCP client that lists tools and calls them (no LLM needed)
- [ ] Add MCP Inspector walkthrough with screenshots
- [ ] Add a test harness: spawn server over stdio, assert `tools/list` output

## Phase 2.5 - Multi-agent system (DONE, agent/)
- [x] Planner/executor agents on Claude over an MCP hub (fs + SQLite servers)
- [x] Retries, tool policy + approvals, schema validation, budgets
- [x] Prompt-injection fencing and scanning of tool output
- [x] OpenTelemetry tracing (JSONL + OTLP), trace viewer CLI
- [x] Offline end-to-end tests with a scripted model
- [x] Eval set of tasks with graded answers, run in CI
- [x] Parallel execution of read-only tool calls within a turn
- [x] Prompt caching and per-run cost accounting with a dollar budget
- [x] Remote servers over Streamable HTTP; web fetch server with allowlist + SSRF guard
- [ ] Parallel execution of independent plan steps (needs a dependency-aware planner)
- [ ] LLM-judge graders for open-ended answers
- [ ] Publish live eval results on the site

## Phase 3 - Remote + auth
- [ ] Deploy a Streamable HTTP server (Cloudflare Workers or a small VPS). The agent hub can already connect to one
- [ ] Implement OAuth 2.1 with PKCE, dynamic client registration
- [ ] Document token audience, resource indicators, and refresh flows

## Phase 4 - Production patterns
- [ ] Gateway / aggregator server that proxies multiple upstream servers
- [ ] Observability: structured logs, tracing per request id, rate limits
- [ ] Prompt-injection red-team of my own servers, write findings

## Phase 5 - Publish
- [ ] Package one server to PyPI and one to npm
- [ ] Submit to MCP registry
- [ ] Write a blog-style summary of lessons learned

## Open questions to research
- How do hosts decide which tools to surface when 50+ servers are connected?
- Best practice for long-running tool calls (progress notifications vs. polling resources)?
- Where should caching live: server, client, or host?
