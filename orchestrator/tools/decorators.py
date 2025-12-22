from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, get_args, get_origin

from ..shared.models import ToolDefinition, ToolParameter
from ..plugins.registry import PluginProtocol, register_plugin, get_registry

logger = logging.getLogger(__name__)


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
        result = fn(params)
        if inspect.isawaitable(result):
            return await result
        return result

    def add(self, name: str, fn: Callable[[Dict[str, Any]], Any], td: ToolDefinition) -> None:
        if name in self._functions:
            logger.warning("Duplicate tool registration detected for '%s'; replacing previous entry", name)
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
        return _register_bound_function(fn=fn, tool_def=td, expects_kwargs=False)

    return wrapper


def mcp_tool(
    *,
    name: Optional[str] = None,
    description: str = "",
    provider: Optional[str] = "mcp",
    domain: str = "general",
    parameters: Optional[List[ToolParameter]] = None,
    input_schema: Optional[Dict[str, Any]] = None,
    output_schema: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for MCP tools with auto parameter extraction from type hints."""

    def wrapper(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or fn.__name__
        inferred_params = parameters or _infer_parameters_from_signature(fn)
        td = ToolDefinition(
            name=tool_name,
            description=description or (fn.__doc__ or tool_name),
            provider=provider,
            type="mcp",
            parameters=inferred_params,
            input_schema=input_schema,
            output_schema=output_schema,
            metadata=metadata or {},
            source="decorator",
            domain=domain,
            returns=_infer_returns_schema(fn),
        )
        return _register_bound_function(fn=fn, tool_def=td, expects_kwargs=True)

    return wrapper


def a2a_agent(
    *,
    name: Optional[str] = None,
    description: str = "",
    provider: Optional[str] = "a2a",
    domain: str = "general",
    parameters: Optional[List[ToolParameter]] = None,
    input_schema: Optional[Dict[str, Any]] = None,
    output_schema: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for agent (A2A) tools with auto parameter extraction."""

    def wrapper(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or fn.__name__
        inferred_params = parameters or _infer_parameters_from_signature(fn)
        td = ToolDefinition(
            name=tool_name,
            description=description or (fn.__doc__ or tool_name),
            provider=provider,
            type="agent",
            parameters=inferred_params,
            input_schema=input_schema,
            output_schema=output_schema,
            metadata=metadata or {},
            source="decorator",
            domain=domain,
            returns=_infer_returns_schema(fn),
        )
        return _register_bound_function(fn=fn, tool_def=td, expects_kwargs=True)

    return wrapper


def _register_bound_function(
    *,
    fn: Callable[..., Any],
    tool_def: ToolDefinition,
    expects_kwargs: bool,
) -> Callable[[Dict[str, Any]], Any]:
    plugin = _ensure_plugin()

    async def bound(params: Dict[str, Any]) -> Any:
        call_params = params or {}
        try:
            result = fn(**call_params) if expects_kwargs else fn(call_params)
        except TypeError as exc:  # surface clearer error for bad calls
            raise TypeError(f"Failed to execute tool '{tool_def.name}': {exc}") from exc

        if inspect.isawaitable(result):
            return await result
        return result

    bound.__wrapped__ = fn  # type: ignore
    bound.__tool_definition__ = tool_def  # type: ignore

    plugin.add(tool_def.name, bound, tool_def)
    return bound


def _infer_parameters_from_signature(fn: Callable[..., Any]) -> List[ToolParameter]:
    sig = inspect.signature(fn)
    inferred: List[ToolParameter] = []

    for name, param in sig.parameters.items():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue

        annotation = param.annotation
        param_type = _map_annotation_to_param_type(annotation)
        optional = _is_optional_annotation(annotation)
        required = param.default is inspect._empty and not optional

        inferred.append(
            ToolParameter(
                name=name,
                type=param_type,
                description="",
                required=required,
            )
        )

    return inferred


def _infer_returns_schema(fn: Callable[..., Any]) -> Optional[Dict[str, Any]]:
    annotation = getattr(fn, "__annotations__", {}).get("return", inspect._empty)
    if annotation is inspect._empty:
        return None
    return {"type": _map_annotation_to_param_type(annotation)}


def _map_annotation_to_param_type(annotation: Any) -> str:
    if annotation is inspect._empty:
        return "string"

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is list or origin is List:
        return "array"
    if origin is dict or origin is Dict:
        return "object"
    if origin in (tuple, set):
        return "array"
    if origin is None and annotation is None:
        return "string"

    if origin is not None:
        non_none_args = [a for a in args if a is not type(None)]  # noqa: E721
        if non_none_args:
            return _map_annotation_to_param_type(non_none_args[0])

    if annotation in (str,):
        return "string"
    if annotation in (int,):
        return "integer"
    if annotation in (float,):
        return "number"
    if annotation in (bool,):
        return "boolean"
    if annotation in (dict, Dict):
        return "object"
    if annotation in (list, List, tuple, set):
        return "array"

    return "string"


def _is_optional_annotation(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is None:
        return False
    args = get_args(annotation)
    return any(arg is type(None) for arg in args)  # noqa: E721
