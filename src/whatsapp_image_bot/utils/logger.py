"""Centralized, color-aware logger for the project.

This module exposes :func:`get_logger`, a convenience wrapper around
Python's :pymod:`logging` facilities.  It standardizes formatting,
log-levels, and handler configuration across the code-base, so all you
need to do elsewhere is:

    from utils.logger import get_logger

    log = get_logger(__name__)
    log.info("Ready to roll!")

Features
--------
* **Single point of configuration** - called once on first import.
* **Rich, legible formatting** - timestamps, level, module, and message.
* **ANSI colours in the console** - INFO → green, WARNING → yellow,
  ERROR/CRITICAL → red; automatically disabled when output is redirected
  to a file or pipe.
* **Optional file handler** - just set the *LOG_FILE* environment
  variable or pass ``file_path=`` to :func:`get_logger`.
* **Thread-safe** - relies on the std-lib only; no extra dependencies.

Environment Variables
---------------------
``LOG_LEVEL``   Override the default minimum level (e.g. ``DEBUG``).
``LOG_FILE``    Write logs to this file in addition to the console.

"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Final

__all__ = ["get_logger"]

# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #

RESET: Final[str] = "\x1b[0m"
COLOR_MAP: Final[dict[int, str]] = {
    logging.DEBUG: "\x1b[38;5;244m",  # grey
    logging.INFO: "\x1b[38;5;82m",  # green
    logging.WARNING: "\x1b[38;5;226m",  # yellow
    logging.ERROR: "\x1b[38;5;196m",  # red
    logging.CRITICAL: "\x1b[1;38;5;196m",  # bold red
}

STANDARD_ATTRS: Final[set[str]] = {
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
    "asctime",
    "message",
}

# Explicitly approved context fields that will be rendered as key=value.
APPROVED_EXTRA_KEYS: Final[set[str]] = {
    "elapsed_ms",
    "sid",
    "url",
    "public_input_url",
    "errors",
}


class _ColorFormatter(logging.Formatter):
    """Colour formatter + hybrid extra rendering (approved + notice of others)."""

    # Base format – subclasses can tweak this string if needed.
    _FMT: Final[str] = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    _DATEFMT: Final[str] = "%Y-%m-%d %H:%M:%S"

    def __init__(self, use_color: bool = True) -> None:
        super().__init__(self._FMT, self._DATEFMT, style="%")
        self.use_color = use_color and sys.stderr.isatty()

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        # Preserve original levelname for other handlers
        original_level = record.levelname
        if self.use_color:
            colour = COLOR_MAP.get(record.levelno, "")
            record.levelname = f"{colour}{record.levelname}{RESET}"
        try:
            base = super().format(record)
        finally:
            record.levelname = original_level

        approved_parts: list[str] = []
        unexpected: list[str] = []

        for key, value in record.__dict__.items():
            if key in APPROVED_EXTRA_KEYS and value is not None:
                approved_parts.append(f"{key}={value}")
            elif (
                key not in STANDARD_ATTRS
                and key not in APPROVED_EXTRA_KEYS
                and not key.startswith("_")
            ):
                unexpected.append(key)

        if unexpected:
            approved_parts.append(f"extra_keys={','.join(sorted(unexpected))}")

        if approved_parts:
            base += " | " + " | ".join(approved_parts)

        return base


def _ensure_root_configured(
    level: int = logging.INFO,
    file_path: str | os.PathLike | None = None,
) -> None:
    """One-time configuration of the *root* logger.

    Parameters
    ----------
    level:
        Minimum severity that will be emitted.
    file_path:
        Optional file path. If provided, a plain file handler will be
        attached in addition to the coloured console handler.

    """
    root = logging.getLogger()
    if root.handlers:  # Already configured – do nothing.
        return

    root.setLevel(level)

    # Console / stderr handler
    console_handler = logging.StreamHandler(stream=sys.stderr)
    console_handler.setFormatter(_ColorFormatter())
    root.addHandler(console_handler)

    # File handler (optional)
    if file_path:
        # Make sure parent directories exist
        Path(file_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, encoding="utf-8", mode="a")
        file_handler.setFormatter(_ColorFormatter(use_color=False))
        root.addHandler(file_handler)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def get_logger(
    name: str | None = None,
    *,
    level: str | int | None = None,
    file_path: str | os.PathLike | None = None,
) -> logging.Logger:
    """Return a namespaced logger, configuring the root logger on first use.

    Parameters
    ----------
    name:
        Logger name.  If *None* (default), the root logger is returned.
    level:
        Minimum severity (e.g. ``"DEBUG"``, ``logging.INFO``).  Defaults to the
        value of the ``LOG_LEVEL`` environment variable, or ``INFO``.
    file_path:
        Path to a log file.  Overrides the ``LOG_FILE`` environment variable.

    Notes
    -----
    * Subsequent calls simply return ``logging.getLogger(name)``; expensive
      configuration happens only once per interpreter session.
    * Levels can be adjusted at runtime with
      ``get_logger().setLevel(logging.DEBUG)``, for example.

    Examples
    --------
    >>> from utils.logger import get_logger
    >>> log = get_logger(__name__, level="DEBUG")
    >>> log.debug("Everything wired up!")

    """
    # Read environment overrides only *once* (when module is first imported).
    default_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    default_level = getattr(logging, default_level_str, logging.INFO)

    # Convert string level to integer if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), default_level)
    elif level is None:
        level = default_level

    # Ensure level is an integer
    level_int: int = level if isinstance(level, int) else default_level

    _ensure_root_configured(
        level=level_int,
        file_path=file_path or os.getenv("LOG_FILE"),
    )

    return logging.getLogger(name)
