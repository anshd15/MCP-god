"""Structured JSON logs that carry the current trace and span ids."""

from __future__ import annotations

import json
import logging
import sys

from opentelemetry import trace


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ctx = trace.get_current_span().get_span_context()
        entry = {"ts": self.formatTime(record), "level": record.levelname, "logger": record.name, "msg": record.getMessage()}
        if ctx.is_valid:
            entry |= {"trace_id": f"{ctx.trace_id:032x}", "span_id": f"{ctx.span_id:016x}"}
        entry |= getattr(record, "fields", {})
        return json.dumps(entry, default=str)


def setup_logging(level: str = "INFO") -> logging.Logger:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    log = logging.getLogger("mcp_agent")
    log.handlers[:] = [handler]
    log.setLevel(level)
    return log
