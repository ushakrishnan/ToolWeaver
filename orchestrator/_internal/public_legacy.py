"""
Public legacy shims loaded from internal to keep orchestrator/__init__.py clean.

This module re-exports existing legacy surfaces so examples/tests continue
to work while the new package-first API solidifies. Do not import this
module directly from user code; import from `orchestrator` instead.
"""

try:
    from ..shared.models import *  # noqa: F401, F403
except Exception:  # noqa: BLE001
    pass

try:
    from .runtime.orchestrator import execute_plan, final_synthesis, Orchestrator  # noqa: F401
except Exception:  # noqa: BLE001
    pass

try:
    from .infra.mcp_client import MCPClientShim  # noqa: F401
except Exception:  # noqa: BLE001
    pass

try:
    from .dispatch.workers import *  # noqa: F401, F403
except Exception:  # noqa: BLE001
    pass

try:
    from .execution.code_exec_worker import code_exec_worker  # noqa: F401
except Exception:  # noqa: BLE001
    pass

try:
    from .dispatch.hybrid_dispatcher import (
        dispatch_step,
        register_function,
        get_registered_functions,
    )  # noqa: F401
except Exception:  # noqa: BLE001
    pass

__all__ = [
    # Intentionally left broad for legacy examples; avoid relying on this list.
]
