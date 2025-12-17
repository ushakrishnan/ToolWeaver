"""Shim module for backwards compatibility.

Tries to import from orchestrator.tools; falls back to stub if dependencies missing.
"""
import logging
logger = logging.getLogger(__name__)

try:
    from .tools.tool_search_tool import (
        tool_search_tool,
        initialize_tool_search,
        get_tool_search_definition,
    )
    __all__ = ["tool_search_tool", "initialize_tool_search", "get_tool_search_definition"]
except Exception as e:
    logger.warning(f"Falling back to stub tool_search_tool due to import error: {e}")
    from typing import Dict, Any, Optional
    from .models import ToolCatalog, ToolDefinition, ToolParameter, ToolExample

    _full_catalog: Optional[ToolCatalog] = None

    def initialize_tool_search(catalog: ToolCatalog):
        global _full_catalog
        _full_catalog = catalog
        logger.info(f"Stub tool search initialized with {len(catalog.tools)} tools")

    def tool_search_tool(query: str, top_k: int = 5) -> Dict[str, Any]:
        if _full_catalog is None:
            return {
                "tools": [],
                "query": query,
                "total_available": 0,
                "error": "Tool search engine not initialized",
            }
        # Simple stub: return first top_k tools
        all_tools = list(_full_catalog.tools.values())
        results = []
        for tool in all_tools[:top_k]:
            tool_dict = tool.to_llm_format(include_examples=False)
            tool_dict["relevance_score"] = 1.0
            results.append(tool_dict)
        return {
            "tools": results,
            "query": query,
            "total_available": len(all_tools),
            "returned": len(results),
        }

    def get_tool_search_definition() -> ToolDefinition:
        return ToolDefinition(
            name="tool_search_tool",
            type="function",
            description=(
                "Search for tools by capability description (stub). Returns first top_k tools."
            ),
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="Natural language description of what you want to do",
                    required=True,
                ),
                ToolParameter(
                    name="top_k",
                    type="integer",
                    description="Number of relevant tools to return (default: 5, max: 20)",
                    required=False,
                    default=5,
                ),
            ],
            returns={
                "type": "object",
                "properties": {
                    "tools": {"type": "array", "description": "List of matching tool definitions"},
                    "query": {"type": "string"},
                    "total_available": {"type": "integer"},
                    "returned": {"type": "integer"},
                },
            },
            source="built-in",
            version="1.0",
            defer_loading=False,
            examples=[],
            metadata={"always_available": True, "category": "tool_discovery", "phase": 6},
        )

    __all__ = ["tool_search_tool", "initialize_tool_search", "get_tool_search_definition"]
