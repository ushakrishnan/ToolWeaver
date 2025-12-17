"""
Shim module for backwards compatibility.

Re-exports control-flow patterns from orchestrator.workflows.control_flow_patterns.
"""

from .workflows.control_flow_patterns import (
    ControlFlowPattern,
    ControlFlowPatterns,
    PatternType,
    create_polling_code,
    create_parallel_code,
    create_conditional_code,
    create_retry_code,
)

__all__ = [
    "ControlFlowPattern",
    "ControlFlowPatterns",
    "PatternType",
    "create_polling_code",
    "create_parallel_code",
    "create_conditional_code",
    "create_retry_code",
]
