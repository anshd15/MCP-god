"""Eval harness: run tasks end to end and grade them with deterministic checks.

A task file is JSONL, one task per line:

    {"id": "top-product", "task": "...", "approve": false,
     "checks": [{"type": "contains", "value": "trimmer"}, ...]}

Each task runs against a fresh copy of the workspace, so writes from one task
cannot leak into the next. Checks look at three things: the final answer,
the files left in the workspace, and the tool calls recorded in the trace.

Check types:
    contains / not_contains   case-insensitive substring of the answer
    regex                     re.search over the answer
    number                    a number within `tol` of `value` appears in the answer
    file_contains             workspace file `path` exists and contains `value`
    file_absent               workspace file `path` does not exist
    tool_called / tool_not_called   a tool span with that name (and decision=allow) exists
    judge                     an LLM grades the answer against `rubric` (for open-ended answers)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .guardrails import Budget
from .hub import HubTool
from .llm import LLM, ClaudeLLM, text_of
from .orchestrator import RunResult, run_task

NUM_RE = re.compile(r"-?\d[\d,]*\.?\d*")


@dataclass
class CheckResult:
    check: dict[str, Any]
    passed: bool
    detail: str = ""


@dataclass
class TaskResult:
    id: str
    passed: bool
    checks: list[CheckResult]
    cost_usd: float
    seconds: float
    tool_calls: int
    answer: str
    trace_file: str
    errors: list[str] = field(default_factory=list)


def load_tasks(path: str | Path) -> list[dict[str, Any]]:
    lines = Path(path).read_text("utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip() and not line.lstrip().startswith("//")]


def _called_tools(trace_file: Path) -> set[str]:
    called = set()
    for line in trace_file.read_text("utf-8").splitlines():
        span = json.loads(line)
        attrs = span["attributes"]
        if span["name"] == "tool.call" and attrs.get("decision") == "allow":
            called.add(attrs["tool"])
    return called


JUDGE_MODEL = "claude-sonnet-5-5"
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"reason": {"type": "string"}, "pass": {"type": "boolean"}},
    "required": ["reason", "pass"],
    "additionalProperties": False,
}
JUDGE_SYSTEM = """You grade an AI agent's answer against a rubric. Pass only if every rubric point is met.
Judge the answer as written; do not reward effort or penalize style. Give a one-sentence reason, then the verdict."""


async def judge(check: dict[str, Any], task: str, answer: str, llm: LLM) -> CheckResult:
    msg = await llm.create(
        max_tokens=2000,
        system=JUDGE_SYSTEM,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": JUDGE_SCHEMA}},
        messages=[{"role": "user", "content": f"Task: {task}

Rubric: {check['rubric']}

Answer:
{answer}"}],
    )
    verdict = json.loads(text_of(msg))
    return CheckResult(check, bool(verdict["pass"]), verdict["reason"])


def grade(check: dict[str, Any], answer: str, workspace: Path, trace_file: Path) -> CheckResult:
    kind, value = check["type"], check.get("value")
    low = answer.lower()
    if kind == "contains":
        return CheckResult(check, str(value).lower() in low)
    if kind == "not_contains":
        return CheckResult(check, str(value).lower() not in low)
    if kind == "regex":
        return CheckResult(check, re.search(value, answer, re.IGNORECASE | re.MULTILINE) is not None)
    if kind == "number":
        tol = check.get("tol", 0.01)
        nums = [float(n.replace(",", "")) for n in NUM_RE.findall(answer) if n.strip(",.")]
        hit = any(abs(n - float(value)) <= tol for n in nums)
        return CheckResult(check, hit, "" if hit else f"numbers seen: {nums[:10]}")
    if kind in ("file_contains", "file_absent"):
        f = workspace / check["path"]
        if kind == "file_absent":
            return CheckResult(check, not f.exists())
        ok = f.is_file() and str(value).lower() in f.read_text("utf-8", errors="replace").lower()
        return CheckResult(check, ok, "" if ok else ("missing file" if not f.exists() else "value not in file"))
    if kind in ("tool_called", "tool_not_called"):
        called = _called_tools(trace_file)
        hit = value in called
        return CheckResult(check, hit if kind == "tool_called" else not hit, f"called: {sorted(called)}")
    raise ValueError(f"unknown check type {kind!r}")


async def _approve(tool: HubTool, args: dict[str, Any]) -> bool:
    return True


async def _deny(tool: HubTool, args: dict[str, Any]) -> bool:
    return False


async def run_eval(
    tasks: list[dict[str, Any]],
    config: str | Path = "servers.json",
    workspace: str | Path = "workspace",
    llm: LLM | None = None,
    judge_llm: LLM | None = None,
    trace_dir: str | Path = "traces/eval",
    max_cost_usd: float = 1.0,
) -> list[TaskResult]:
    results = []
    for spec in tasks:
        with tempfile.TemporaryDirectory(prefix=f"eval-{spec['id']}-") as tmp:
            ws = Path(tmp) / "workspace"
            shutil.copytree(workspace, ws)
            old_root = os.environ.get("MCP_FS_ROOT")
            os.environ["MCP_FS_ROOT"] = str(ws)  # servers inherit the agent's environment
            started = time.perf_counter()
            try:
                run: RunResult = await run_task(
                    spec["task"],
                    config=config,
                    llm=llm,
                    approver=_approve if spec.get("approve") else _deny,
                    budget=Budget(max_cost_usd=spec.get("max_cost_usd", max_cost_usd)),
                    trace_dir=trace_dir,
                )
            finally:
                if old_root is None:
                    os.environ.pop("MCP_FS_ROOT", None)
                else:
                    os.environ["MCP_FS_ROOT"] = old_root
            seconds = time.perf_counter() - started
            checks = []
            for c in spec["checks"]:
                if c["type"] == "judge":
                    judge_llm = judge_llm or ClaudeLLM(model=JUDGE_MODEL)
                    checks.append(await judge(c, spec["task"], run.answer, judge_llm))
                else:
                    checks.append(grade(c, run.answer, ws, run.trace_file))
        results.append(TaskResult(
            id=spec["id"],
            passed=all(c.passed for c in checks) and not run.errors,
            checks=checks,
            cost_usd=run.budget.cost_usd,
            seconds=seconds,
            tool_calls=run.budget.tool_calls,
            answer=run.answer,
            trace_file=str(run.trace_file),
            errors=run.errors,
        ))
    return results


def report(results: list[TaskResult]) -> str:
    rows = ["| task | result | tool calls | cost | time | failed checks |", "|---|---|---|---|---|---|"]
    for r in results:
        failed = "; ".join(f"{c.check['type']}={c.check.get('value', c.check.get('path'))} {c.detail}".strip()
                           for c in r.checks if not c.passed) or ("; ".join(r.errors) if r.errors else "")
        rows.append(f"| {r.id} | {'PASS' if r.passed else 'FAIL'} | {r.tool_calls} | ${r.cost_usd:.4f} "
                    f"| {r.seconds:.1f}s | {failed} |")
    n = len(results)
    passed = sum(r.passed for r in results)
    total_cost = sum(r.cost_usd for r in results)
    rows.append(f"\n**{passed}/{n} passed ({passed / n:.0%})**, total ${total_cost:.4f}" if n else "\nno tasks")
    return "\n".join(rows)


def save(results: list[TaskResult], out_dir: str | Path = "evals/results") -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{time.strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps([asdict(r) for r in results], indent=2), "utf-8")
    return path
