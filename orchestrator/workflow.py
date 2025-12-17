"""
Shim module for backwards compatibility.

Re-exports workflow classes from orchestrator.workflows.workflow.
"""

from .workflows.workflow import (
    WorkflowTemplate,
    WorkflowStep,
    WorkflowExecutor,
    WorkflowContext,
    StepStatus,
)

__all__ = [
    "WorkflowTemplate",
    "WorkflowStep",
    "WorkflowExecutor",
    "WorkflowContext",
    "StepStatus",
]
