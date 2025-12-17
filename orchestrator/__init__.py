"""
Orchestrator module for hybrid execution plans with two-model architecture.

Architecture:
- Large Model Planner (GPT-4o, Claude) for generating execution plans
- Small Model Workers (Phi-3, Llama) for efficient task execution
- Hybrid Dispatcher supporting MCP workers, function calls, and code execution
"""

from .models import *
from .runtime.orchestrator import execute_plan, final_synthesis
from .infra.mcp_client import MCPClientShim
from .dispatch.workers import *
from .execution.code_exec_worker import code_exec_worker
from .dispatch.hybrid_dispatcher import dispatch_step, register_function, get_registered_functions
from . import functions  # Import to register functions

# Optional imports (only if packages installed)
try:
    from .planning.planner import LargePlanner
    _PLANNER_AVAILABLE = True
except ImportError:
    _PLANNER_AVAILABLE = False

try:
    from .execution.small_model_worker import SmallModelWorker
    _SMALL_MODEL_AVAILABLE = True
except ImportError:
    _SMALL_MODEL_AVAILABLE = False

__all__ = [
    # Core orchestration
    'execute_plan',
    'final_synthesis',
    'MCPClientShim',
    'dispatch_step',
    'register_function',
    'get_registered_functions',
    'code_exec_worker',
    # Two-model architecture (optional)
    'LargePlanner' if _PLANNER_AVAILABLE else None,
    'SmallModelWorker' if _SMALL_MODEL_AVAILABLE else None,
]

# Remove None values from __all__
__all__ = [x for x in __all__ if x is not None]
