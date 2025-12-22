from __future__ import annotations

from typing import Any, Dict, Tuple, Type, cast

from pydantic import BaseModel, create_model

from orchestrator._internal.logger import get_logger
from orchestrator._internal.validation import (
    ToolDefinition,
    ToolParameter,
    ValidationErrorBase,
    InvalidInputError,
    validate_tool_input,
)


logger = get_logger(__name__)


ALLOWED_PARAM_TYPES = {
    "string": str,
    "number": float,
    "integer": int,
    "boolean": bool,
    "object": dict,
    "array": list,
}


def _build_schema_from_tool(tool: ToolDefinition) -> Type[BaseModel]:
    fields: Dict[str, Tuple[type, Any]] = {}

    for p in tool.parameters:
        if p.type not in ALLOWED_PARAM_TYPES:
            raise InvalidInputError(
                f"Unsupported parameter type '{p.type}' for '{p.name}'."
            )

        py_type = ALLOWED_PARAM_TYPES[p.type]
        default = ... if p.required else (p.default if hasattr(p, "default") else None)

        # Pydantic expects a tuple of (type, default)
        fields[p.name] = (py_type, default)

    model = create_model(
        f"ToolInput__{tool.name}",
        __base__=BaseModel,
        **cast(Dict[str, Any], fields),
    )
    return model


def validate_registration(tool: ToolDefinition) -> ToolDefinition:
    # Basic checks
    if not tool.name or not isinstance(tool.name, str):
        raise InvalidInputError("Tool name must be a non-empty string")
    if not tool.description or not isinstance(tool.description, str):
        raise InvalidInputError("Tool description must be a non-empty string")

    # Parameter names unique and valid
    seen = set()
    for param in tool.parameters:
        if not isinstance(param, ToolParameter):
            raise InvalidInputError("Parameters must be ToolParameter instances")
        if not param.name or not isinstance(param.name, str):
            raise InvalidInputError("Parameter name must be a non-empty string")
        if param.name in seen:
            raise InvalidInputError(f"Duplicate parameter name: {param.name}")
        seen.add(param.name)
        if param.type not in ALLOWED_PARAM_TYPES:
            raise InvalidInputError(
                f"Unsupported parameter type '{param.type}' for '{param.name}'"
            )

    logger.debug("Registration validated for tool %s", tool.name)
    return tool


def validate_call(params: dict[str, Any], tool: ToolDefinition) -> dict[str, Any]:
    try:
        schema = _build_schema_from_tool(tool)
        return validate_tool_input(params, schema=schema, sanitize=True)
    except ValidationErrorBase:
        raise
    except Exception as e:  # Safety net to unify unexpected errors
        raise InvalidInputError(f"Validation failed: {e}") from e


__all__ = [
    "validate_registration",
    "validate_call",
]
