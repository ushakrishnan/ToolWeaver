"""
Shim module for backwards compatibility.

Re-exports workflow library from orchestrator.workflows.workflow_library.
"""

from .workflows.workflow_library import (
    WorkflowLibrary,
    PatternDetector,
    ToolSequence,
)

__all__ = [
    "WorkflowLibrary",
    "PatternDetector",
    "ToolSequence",
]
