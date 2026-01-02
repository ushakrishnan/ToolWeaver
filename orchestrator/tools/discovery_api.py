from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from ..plugins.registry import get_registry
from ..shared.models import ToolCatalog, ToolDefinition

logger = logging.getLogger(__name__)


def _collect_all_tool_defs() -> list[ToolDefinition]:
    """Collect all tool definitions from all plugins, normalized to ToolDefinition.

    Plugins return lists of dicts; we validate to ToolDefinition for consistent access.
    """
    registry = get_registry()
    all_tools: list[ToolDefinition] = []
    for _, tools in registry.get_all_tools().items():
        for t in tools:
            try:
                td = ToolDefinition.model_validate(t)
                all_tools.append(td)
            except Exception:
                # Skip invalid entries rather than failing discovery
                continue
    return all_tools


DETAIL_LEVELS = {"name", "summary", "full"}


def _format_tool_view(
    tool: ToolDefinition,
    *,
    detail_level: str = "summary",
    include_examples: bool = False,
) -> ToolDefinition | dict[str, Any]:
    """Project a tool definition to a lightweight view for progressive loading."""
    if detail_level is not None and detail_level not in DETAIL_LEVELS:
        raise ValueError(f"detail_level must be one of {sorted(DETAIL_LEVELS)}")

    if detail_level == "full" or detail_level is None:
        return tool

    base_view: dict[str, Any] = {
        "name": tool.name,
        "type": tool.type,
        "domain": tool.domain,
        "source": tool.source,
        "version": tool.version,
        "defer_loading": tool.defer_loading,
    }

    if detail_level == "name":
        return base_view

    summary: dict[str, Any] = {
        **base_view,
        "description": tool.description,
        "provider": tool.provider,
        "parameter_count": len(tool.parameters),
        "example_count": len(tool.examples),
        "metadata": tool.metadata,
    }

    if include_examples and tool.examples:
        summary["examples"] = [ex.model_dump() for ex in tool.examples]

    return summary


def get_available_tools(
    *,
    plugin: str | None = None,
    type_filter: str | None = None,
    domain: str | None = None,
) -> list[ToolDefinition]:
    """List available tools across all plugins with optional filters."""
    registry = get_registry()
    tool_dict: dict[str, list[dict[str, Any]]] = (
        {plugin: registry.get(plugin).get_tools()} if plugin else registry.get_all_tools()
    )

    out: list[ToolDefinition] = []
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


def browse_tools(
    *,
    plugin: str | None = None,
    type_filter: str | None = None,
    domain: str | None = None,
    detail_level: str = "summary",
    offset: int = 0,
    limit: int | None = 50,
    include_examples: bool = False,
) -> Sequence[ToolDefinition | dict[str, Any]]:
    """Browse tools with pagination and progressive detail levels.

    Uses lightweight projections to avoid loading full schemas when not needed.
    """
    if offset < 0 or (limit is not None and limit < 0):
        raise ValueError("offset and limit must be non-negative")

    tools = get_available_tools(plugin=plugin, type_filter=type_filter, domain=domain)
    tools = sorted(tools, key=lambda t: t.name)
    end = offset + limit if limit is not None else None
    window = tools[offset:end]

    return [
        _format_tool_view(tool, detail_level=detail_level, include_examples=include_examples)
        for tool in window
    ]


def search_tools(
    *,
    query: str | None = None,
    domain: str | None = None,
    type_filter: str | None = None,
    use_semantic: bool = False,
    top_k: int = 10,
    min_score: float = 0.3,
    detail_level: str | None = None,
    include_examples: bool = False,
) -> Sequence[ToolDefinition | dict[str, Any]]:
    """Keyword or semantic search with optional progressive detail levels."""
    logger.debug(
        "Searching tools",
        extra={
            "query": query,
            "domain": domain,
            "type_filter": type_filter,
            "use_semantic": use_semantic,
            "top_k": top_k,
        }
    )

    results: list[ToolDefinition] = []
    semantic_attempted = False

    if use_semantic and query:
        semantic_attempted = True
        try:
            results_with_scores = semantic_search_tools(
                query=query,
                top_k=top_k,
                domain=domain,
                min_score=min_score,
                fallback_to_substring=True,
            )
            if type_filter:
                results_with_scores = [
                    (tool, score) for tool, score in results_with_scores if tool.type == type_filter
                ]
            results = [tool for tool, _ in results_with_scores]
            logger.debug(f"Semantic search found {len(results)} results")
        except Exception as e:
            logger.warning(f"Semantic search failed, falling back to substring: {e}")
            results = []

    if not semantic_attempted or not results:
        query_norm = (query or "").strip().lower()
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

        logger.debug(f"Keyword search found {len(results)} results")

    logger.info(
        "Tool search completed",
        extra={
            "query": query,
            "domain": domain,
            "type_filter": type_filter,
            "results_count": len(results),
            "semantic_used": semantic_attempted and use_semantic,
        }
    )

    if detail_level:
        return [
            _format_tool_view(tool, detail_level=detail_level, include_examples=include_examples)
            for tool in results
        ]

    return results


def get_tool_info(
    name: str,
    *,
    detail_level: str = "full",
    include_examples: bool = True,
) -> ToolDefinition | dict[str, Any] | None:
    """Get tool definition by name with optional projection."""
    for td in _collect_all_tool_defs():
        if td.name == name:
            return _format_tool_view(td, detail_level=detail_level, include_examples=include_examples)
    return None


def list_tools_by_domain(domain: str) -> list[ToolDefinition]:
    return [td for td in _collect_all_tool_defs() if td.domain == domain]


def semantic_search_tools(
    query: str,
    *,
    top_k: int = 5,
    domain: str | None = None,
    min_score: float = 0.3,
    fallback_to_substring: bool = True
) -> list[tuple[ToolDefinition, float]]:
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
            # Call search_tools without detail_level to get List[ToolDefinition]
            substring_results = search_tools(query=query, domain=domain, detail_level=None)
            # Cast to list of tuples with ToolDefinition type
            return [(tool, 1.0) for tool in substring_results if isinstance(tool, ToolDefinition)][:top_k]
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
            substring_results = search_tools(query=query, domain=domain, detail_level=None)
            return [(tool, 1.0) for tool in substring_results if isinstance(tool, ToolDefinition)][:top_k]
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
            substring_results = search_tools(query=query, domain=domain, detail_level=None)
            return [(tool, 1.0) for tool in substring_results if isinstance(tool, ToolDefinition)][:top_k]
        return []

