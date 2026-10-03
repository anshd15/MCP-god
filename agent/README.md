# mcp-agent

Multi-agent system built on MCP: a **planner** breaks a task into steps, an **executor** carries out each step by calling tools exposed by MCP servers. Every tool call passes through retries and guardrails, and every action is traced with OpenTelemetry.

Work in progress. See [../ROADMAP.md](../ROADMAP.md).
