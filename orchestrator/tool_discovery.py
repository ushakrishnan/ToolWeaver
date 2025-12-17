"""Shim module for backwards compatibility. Re-exports from orchestrator.tools."""
from .tools.tool_discovery import (
    ToolDiscoveryService,
    ToolDiscoveryOrchestrator,
    MCPToolDiscoverer,
    FunctionToolDiscoverer,
    CodeExecToolDiscoverer,
    DiscoveryMetrics,
    discover_tools,
)
__all__ = [
    "ToolDiscoveryService", "ToolDiscoveryOrchestrator", "MCPToolDiscoverer",
    "FunctionToolDiscoverer", "CodeExecToolDiscoverer", "DiscoveryMetrics", "discover_tools",
]
