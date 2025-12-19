from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from ..shared.models import ToolDefinition, ToolParameter
from ..plugins.registry import PluginProtocol, register_plugin, get_registry


class _FunctionDecoratorPlugin:
    """Collects functions decorated with @tool and exposes them via PluginProtocol."""

    def __init__(self) -> None:
        self._functions: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._defs: Dict[str, ToolDefinition] = {}

    def get_tools(self) -> List[Dict[str, Any]]:
        # Return ToolDefinitions as plain dicts for registry consumers
        # Use Pydantic model_dump for proper serialization of nested models
        return [td.model_dump() for td in self._defs.values()]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
        fn = self._functions.get(tool_name)
        if fn is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        return fn(params)

    def add(self, name: str, fn: Callable[[Dict[str, Any]], Any], td: ToolDefinition) -> None:
        self._functions[name] = fn
        self._defs[name] = td


_DEF_PLUGIN_NAME = "decorators"


def _ensure_plugin() -> _FunctionDecoratorPlugin:
    registry = get_registry()
    if not registry.has(_DEF_PLUGIN_NAME):
        plugin = _FunctionDecoratorPlugin()
        register_plugin(_DEF_PLUGIN_NAME, plugin)
        return plugin
    return registry.get(_DEF_PLUGIN_NAME)  # type: ignore[return-value]


def tool(
    *,
    name: Optional[str] = None,
    description: str = "",
    provider: Optional[str] = None,
    type: str = "function",
    parameters: Optional[List[ToolParameter]] = None,
    input_schema: Optional[Dict[str, Any]] = None,
    output_schema: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to declare a function as a ToolWeaver tool.

    Example:
        @tool(description="Echo input", parameters=[ToolParameter(name="text", type="string", required=True, description="Text to echo")])
        def echo(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"text": params["text"]}
    """

    def wrapper(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or fn.__name__
        td = ToolDefinition(
            name=tool_name,
            description=description or (fn.__doc__ or tool_name),
            provider=provider,
            type=type,
            parameters=parameters or [],
            input_schema=input_schema,
            output_schema=output_schema,
            metadata=metadata or {},
            source="decorator",
        )
        plugin = _ensure_plugin()

        def bound(params: Dict[str, Any]) -> Any:
            return fn(params)

        plugin.add(tool_name, bound, td)
        return bound

    return wrapper
