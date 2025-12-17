"""Shim module for backwards compatibility. Re-exports from orchestrator.tools."""
from .tools.tool_executor import call_tool
__all__ = ["call_tool"]
