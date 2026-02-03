"""Logging configuration for Ableton MCP Server.

Provides JSON-formatted structured logging with file output by default.
Configuration can be customized via environment variables:
    - ABLETON_MCP_LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - ABLETON_MCP_LOG_FILE: Log file path (default: ableton_mcp.log)
    - ABLETON_MCP_LOG_TO_CONSOLE: Also log to console (true/false, default: false)
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import structlog

# Default configuration
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FILE = "ableton_mcp.log"
DEFAULT_LOG_TO_CONSOLE = False
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5


def get_log_level() -> int:
    """Get log level from environment or default."""
    level_name = os.environ.get("ABLETON_MCP_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    return getattr(logging, level_name, logging.INFO)


def get_log_file() -> Path:
    """Get log file path from environment or default."""
    log_file = os.environ.get("ABLETON_MCP_LOG_FILE", DEFAULT_LOG_FILE)
    return Path(log_file)


def should_log_to_console() -> bool:
    """Check if console logging is enabled."""
    value = os.environ.get("ABLETON_MCP_LOG_TO_CONSOLE", str(DEFAULT_LOG_TO_CONSOLE))
    return value.lower() in ("true", "1", "yes")


class JSONFileHandler(RotatingFileHandler):
    """Rotating file handler for JSON log output."""

    def __init__(
        self,
        filename: str,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT,
    ) -> None:
        # Ensure parent directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        super().__init__(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )


def setup_logging(
    log_level: Optional[int] = None,
    log_file: Optional[Path] = None,
    log_to_console: Optional[bool] = None,
) -> None:
    """Configure structured logging with JSON output to file.

    Args:
        log_level: Override log level (default: from env or INFO)
        log_file: Override log file path (default: from env or ableton_mcp.log)
        log_to_console: Override console logging (default: from env or False)
    """
    # Resolve configuration
    level = log_level if log_level is not None else get_log_level()
    file_path = log_file if log_file is not None else get_log_file()
    console_enabled = log_to_console if log_to_console is not None else should_log_to_console()

    # Create handlers
    handlers: list[logging.Handler] = []

    # File handler (always enabled) - outputs JSON
    file_handler = JSONFileHandler(str(file_path))
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    handlers.append(file_handler)

    # Console handler (optional) - outputs JSON for consistency
    if console_enabled:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(console_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add new handlers
    for handler in handlers:
        root_logger.addHandler(handler)

    # Configure structlog for JSON output
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
