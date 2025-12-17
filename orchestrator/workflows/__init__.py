"""
Workflows subpackage

Provides access to workflow-related modules and control-flow patterns
via a stable namespace without moving files yet.
"""

from orchestrator import control_flow_patterns as control_flow_patterns
from orchestrator import workflow as workflow
from orchestrator import workflow_library as workflow_library

__all__ = [
    "control_flow_patterns",
    "workflow",
    "workflow_library",
]
