"""
Tool Search Tool - Phase 6 Implementation

Enables LLMs to dynamically search for and discover tools during conversation.
Implements Anthropic's Tool Search Tool pattern for efficient tool discovery.

Reference: https://www.anthropic.com/engineering/advanced-tool-use
"""

import logging
from typing import Dict, Any, List, Optional
from ..shared.models import ToolCatalog, ToolDefinition
from .tool_search import ToolSearchEngine

logger = logging.getLogger(__name__)

# Global search engine instance (lazy-initialized)
_search_engine: Optional[ToolSearchEngine] = None
_full_catalog: Optional[ToolCatalog] = None

def initialize_tool_search(catalog: ToolCatalog):
    """
    Initialize the tool search engine with the full tool catalog.
    
    Args:
        catalog: Complete tool catalog with all available tools
    """
    global _search_engine, _full_catalog
    if _search_engine is None:
        try:
            _search_engine = ToolSearchEngine()
            _full_catalog = catalog
            logger.info(f"Tool search initialized with {len(catalog.tools)} tools")
        except Exception as e:
            logger.error(f"Failed to initialize tool search: {e}")
            _search_engine = None
            _full_catalog = None

def tool_search_tool(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Search for tools by capability description.
    
    This tool allows the LLM to dynamically discover tools that aren't 
    currently loaded in context. Use this when you need a tool but don't 
    see it in your available tools.
    
    Args:
        query: Natural language description of what you want to do.
               Examples: "create a pull request on github", "send slack message",
               "parse JSON data", "categorize expenses"
        top_k: Number of relevant tools to return (default: 5)
    
    Returns:
        Dictionary with:
        - tools: List of tool definitions that match the query
        - query: The search query used
        - total_available: Total number of tools in catalog
    
    Examples:
        1. Search for GitHub tools:
           Input: {"query": "create pull request", "top_k": 3}
           Output: {"tools": [github.createPR, github.listIssues, ...]}
        
        2. Search for communication tools:
           Input: {"query": "send message to team", "top_k": 5}
           Output: {"tools": [slack.sendMessage, teams.postMessage, ...]}
        
        3. Search for data processing:
           Input: {"query": "parse and transform data", "top_k": 3}
           Output: {"tools": [parse_json, transform_data, ...]}
    """
    if _search_engine is None or _full_catalog is None:
        logger.warning("Tool search not initialized, returning empty results")
        return {
            "tools": [],
            "query": query,
            "total_available": 0,
            "error": "Tool search engine not initialized"
        }
    
    try:
        # Search for relevant tools
        results = _search_engine.search(query, _full_catalog, top_k=top_k)
        
        # Convert to LLM format
        tools = []
        for tool_def, score in results:
            tool_dict = tool_def.to_llm_format(include_examples=True)
            tool_dict["relevance_score"] = round(score, 3)
            tools.append(tool_dict)
        
        logger.info(f"Tool search for '{query}' returned {len(tools)} tools")
        
        return {
            "tools": tools,
            "query": query,
            "total_available": len(_full_catalog.tools),
            "returned": len(tools)
        }
    
    except Exception as e:
        logger.error(f"Tool search failed: {e}")
        return {
            "tools": [],
            "query": query,
            "total_available": len(_full_catalog.tools) if _full_catalog else 0,
            "error": str(e)
        }

def get_tool_search_definition() -> ToolDefinition:
    """
    Get the ToolDefinition for tool_search_tool.
    
    This tool should always be loaded in the initial context.
    """
    from ..shared.models import ToolParameter, ToolExample
    
    return ToolDefinition(
        name="tool_search_tool",
        type="function",
        description=(
            "Search for tools by capability description. Use this when you need a tool "
            "but don't see it in your available tools. Returns relevant tools that can "
            "then be used to complete the task."
        ),
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Natural language description of what you want to do",
                required=True
            ),
            ToolParameter(
                name="top_k",
                type="integer",
                description="Number of relevant tools to return (default: 5, max: 20)",
                required=False,
                default=5
            )
        ],
        returns={
            "type": "object",
            "properties": {
                "tools": {"type": "array", "description": "List of matching tool definitions"},
                "query": {"type": "string"},
                "total_available": {"type": "integer"},
                "returned": {"type": "integer"}
            }
        },
        source="built-in",
        version="1.0",
        defer_loading=False,  # Always load this tool
        examples=[
            ToolExample(
                scenario="Need to create a GitHub pull request but don't see github tools",
                input={"query": "create pull request on github", "top_k": 3},
                output={
                    "tools": ["github.createPR", "github.updatePR", "github.listPRs"],
                    "returned": 3
                },
                notes="Use tool_search_tool first, then use the returned tools"
            ),
            ToolExample(
                scenario="Need to send a notification but not sure which tool",
                input={"query": "send notification to team", "top_k": 5},
                output={
                    "tools": ["slack.sendMessage", "teams.postMessage", "email.send"],
                    "returned": 3
                },
                notes="Search returns tools from multiple services matching the intent"
            )
        ],
        metadata={
            "always_available": True,
            "category": "tool_discovery",
            "phase": 6
        }
    )
