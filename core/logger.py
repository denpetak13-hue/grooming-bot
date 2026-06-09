import logging
import sys
from datetime import datetime
from pathlib import Path

import structlog

LOG_FORMAT = "%(message)s"
LOG_LEVEL = logging.DEBUG

# Prevent handler/processor failures from crashing the application.
logging.raiseExceptions = False

_processors = [
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.add_log_level,
    structlog.processors.StackInfoRenderer(),
    structlog.processors.JSONRenderer(),
]


def _create_stream_handler(stream) -> logging.Handler | None:
    if stream is None or getattr(stream, "closed", False):
        return None

    try:
        handler = logging.StreamHandler(stream)
        handler.setLevel(LOG_LEVEL)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        return handler
    except OSError:
        return None


def _build_handlers() -> tuple[list[logging.Handler], Path | None]:
    """Build stdout handler (required) and file handler (best-effort)."""
    handlers: list[logging.Handler] = []

    stdout_handler = _create_stream_handler(sys.stdout)
    if stdout_handler is not None:
        handlers.append(stdout_handler)
    else:
        stderr_handler = _create_stream_handler(sys.stderr)
        if stderr_handler is not None:
            handlers.append(stderr_handler)
            print(
                "WARNING: stdout unavailable; logging to stderr.",
                file=sys.stderr,
            )

    log_file: Path | None = None

    try:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"grooming_bot_{datetime.now().strftime('%Y-%m-%d')}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handlers.append(file_handler)
    except OSError as exc:
        print(
            f"WARNING: File logging unavailable ({exc}). Using stdout only.",
            file=sys.stderr,
        )

    if not handlers:
        handlers.append(logging.NullHandler())

    return handlers, log_file


def _configure_logging() -> Path | None:
    handlers, log_file = _build_handlers()

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(LOG_LEVEL)

    for handler in handlers:
        root_logger.addHandler(handler)

    structlog.configure(
        processors=_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(LOG_LEVEL),
        cache_logger_on_first_use=True,
    )

    return log_file


def _safe_log(method, *args, **kwargs) -> None:
    try:
        method(*args, **kwargs)
    except Exception:
        pass


_log_file = _configure_logging()
logger = structlog.get_logger()

_safe_log(
    logger.info,
    "Logging AKTIVIRAN",
    destinations=["stdout"] + (["file"] if _log_file else []),
)

if _log_file:
    _safe_log(
        logger.info,
        "Logovi se cuvaju u fajl",
        log_file=str(_log_file.resolve()),
    )
