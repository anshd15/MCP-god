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
| Tools | `servers/fs_server.py` (sandboxed files), `servers/sqlite_server.py` (read-only SQL), `servers/web_server.py` (fetch with domain allowlist and SSRF guard). Configure more in `servers.json` |
| Hub | `hub.py`: local stdio servers or remote Streamable HTTP servers (`"url"` + `"headers"` in `servers.json`), tools namespaced as `server__tool`, per-call timeouts |
| Parallelism | Read-only, auto-allowed tool calls from one model turn run concurrently; calls that need approval run after, in order |
| Retries | `retry.py`: jittered exponential backoff for transport failures. Claude calls use the SDK's built-in retries |
| Policy | `guardrails.py`: allow, ask, or deny per tool, from config globs and MCP annotations (read-only tools are allowed; mutating tools need approval) |
| Validation | Tool arguments are checked against each tool's JSON schema before the call |
| Budgets | Caps on steps, tool calls, tokens, and dollars per run (`--max-cost`) |
| Cost | `costs.py` prices every response (input, output, cache read/write) using the model that actually served it. Shown per span and per run |
| Caching | Planner and executor requests use prompt caching, so each tool-loop turn reads the previous prefix from cache |
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

## More tools

| Module | Use |
|---|---|
| `clients/list_tools.py` | No-LLM client: list hub tools or call one with JSON args |
| `servers/memory_server.py` | Persistent key-value memory shared across runs |
| `mcp_agent/gateway.py` | One MCP server forwarding every allowed hub tool (`python -m mcp_agent.gateway`) |
| `mcp_agent/ratelimit.py` | Token-bucket limits per tool glob |
| `mcp_agent/logs.py` | JSON logs carrying trace and span ids |
| `evals/judge_tasks.jsonl` | Open-ended tasks graded by an LLM judge |

## Evaluate

```bash
uv run mcp-agent eval evals/tasks.jsonl --min-pass 0.8
uv run mcp-agent eval evals/tasks.jsonl --only injection-resistance sandbox-escape
```

[evals/tasks.jsonl](evals/tasks.jsonl) has 12 tasks with ground truth from the demo data:
- SQL questions
- Tasks that combine servers
- A report-writing task
- Safety tasks: prompt injection, writes without approval, sandbox escape, deleting from the read-only DB
- One web task

Each task runs against a scratch copy of the workspace. Graders check the answer, the files left behind, and which tool calls the trace recorded. The report shows pass rate, cost, latency, and tool calls per task. Results go to `evals/results/`.

## CI

[.github/workflows/agent.yml](../.github/workflows/agent.yml) runs the offline tests on Linux and Windows. On pushes to `main`, it also runs the live evals and fails below an 80% pass rate. The eval job only runs when the `ANTHROPIC_API_KEY` repository secret is set.

## Test

```bash
uv run pytest
```

The tests run offline. They start the real MCP servers over stdio and swap Claude for a scripted model. The end-to-end test checks that injected text gets flagged, that a write without approval is denied, that the planner replans, and that the trace has the expected spans.
