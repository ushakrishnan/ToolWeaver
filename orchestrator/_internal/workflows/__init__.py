"""
Workflows subpackage

Workflow-related modules and control-flow patterns under a stable namespace.
"""

from .control_flow_patterns import (
    ControlFlowPatterns,
    PatternType,
    create_polling_code,
    create_parallel_code,
    create_conditional_code,
    create_retry_code,
)
from .workflow import (
    WorkflowTemplate,
    WorkflowStep,
    WorkflowExecutor,
    WorkflowContext,
    StepStatus,
)
from .workflow_library import (
    WorkflowLibrary,
    PatternDetector,
    ToolSequence,
)

__all__ = [
    # control flow
    "ControlFlowPatterns",
    "PatternType",
    "create_polling_code",
    "create_parallel_code",
    "create_conditional_code",
    "create_retry_code",
    # workflow core
    "WorkflowTemplate",
    "WorkflowStep",
    "WorkflowExecutor",
    "WorkflowContext",
    "StepStatus",
    # workflow library
    "WorkflowLibrary",
    "PatternDetector",
    "ToolSequence",
]
