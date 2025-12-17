"""
Shim module for backwards compatibility.

Re-exports code execution worker from orchestrator.execution.code_exec_worker.
"""

from .execution.code_exec_worker import (
    code_exec_worker,
    _exec_code,
)

__all__ = [
    "code_exec_worker",
    "_exec_code",
]
