from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from ..plugins.registry import get_registry
from ..shared.models import ToolDefinition, ToolCatalog

logger = logging.getLogger(__name__)


def _collect_all_tool_defs() -> List[ToolDefinition]:
    """Collect all tool definitions from all plugins, normalized to ToolDefinition.

    Plugins return lists of dicts; we validate to ToolDefinition for consistent access.
    """
    registry = get_registry()
    all_tools: List[ToolDefinition] = []
    for _, tools in registry.get_all_tools().items():
        for t in tools:
            try:
                td = ToolDefinition.model_validate(t)
                all_tools.append(td)
            except Exception:
                # Skip invalid entries rather than failing discovery
                continue
    return all_tools


def get_available_tools(
    *,
    plugin: Optional[str] = None,
    type_filter: Optional[str] = None,
    domain: Optional[str] = None,
) -> List[ToolDefinition]:
    """List available tools across all plugins with optional filters."""
    registry = get_registry()
    tool_dict: Dict[str, List[Dict[str, Any]]] = (
        {plugin: registry.get(plugin).get_tools()} if plugin else registry.get_all_tools()
    )

    out: List[ToolDefinition] = []
    for _, tools in tool_dict.items():
        for t in tools:
            try:
                td = ToolDefinition.model_validate(t)
            except Exception:
                continue
            if type_filter and td.type != type_filter:
                continue
            if domain and td.domain != domain:
                continue
            out.append(td)
    return out


def search_tools(
    *,
    query: Optional[str] = None,
    domain: Optional[str] = None,
    type_filter: Optional[str] = None,
    use_semantic: bool = False,
    top_k: int = 10,
    min_score: float = 0.3,
) -> List[ToolDefinition]:
    """Keyword search across name and description with optional filters.

    By default uses simple substring search. Set use_semantic=True to enable
    vector-backed semantic search (requires Qdrant).
    
    Args:
        query: Search query
        domain: Optional domain filter
        type_filter: Optional type filter
        use_semantic: Use semantic search instead of substring (requires Qdrant)
        top_k: Number of results for semantic search
        min_score: Minimum score for semantic search (0-1)
    
    Returns:
        List of ToolDefinition objects
    """
    # Semantic search path
    if use_semantic and query:
        try:
            results_with_scores = semantic_search_tools(
                query=query,
                top_k=top_k,
                domain=domain,
                min_score=min_score,
                fallback_to_substring=True
            )
            # Filter by type if specified
            if type_filter:
                results_with_scores = [
                    (tool, score) for tool, score in results_with_scores 
                    if tool.type == type_filter
                ]
            return [tool for tool, _ in results_with_scores]
        except Exception as e:
            logger.warning(f"Semantic search failed, falling back to substring: {e}")
    
    # Substring search (original implementation)
    query_norm = (query or "").strip().lower()
    results: List[ToolDefinition] = []
    for td in _collect_all_tool_defs():
        if type_filter and td.type != type_filter:
            continue
        if domain and td.domain != domain:
            continue
        if not query_norm:
            results.append(td)
            continue
        hay = f"{td.name} {td.description}".lower()
        if query_norm in hay:
            results.append(td)
    return results


def get_tool_info(name: str) -> Optional[ToolDefinition]:
    """Get full tool definition by name across all plugins."""
    for td in _collect_all_tool_defs():
        if td.name == name:
            return td
    return None


def list_tools_by_domain(domain: str) -> List[ToolDefinition]:
    return [td for td in _collect_all_tool_defs() if td.domain == domain]


def semantic_search_tools(
    query: str,
    *,
    top_k: int = 5,
    domain: Optional[str] = None,
    min_score: float = 0.3,
    fallback_to_substring: bool = True
) -> List[Tuple[ToolDefinition, float]]:
    """
    Semantic search across tools using vector similarity.
    
    Uses VectorToolSearchEngine with Qdrant for semantic search. Falls back to
    substring search if Qdrant is unavailable and fallback_to_substring=True.
    
    Args:
        query: Natural language query
        top_k: Number of results to return
        domain: Optional domain filter (e.g., "github", "slack")
        min_score: Minimum similarity score (0-1)
        fallback_to_substring: Use substring search if vector search unavailable
    
    Returns:
        List of (ToolDefinition, score) tuples sorted by relevance
    
    Example:
        results = semantic_search_tools("create github pull request", top_k=3)
        for tool, score in results:
            print(f"{tool.name}: {score:.2f}")
    """
    try:
        from .vector_search import VectorToolSearchEngine
    except ImportError:
        logger.warning("Vector search dependencies not available (qdrant-client, sentence-transformers)")
        if fallback_to_substring:
            logger.info("Falling back to substring search")
            substring_results = search_tools(query=query, domain=domain)
            return [(tool, 1.0) for tool in substring_results[:top_k]]
        return []
    
    # Build catalog from all tools
    all_tools = _collect_all_tool_defs()
    if domain:
        all_tools = [t for t in all_tools if t.domain == domain]
    
    catalog = ToolCatalog(tools={t.name: t for t in all_tools})
    
    # Initialize search engine with fallback enabled
    search_engine = VectorToolSearchEngine(
        fallback_to_memory=True
    )
    
    # Index catalog (lazy, cached in Qdrant)
    try:
        search_engine.index_catalog(catalog, batch_size=32)
    except Exception as e:
        logger.warning(f"Failed to index catalog: {e}")
        if fallback_to_substring:
            logger.info("Falling back to substring search")
            substring_results = search_tools(query=query, domain=domain)
            return [(tool, 1.0) for tool in substring_results[:top_k]]
        return []
    
    # Perform semantic search
    try:
        results = search_engine.search(
            query=query,
            catalog=catalog,
            top_k=top_k,
            domain=domain,
            min_score=min_score
        )
        return results
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        if fallback_to_substring:
            logger.info("Falling back to substring search")
            substring_results = search_tools(query=query, domain=domain)
            return [(tool, 1.0) for tool in substring_results[:top_k]]
        return []

