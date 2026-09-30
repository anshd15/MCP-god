# Roadmap

## Phase 1 - Knowledge base (DONE in this commit series)
- [x] Repo scaffold and outline
- [x] Fundamentals, architecture, primitives, transports, server taxonomy
- [x] Custom MCP build guide (Python + TypeScript)
- [x] Security and auth notes
- [x] Two runnable starter servers

## Phase 2 - Hands-on lab (next)
- [ ] Build 5 servers of increasing complexity: echo -> filesystem -> SQLite -> REST wrapper -> stateful agent tool
- [ ] Add a `clients/` folder with a tiny Python MCP client that lists tools and calls them (no LLM needed)
- [ ] Add MCP Inspector walkthrough with screenshots
- [ ] Add a test harness: spawn server over stdio, assert `tools/list` output

## Phase 3 - Remote + auth
- [ ] Deploy a Streamable HTTP server (Cloudflare Workers or a small VPS)
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
