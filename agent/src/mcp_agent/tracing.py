"""OpenTelemetry tracing: run -> plan -> step -> llm / tool spans.

Spans always go to traces/<run_id>.jsonl (one JSON object per span). Set
OTEL_EXPORTER_OTLP_ENDPOINT to also ship them to Jaeger, Langfuse, or any
OTLP backend.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from pathlib import Path

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, SpanExporter, SpanExportResult

TRACER_NAME = "mcp_agent"


class JsonlSpanExporter(SpanExporter):
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        with self.path.open("a", encoding="utf-8") as f:
            for s in spans:
                ctx = s.get_span_context()
                f.write(json.dumps({
                    "name": s.name,
                    "trace_id": f"{ctx.trace_id:032x}",
                    "span_id": f"{ctx.span_id:016x}",
                    "parent_id": f"{s.parent.span_id:016x}" if s.parent else None,
                    "start_ns": s.start_time,
                    "end_ns": s.end_time,
                    "status": s.status.status_code.name,
                    "attributes": dict(s.attributes or {}),
                    "events": [{"name": e.name, "attributes": dict(e.attributes or {})} for e in s.events],
                }, default=str) + "\n")
        return SpanExportResult.SUCCESS


def setup_tracing(trace_file: Path) -> TracerProvider:
    provider = TracerProvider(resource=Resource.create({"service.name": "mcp-agent"}))
    provider.add_span_processor(SimpleSpanProcessor(JsonlSpanExporter(trace_file)))
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    return provider


def tracer(provider: TracerProvider) -> trace.Tracer:
    return provider.get_tracer(TRACER_NAME)


def render_tree(trace_file: Path) -> str:
    """Pretty-print a JSONL trace as an indented tree with durations."""
    spans = [json.loads(line) for line in trace_file.read_text("utf-8").splitlines() if line.strip()]
    children: dict[str | None, list[dict]] = {}
    for s in spans:
        children.setdefault(s["parent_id"], []).append(s)
    ids = {s["span_id"] for s in spans}
    lines: list[str] = []

    def walk(span: dict, depth: int) -> None:
        ms = (span["end_ns"] - span["start_ns"]) / 1e6
        keys = ("tool", "decision", "tokens.in", "tokens.out", "tokens.cache_read", "injection.hits", "error", "step.goal")
        attrs = {k: v for k, v in span["attributes"].items() if k in keys}
        mark = "x" if span["status"] == "ERROR" else "-"
        lines.append(f"{'  ' * depth}{mark} {span['name']} {ms:.0f}ms {attrs if attrs else ''}".rstrip())
        for c in sorted(children.get(span["span_id"], []), key=lambda c: c["start_ns"]):
            walk(c, depth + 1)

    for root in sorted((s for s in spans if s["parent_id"] not in ids), key=lambda s: s["start_ns"]):
        walk(root, 0)
    return "\n".join(lines)
