"""
Tools & Discovery subpackage

Aggregates tool discovery and tool search modules under a single namespace
without moving files yet.
"""

from orchestrator import tool_discovery as tool_discovery
from orchestrator import tool_search as tool_search
from orchestrator import tool_search_tool as tool_search_tool
from orchestrator import mcp_client as mcp_client
from orchestrator import functions as functions

__all__ = [
    "tool_discovery",
    "tool_search",
    "tool_search_tool",
    "mcp_client",
    "functions",
]
