import logging
import sys
from contextvars import ContextVar

import structlog

CONTEXT_FIELDS = ("correlation_id", "run_id", "video_id", "channel_id")
_ctx: ContextVar[dict | None] = ContextVar("dcs_log_ctx", default=None)


def bind_context(**values: str) -> None:
    unknown = set(values) - set(CONTEXT_FIELDS)
    if unknown:
        raise ValueError(f"unknown log context fields: {sorted(unknown)}")
    _ctx.set({**(_ctx.get() or {}), **values})


def clear_context() -> None:
    _ctx.set({})


def _add_context(_logger, _method, event_dict):
    current = _ctx.get() or {}
    for field in CONTEXT_FIELDS:
        event_dict.setdefault(field, current.get(field))
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _add_context,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level)),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=False,
    )
