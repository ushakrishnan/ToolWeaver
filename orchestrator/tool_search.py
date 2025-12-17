"""Shim module for backwards compatibility. Re-exports from orchestrator.tools."""
from .tools.tool_search import ToolSearchEngine, search_tools
__all__ = ["ToolSearchEngine", "search_tools"]
