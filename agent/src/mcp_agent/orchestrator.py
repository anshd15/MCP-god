"""Run loop: plan -> execute steps -> replan once per failure -> synthesize."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path

from opentelemetry.trace import Status, StatusCode

from .agents import Executor, Planner, StepResult, synthesize
from .guardrails import Approver, Budget, BudgetExceeded, Policy, deny_all
from .hub import MCPHub, load_config
from .llm import LLM, ClaudeLLM
from .tracing import setup_tracing, tracer


@dataclass
class RunResult:
    run_id: str
    answer: str
    steps: list[StepResult]
    trace_file: Path
    budget: Budget
    errors: list[str] = field(default_factory=list)


async def run_task(
    task: str,
    config: str | Path = "servers.json",
    llm: LLM | None = None,
    approver: Approver = deny_all,
    budget: Budget | None = None,
    max_replans: int = 2,
    trace_dir: str | Path = "traces",
) -> RunResult:
    run_id = uuid.uuid4().hex[:12]
    trace_file = Path(trace_dir) / f"{run_id}.jsonl"
    provider = setup_tracing(trace_file)
    t = tracer(provider)
    llm = llm or ClaudeLLM()
    budget = budget or Budget()
    specs, policy_cfg = load_config(config)
    policy = Policy.from_config(policy_cfg)
    results: list[StepResult] = []
    errors: list[str] = []
    answer = ""

    try:
        with t.start_as_current_span("run") as root:
            root.set_attributes({"run.id": run_id, "task": task})
            async with MCPHub(specs) as hub:
                planner = Planner(llm, hub, t, budget)
                executor = Executor(llm, hub, t, budget, policy, approver)
                try:
                    plan = await planner.plan(task)
                    i, replans = 0, 0
                    while i < len(plan):
                        budget.charge_step()
                        with t.start_as_current_span("step") as span:
                            span.set_attribute("step.goal", plan[i].goal)
                            res = await executor.run_step(task, plan, i, results)
                            if not res.ok:
                                span.set_status(Status(StatusCode.ERROR, res.text[:200]))
                        if res.ok:
                            results.append(res)
                            i += 1
                            continue
                        if replans >= max_replans:
                            results.append(res)
                            break
                        replans += 1
                        plan = results_plan(results) + await planner.replan(task, results, res)
                        i = len(results)
                except BudgetExceeded as e:
                    errors.append(str(e))
                    root.set_status(Status(StatusCode.ERROR, str(e)))
                if not results:
                    answer = "Nothing was completed."
                elif errors:
                    # Budget is spent; report raw step results instead of paying for synthesis.
                    answer = "\n".join(f"- {r.step.goal}: {r.text}" for r in results)
                else:
                    answer = await synthesize(llm, t, budget, task, results)
                if errors:
                    answer += f"\n\n(Stopped early: {'; '.join(errors)})"
            root.set_attributes({
                "budget.tokens": budget.tokens, "budget.tool_calls": budget.tool_calls,
                "cost.usd": round(budget.cost_usd, 6),
            })
    finally:
        provider.shutdown()

    return RunResult(run_id, answer, results, trace_file, budget, errors)


def results_plan(results: list[StepResult]) -> list:
    return [r.step for r in results]
