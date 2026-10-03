"""mcp-agent: planner/executor agents that act through MCP servers.

Layers, bottom up:
    hub        - connects to MCP servers over stdio, namespaces their tools
    retry      - backoff for transient tool/transport failures
    guardrails - policy, argument validation, budgets, injection scanning
    tracing    - OpenTelemetry spans for every run, step, LLM call, tool call
    agents     - planner (structured plan) and executor (tool loop) on Claude
    orchestrator / cli - glue and entry point
"""

__version__ = "0.1.0"
