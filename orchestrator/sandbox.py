"""
Shim module for backwards compatibility.

Re-exports sandbox from orchestrator.execution.sandbox.
"""

from .execution.sandbox import (
    SandboxEnvironment,
    ResourceLimits,
    ExecutionResult,
    SandboxSecurityError,
    create_sandbox,
)

__all__ = [
    "SandboxEnvironment",
    "ResourceLimits",
    "ExecutionResult",
    "SandboxSecurityError",
    "create_sandbox",
]
