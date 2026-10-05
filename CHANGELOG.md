# Changelog

All notable changes, newest first. Dates are the day the commit series landed.

## 2026-10-05

- Contributor guide, changelog, editor config, issue and PR templates.
- Glossary and FAQ guides in `docs/`.
- Site: Open Graph metadata and an Agent link in the nav.
- Roadmap and README updated to reflect `agent/`.

## 2026-10-04

- `agent/`: parallel read-only tool calls, prompt-prefix caching, dollar cost budget.
- `agent/`: Streamable HTTP hub client, web-fetch MCP server with SSRF guard.
- `agent/`: eval harness with deterministic graders and a 12-task set.
- CI on Linux and Windows; live evals on `main`.

## 2026-10-03

- `agent/`: scaffolded `mcp-agent` package.
- Sandboxed filesystem and read-only SQLite MCP servers.
- MCP hub with namespaced tools, call timeouts, retries with jittered backoff.
- Tool policy, schema validation, run budgets, untrusted-output fencing, injection scan.
- OpenTelemetry tracing, Claude planner, guarded executor, orchestrator, CLI.
- `examples/python-basic` ported to `mcp` 2.x.

## 2026-10-02

- `site/`: animated companion page deployed to https://mcp-god.vercel.app.

## 2026-10-01

- Phase 1: seven guides in `docs/`, Python and TypeScript starter servers, roadmap.
