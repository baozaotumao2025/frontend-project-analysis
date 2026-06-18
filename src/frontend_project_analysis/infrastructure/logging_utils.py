"""Logging bootstrap helpers."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler

from ..core.config import AppPaths, Settings, ensure_state_dirs

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class CallContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = trace_id_var.get()
        record.request_id = request_id_var.get()
        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", trace_id_var.get()),
            "request_id": getattr(record, "request_id", request_id_var.get()),
        }
        extra_fields = self._collect_extra_fields(record)
        if extra_fields:
            payload["fields"] = extra_fields
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)

    @staticmethod
    def _collect_extra_fields(record: logging.LogRecord) -> dict[str, object]:
        reserved = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
            "asctime",
            "trace_id",
            "request_id",
        }
        extra_fields: dict[str, object] = {}
        for key, value in record.__dict__.items():
            if key in reserved or key.startswith("_"):
                continue
            try:
                json.dumps(value, ensure_ascii=True)
                extra_fields[key] = value
            except TypeError:
                extra_fields[key] = repr(value)
        return extra_fields


def configure_logging(settings: Settings, paths: AppPaths) -> None:
    root_logger = logging.getLogger()
    if getattr(root_logger, "_fpa_configured", False):
        return

    ensure_state_dirs(paths)
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    formatter: logging.Formatter
    if settings.log_json:
        formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter(
            fmt=(
                "%(asctime)s %(levelname)s [%(name)s] "
                "[trace=%(trace_id)s request=%(request_id)s] %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    call_filter = CallContextFilter()

    handlers: list[logging.Handler] = []
    file_handler = RotatingFileHandler(
        paths.log_dir / settings.log_file_name,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(call_filter)
    handlers.append(file_handler)

    if settings.log_to_stderr:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(call_filter)
        handlers.append(stream_handler)

    for handler in handlers:
        root_logger.addHandler(handler)

    root_logger._fpa_configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


@contextmanager
def call_context(trace_id: str | None = None, request_id: str | None = None) -> Iterator[None]:
    trace_token = trace_id_var.set(trace_id or trace_id_var.get())
    request_token = request_id_var.set(request_id or request_id_var.get())
    try:
        yield
    finally:
        trace_id_var.reset(trace_token)
        request_id_var.reset(request_token)
