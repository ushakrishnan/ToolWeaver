from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..plugins.registry import get_registry
from ..shared.models import ToolDefinition


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
) -> List[ToolDefinition]:
    """Keyword search across name and description with optional filters.

    This is a simple substring search; semantic search can be added later.
    """
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
