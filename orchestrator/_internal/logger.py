"""
Structured logging for ToolWeaver.

Phase 0.l: Built-in logging using standard Python logging module.
No external dependencies. Configurable via environment variables.

Usage:
    from orchestrator._internal.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("Tool registered", extra={"tool_name": "get_balance", "domain": "finance"})
    logger.error("Tool execution failed", extra={"tool_name": "process_data", "error": str(e)})

Configuration:
    Environment variable: TOOLWEAVER_LOG_LEVEL
    Values: DEBUG, INFO, WARNING, ERROR, CRITICAL
    Default: INFO

Output format:
    [2025-12-19 10:45:23] INFO [orchestrator.tools.registry] Tool registered: get_balance
"""

import logging
import os
import sys
from typing import Any, Optional


# ============================================================
# Configuration
# ============================================================

DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "[%(asctime)s] %(levelname)s [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _get_log_level_from_env() -> int:
    """
    Get log level from environment variable.
    
    Returns:
        Log level as int (logging.INFO, logging.DEBUG, etc.)
    """
    level_str = os.getenv("TOOLWEAVER_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    return level_map.get(level_str, logging.INFO)


# ============================================================
# Logger Setup
# ============================================================

_initialized = False
_root_logger: Optional[logging.Logger] = None


def _initialize_logging() -> None:
    """
    Initialize the logging system once.
    
    Sets up:
    - Console handler with structured format
    - Log level from environment
    - Timestamps in logs
    """
    global _initialized, _root_logger
    
    if _initialized:
        return
    
    # Get or create root logger for ToolWeaver
    _root_logger = logging.getLogger("orchestrator")
    _root_logger.setLevel(_get_log_level_from_env())
    
    # Remove existing handlers (avoid duplicates)
    _root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(_get_log_level_from_env())
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    _root_logger.addHandler(console_handler)
    
    # Don't propagate to root logger (avoid duplicate logs)
    _root_logger.propagate = False
    
    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Logger instance configured for ToolWeaver
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting tool discovery")
        [2025-12-19 10:45:23] INFO [orchestrator.tools.discovery] Starting tool discovery
        
        >>> logger.debug("Found tool", extra={"tool_name": "get_balance"})
        [2025-12-19 10:45:23] DEBUG [orchestrator.tools.discovery] Found tool
    """
    _initialize_logging()
    
    # Ensure logger name starts with "orchestrator"
    if not name.startswith("orchestrator"):
        name = f"orchestrator.{name}"
    
    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    """
    Dynamically change log level at runtime.
    
    Args:
        level: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Example:
        >>> set_log_level("DEBUG")  # Enable debug logging
        >>> set_log_level("ERROR")  # Only show errors
    """
    _initialize_logging()
    
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    log_level = level_map.get(level.upper(), logging.INFO)
    
    if _root_logger:
        _root_logger.setLevel(log_level)
        for handler in _root_logger.handlers:
            handler.setLevel(log_level)


def disable_logging() -> None:
    """
    Disable all logging output.
    
    Useful for tests that don't want log output.
    
    Example:
        >>> disable_logging()  # Silence all logs
    """
    _initialize_logging()
    if _root_logger:
        _root_logger.setLevel(logging.CRITICAL + 1)


def enable_debug_mode() -> None:
    """
    Enable debug-level logging for troubleshooting.
    
    Equivalent to setting TOOLWEAVER_LOG_LEVEL=DEBUG
    
    Example:
        >>> enable_debug_mode()
        >>> logger = get_logger(__name__)
        >>> logger.debug("This will now show up")
    """
    set_log_level("DEBUG")


# ============================================================
# Structured Logging Helpers
# ============================================================

class StructuredLogger:
    """
    Wrapper around logging.Logger for structured logging.
    
    Provides convenience methods for logging with context.
    """
    
    def __init__(self, logger: logging.Logger):
        self._logger = logger
    
    def info(self, message: str, **context: Any) -> None:
        """Log info with structured context."""
        self._logger.info(message, extra=context)
    
    def debug(self, message: str, **context: Any) -> None:
        """Log debug with structured context."""
        self._logger.debug(message, extra=context)
    
    def warning(self, message: str, **context: Any) -> None:
        """Log warning with structured context."""
        self._logger.warning(message, extra=context)
    
    def error(self, message: str, **context: Any) -> None:
        """Log error with structured context."""
        self._logger.error(message, extra=context)
    
    def critical(self, message: str, **context: Any) -> None:
        """Log critical with structured context."""
        self._logger.critical(message, extra=context)
    
    def exception(self, message: str, **context: Any) -> None:
        """Log exception with traceback."""
        self._logger.exception(message, extra=context)


def get_structured_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        StructuredLogger instance
        
    Example:
        >>> logger = get_structured_logger(__name__)
        >>> logger.info("Tool registered", tool_name="get_balance", domain="finance")
        [2025-12-19 10:45:23] INFO [orchestrator.tools.registry] Tool registered
    """
    return StructuredLogger(get_logger(name))


# ============================================================
# Export
# ============================================================

__all__ = [
    "get_logger",
    "get_structured_logger",
    "set_log_level",
    "disable_logging",
    "enable_debug_mode",
]
