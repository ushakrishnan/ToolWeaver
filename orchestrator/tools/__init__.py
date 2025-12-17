"""
Tools and Search subpackage.

Consolidates tool discovery, execution, filesystem management, and semantic search.
"""

from .tool_discovery import (
    ToolDiscoveryService,
    ToolDiscoveryOrchestrator,
    MCPToolDiscoverer,
    FunctionToolDiscoverer,
    CodeExecToolDiscoverer,
    DiscoveryMetrics,
    discover_tools,
)

from .tool_executor import call_tool

from .tool_filesystem import (
    ToolFileSystem,
    ToolInfo,
)

# Optional: Search tools (require numpy, sentence-transformers)
try:
    from .tool_search import ToolSearchEngine, search_tools
    from .tool_search_tool import tool_search_tool, initialize_tool_search, get_tool_search_definition
    from .vector_search import VectorToolSearchEngine
    _SEARCH_AVAILABLE = True
except ImportError:
    _SEARCH_AVAILABLE = False

from .sharded_catalog import ShardedCatalog

__all__ = [
    "ToolDiscoveryService", "ToolDiscoveryOrchestrator", "MCPToolDiscoverer",
    "FunctionToolDiscoverer", "CodeExecToolDiscoverer", "DiscoveryMetrics", "discover_tools",
    "call_tool", "ToolFileSystem", "ToolInfo", "ShardedCatalog",
]

if _SEARCH_AVAILABLE:
    __all__.extend(["ToolSearchEngine", "search_tools", "tool_search_tool", 
                    "initialize_tool_search", "get_tool_search_definition", "VectorToolSearchEngine"])
