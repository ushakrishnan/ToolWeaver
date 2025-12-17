"""
Shim module for backwards compatibility.

Re-exports programmatic executor from orchestrator.execution.programmatic_executor.
"""

from .execution.programmatic_executor import (
    ProgrammaticToolExecutor,
    SecurityError,
    execute_programmatic_code,
)

__all__ = [
    "ProgrammaticToolExecutor",
    "SecurityError",
    "execute_programmatic_code",
]
