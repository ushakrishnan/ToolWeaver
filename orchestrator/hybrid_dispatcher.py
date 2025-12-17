"""Shim module. Re-exports from orchestrator.dispatch.hybrid_dispatcher."""
from .dispatch.hybrid_dispatcher import register_function, get_registered_functions, dispatch_step, function_call_worker
__all__ = ["register_function", "get_registered_functions", "dispatch_step", "function_call_worker"]
