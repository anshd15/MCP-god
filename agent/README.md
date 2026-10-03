# mcp-agent

Multi-agent system built on MCP. A **planner** agent breaks a task into steps, and an **executor** agent completes each step by calling tools served by MCP servers. Both run on Claude Opus 5.5. Every tool call passes through retries and guardrails, and every action is traced with OpenTelemetry.

```
task ─▶ Planner (structured JSON plan)
          │
          ▼
   for each step ─▶ Executor tool loop ─▶ guardrails ─▶ retry ─▶ MCP hub ─▶ fs / sqlite servers
          │                 ▲                                         │
          │                 └──── fenced + injection-scanned output ◀─┘
          ├─ step failed? ─▶ Planner.replan (bounded)
          ▼
     Synthesizer ─▶ answer          all of it ─▶ OpenTelemetry spans (JSONL + OTLP)
```

## Features

| Concern | Implementation |
|---|---|
| Tools | `servers/fs_server.py` (sandboxed files), `servers/sqlite_server.py` (read-only SQL). Configure more in `servers.json` |
| Hub | `hub.py`: one stdio session per server, tools namespaced as `server__tool`, per-call timeouts |
| Retries | `retry.py`: jittered exponential backoff for transport failures. Claude calls use the SDK's built-in retries |
| Policy | `guardrails.py`: allow, ask, or deny per tool, from config globs and MCP annotations (read-only tools are allowed; mutating tools need approval) |
| Validation | Tool arguments are checked against each tool's JSON schema before the call |
| Budgets | Caps on steps, tool calls, and tokens per run |
| Prompt injection | Tool output is truncated, fenced in `<tool_output>`, and scanned. Hits add a warning and are recorded on the span |
| Tracing | `tracing.py`: spans for `run → plan → step → llm.call / tool.call → synthesize`, written to `traces/*.jsonl`. Set `OTEL_EXPORTER_OTLP_ENDPOINT` to send them to Jaeger or Langfuse |
| Replanning | After a failed step the planner routes around it, at most `max_replans` times |

## Run

```bash
cd agent
uv sync
export ANTHROPIC_API_KEY=...
uv run mcp-agent run "Which product earned the most revenue? Write a short report to report.md"
uv run mcp-agent trace traces/<run_id>.jsonl
```

`fs__write_file` asks for approval in the terminal. Pass `--yes` to auto-approve.

To see the injection guardrail, try `"Summarize vendor_reply.txt"`. That file contains a planted injection.

## Test

```bash
uv run pytest
```

The tests run offline. They start the real MCP servers over stdio and swap Claude for a scripted model. The end-to-end test checks that injected text gets flagged, that a write without approval is denied, that the planner replans, and that the trace has the expected spans.
