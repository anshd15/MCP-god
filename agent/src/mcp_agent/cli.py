"""Command line entry point.

    mcp-agent run "How much revenue did trimmers make? Save a summary to report.md"
    mcp-agent run --yes "..."          # auto-approve mutating tools
    mcp-agent trace traces/<run_id>.jsonl
    mcp-agent eval evals/tasks.jsonl --min-pass 0.8
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import anyio

from .guardrails import Budget
from .hub import HubTool
from .orchestrator import run_task
from .tracing import render_tree


async def _prompt_approver(tool: HubTool, args: dict[str, Any]) -> bool:
    print(f"\n[approval] {tool.name} wants to run with:\n{json.dumps(args, indent=2)[:1500]}", file=sys.stderr)
    answer = await anyio.to_thread.run_sync(lambda: input("Allow? [y/N] "))
    return answer.strip().lower() in {"y", "yes"}


async def _auto_approver(tool: HubTool, args: dict[str, Any]) -> bool:
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mcp-agent")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="plan and execute a task")
    r.add_argument("task")
    r.add_argument("--config", default="servers.json")
    r.add_argument("--yes", action="store_true", help="auto-approve tools that need approval")
    r.add_argument("--max-steps", type=int, default=8)
    r.add_argument("--max-tool-calls", type=int, default=30)
    r.add_argument("--max-cost", type=float, default=2.0, help="stop the run past this many USD")
    tr = sub.add_parser("trace", help="print a trace file as a span tree")
    tr.add_argument("file", type=Path)
    ev = sub.add_parser("eval", help="run a task set and grade the answers")
    ev.add_argument("tasks", type=Path)
    ev.add_argument("--config", default="servers.json")
    ev.add_argument("--only", nargs="*", help="task ids to run")
    ev.add_argument("--min-pass", type=float, default=0.0, help="exit 1 below this pass rate")
    args = p.parse_args(argv)

    if args.cmd == "eval":
        return _eval(args)

    if args.cmd == "trace":
        print(render_tree(args.file))
        return 0

    budget = Budget(max_steps=args.max_steps, max_tool_calls=args.max_tool_calls, max_cost_usd=args.max_cost)
    approver = _auto_approver if args.yes else _prompt_approver
    result = anyio.run(lambda: run_task(args.task, config=args.config, approver=approver, budget=budget))
    print(result.answer)
    print(
        f"\n-- run {result.run_id}: {len(result.steps)} steps, {result.budget.tool_calls} tool calls, "
        f"{result.budget.tokens} tokens, ${result.budget.cost_usd:.4f}. Trace: {result.trace_file}",
        file=sys.stderr,
    )
    return 1 if result.errors else 0


def _eval(args: argparse.Namespace) -> int:
    from .evals import load_tasks, report, run_eval, save

    tasks = load_tasks(args.tasks)
    if args.only:
        tasks = [t for t in tasks if t["id"] in set(args.only)]
    results = anyio.run(lambda: run_eval(tasks, config=args.config))
    print(report(results))
    print(f"
results: {save(results)}", file=sys.stderr)
    rate = sum(r.passed for r in results) / max(len(results), 1)
    return 0 if rate >= args.min_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
