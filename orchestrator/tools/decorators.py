from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import Any, Literal, get_args, get_origin

from ..plugins.registry import get_registry, register_plugin
from ..shared.models import ToolDefinition, ToolParameter

logger = logging.getLogger(__name__)


class _FunctionDecoratorPlugin:
    """Collects functions decorated with @tool and exposes them via PluginProtocol."""

    def __init__(self) -> None:
        self._functions: dict[str, Callable[[dict[str, Any]], Any]] = {}
        self._defs: dict[str, ToolDefinition] = {}

    def get_tools(self) -> list[dict[str, Any]]:
        # Return ToolDefinitions as plain dicts for registry consumers
        # Use Pydantic model_dump for proper serialization of nested models
        return [td.model_dump() for td in self._defs.values()]

    async def execute(self, tool_name: str, params: dict[str, Any]) -> Any:
        fn = self._functions.get(tool_name)
        if fn is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        result = fn(params)
        if inspect.isawaitable(result):
            return await result
        return result

    def add(self, name: str, fn: Callable[[dict[str, Any]], Any], td: ToolDefinition) -> None:
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
    name: str | None = None,
    description: str = "",
    provider: str | None = None,
    type: Literal["mcp", "function", "code_exec", "agent", "tool"] = "function",
    parameters: list[ToolParameter] | None = None,
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to declare a function as a ToolWeaver tool.

    Example:
        @tool(description="Echo input", parameters=[ToolParameter(name="text", type="string", required=True, description="Text to echo")])
        def echo(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"text": params["text"]}
    """

    def wrapper(fn: Callable[..., Any]) -> Callable[..., Any]:
        tool_name = name or fn.__name__
        inferred_params = parameters or _infer_parameters_from_signature(fn)
        td = ToolDefinition(
            name=tool_name,
            description=description or (fn.__doc__ or tool_name),
            provider=provider,
            type="function",
            parameters=inferred_params,
            input_schema=input_schema,
            output_schema=output_schema,
            metadata=metadata or {},
            source="decorator",
        )
        return _register_bound_function(fn=fn, tool_def=td, expects_kwargs=False)

    return wrapper


def mcp_tool(
    *,
    name: str | None = None,
    description: str = "",
    provider: str | None = "mcp",
    domain: str = "general",
    parameters: list[ToolParameter] | None = None,
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
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
    name: str | None = None,
    description: str = "",
    provider: str | None = "a2a",
    domain: str = "general",
    parameters: list[ToolParameter] | None = None,
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
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
) -> Callable[[dict[str, Any]], Any]:
    plugin = _ensure_plugin()

    _validate_tool_signature(fn=fn, tool_def=tool_def, expects_kwargs=expects_kwargs)

    async def bound(params: dict[str, Any]) -> Any:
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

    # Log tool registration
    logger.info(
        f"Tool registered: {tool_def.name}",
        extra={
            "tool_name": tool_def.name,
            "tool_type": tool_def.type,
            "provider": tool_def.provider,
            "domain": getattr(tool_def, "domain", "general"),
            "param_count": len(tool_def.parameters),
        }
    )

    return bound


def _validate_tool_signature(*, fn: Callable[..., Any], tool_def: ToolDefinition, expects_kwargs: bool) -> None:
    """Validate decorator usage and surface helpful warnings/errors."""
    sig = inspect.signature(fn)

    # Missing docstring
    if not (fn.__doc__ or "").strip():
        logger.warning("Tool '%s' is missing a docstring", tool_def.name)

    # Missing return annotation
    if sig.return_annotation is inspect.Signature.empty:
        logger.warning("Tool '%s' is missing a return type annotation", tool_def.name)

    # Missing parameter annotations
    missing_param_annotations = [p.name for p in sig.parameters.values() if p.annotation is inspect.Signature.empty]
    if missing_param_annotations:
        logger.warning(
            "Tool '%s' parameters missing type hints: %s",
            tool_def.name,
            ", ".join(missing_param_annotations),
        )

    # Invalid parameter names (fail fast)
    param_names = [p.name for p in sig.parameters.values()]
    invalid = [name for name in param_names if not name.isidentifier()]
    if invalid:
        raise ValueError(f"Tool '{tool_def.name}' has invalid parameter names: {', '.join(invalid)}")

    # Ensure provided ToolParameters align with function signature when using kwargs
    if expects_kwargs and tool_def.parameters:
        provided_names = {p.name for p in tool_def.parameters}
        missing_in_params = [n for n in param_names if n not in provided_names]
        if missing_in_params:
            raise ValueError(
                f"Tool '{tool_def.name}' parameter mismatch: signature has {missing_in_params}"
            )


def _infer_parameters_from_signature(fn: Callable[..., Any]) -> list[ToolParameter]:
    sig = inspect.signature(fn)
    inferred: list[ToolParameter] = []

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


def _infer_returns_schema(fn: Callable[..., Any]) -> dict[str, Any] | None:
    annotation = getattr(fn, "__annotations__", {}).get("return", inspect._empty)
    if annotation is inspect._empty:
        return None
    return {"type": _map_annotation_to_param_type(annotation)}


def _map_annotation_to_param_type(annotation: Any) -> str:
    if annotation is inspect._empty:
        return "string"

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is list or origin is list:
        return "array"
    if origin is dict or origin is dict:
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
    if annotation in (dict, dict):
        return "object"
    if annotation in (list, list, tuple, set):
        return "array"

    return "string"


def _is_optional_annotation(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is None:
        return False
    args = get_args(annotation)
    return any(arg is type(None) for arg in args)  # noqa: E721
