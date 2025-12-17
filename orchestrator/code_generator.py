"""
Shim module for backwards compatibility.

Re-exports code generator from orchestrator.execution.code_generator.
"""

from .execution.code_generator import (
    StubGenerator,
    GeneratedStub,
)

__all__ = [
    "StubGenerator",
    "GeneratedStub",
]
