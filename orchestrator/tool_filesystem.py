"""Shim module for backwards compatibility. Re-exports from orchestrator.tools."""
from .tools.tool_filesystem import ToolFileSystem, ToolInfo
__all__ = ["ToolFileSystem", "ToolInfo"]
