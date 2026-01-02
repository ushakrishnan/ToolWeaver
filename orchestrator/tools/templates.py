from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Literal

from ..plugins.registry import get_registry, register_plugin
from ..shared.models import ToolDefinition, ToolParameter

logger = logging.getLogger(__name__)


class BaseTemplate:
    """Abstract base for tool/agent templates that produce `ToolDefinition` and execute.

    Subclasses should set `type` appropriately and implement `execute()`.
    """

    name: str
    description: str
    type: Literal["mcp", "function", "code_exec", "agent", "tool"]
    provider: str | None
    parameters: list[ToolParameter]
    metadata: dict[str, Any]
    input_schema: dict[str, Any] | None
    output_schema: dict[str, Any] | None
    returns: dict[str, Any] | None

    def __init__(
        self,
        *,
        name: str,
        description: str = "",
        type: Literal["mcp", "function", "code_exec", "agent", "tool"],
        provider: str | None = None,
        parameters: list[ToolParameter] | None = None,
        metadata: dict[str, Any] | None = None,
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
        returns: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.description = description or name
        self.type = type
        self.provider = provider
        self.parameters = parameters or []
        self.metadata = metadata or {}
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.returns = returns

    def build_definition(self) -> ToolDefinition:
        """Create a `ToolDefinition` from this template."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            type=self.type,
            provider=self.provider,
            parameters=self.parameters,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            returns=self.returns,
            metadata=self.metadata,
            source="template",
        )

    def execute(self, params: dict[str, Any]) -> Any:  # pragma: no cover - abstract
        raise NotImplementedError("Subclasses must implement execute()")

    def save_as_skill(self, *, tags: list[str] | None = None, bump_type: str = "patch") -> Any:
        """
        Save this tool's implementation as a skill in the skill library.

        Args:
            tags: Optional tags for skill categorization
            bump_type: Version bump type if updating ("major", "minor", "patch")

        Returns:
            Skill object

        Raises:
            NotImplementedError: If template doesn't have a callable function to save
        """
        # Import here to avoid circular dependency
        from .skill_bridge import save_tool_as_skill

        # Get the execute function or override in subclass
        if hasattr(self, '_function') and callable(self._function):
            func = self._function
        else:
            raise NotImplementedError(
                f"Template '{self.name}' does not have a callable function to save as skill. "
                "Subclasses should store their function in self._function or override this method."
            )

        tool_def = self.build_definition()
        return save_tool_as_skill(tool_def, func, tags=tags, bump_type=bump_type)

    @classmethod
    def load_from_skill(
        cls,
        skill_name: str,
        *,
        version: str | None = None,
        **template_kwargs: Any
    ) -> tuple[BaseTemplate, Callable[..., Any]]:
        """
        Create a template instance from a skill in the skill library.

        Args:
            skill_name: Name of the skill to load
            version: Optional specific version (defaults to latest)
            **template_kwargs: Additional kwargs to pass to template __init__

        Returns:
            Tuple of (template instance, callable function)

        Example:
            >>> template, func = FunctionToolTemplate.load_from_skill("process_data")
            >>> result = func({"input": "test"})
        """
        from .skill_bridge import load_tool_from_skill

        tool_def, func = load_tool_from_skill(
            skill_name,
            version=version,
            tool_type=template_kwargs.get('type', 'function')
        )

        # Create template instance with tool definition fields
        template = cls(
            name=tool_def.name,
            description=tool_def.description,
            type=tool_def.type,
            provider=tool_def.provider,
            parameters=tool_def.parameters,
            input_schema=tool_def.input_schema,
            output_schema=tool_def.output_schema,
            metadata=tool_def.metadata,
            **template_kwargs
        )

        # Store function for later save_as_skill calls
        template._function = func  # type: ignore

        return template, func


class FunctionToolTemplate(BaseTemplate):
    """Template for simple function-based tools.

    Stores the function for skill bridge integration.
    """

    def __init__(self, *, function: Callable[..., Any] | None = None, **kwargs: Any) -> None:
        kwargs.setdefault("type", "function")
        super().__init__(**kwargs)
        self._function = function

    def execute(self, params: dict[str, Any]) -> Any:
        """Execute the function with given parameters."""
        if self._function is None:
            raise NotImplementedError("No function set for this template")
        return self._function(**params)


class MCPToolTemplate(BaseTemplate):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("type", "mcp")
        super().__init__(**kwargs)


class CodeExecToolTemplate(BaseTemplate):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("type", "code_exec")
        super().__init__(**kwargs)


class AgentTemplate(BaseTemplate):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("type", "agent")
        super().__init__(**kwargs)


class _TemplatePlugin:
    """Plugin that exposes registered templates via `PluginProtocol`."""

    def __init__(self) -> None:
        self._templates: dict[str, BaseTemplate] = {}
        self._defs: dict[str, ToolDefinition] = {}

    def get_tools(self) -> list[dict[str, Any]]:
        # Serialize ToolDefinition to dict, including nested models
        return [td.model_dump() for td in self._defs.values()]

    async def execute(self, tool_name: str, params: dict[str, Any]) -> Any:
        tmpl = self._templates.get(tool_name)
        if tmpl is None:
            raise ValueError(f"Unknown template tool: {tool_name}")
        return tmpl.execute(params)

    def add(self, tmpl: BaseTemplate) -> None:
        td = tmpl.build_definition()
        self._templates[tmpl.name] = tmpl
        self._defs[tmpl.name] = td


_TPL_PLUGIN_NAME = "templates"


def _ensure_template_plugin() -> _TemplatePlugin:
    registry = get_registry()
    if not registry.has(_TPL_PLUGIN_NAME):
        plugin = _TemplatePlugin()
        register_plugin(_TPL_PLUGIN_NAME, plugin)
        return plugin
    return registry.get(_TPL_PLUGIN_NAME)  # type: ignore[return-value]


def register_template(template: BaseTemplate) -> None:
    """Register a template into the global `templates` plugin."""
    plugin = _ensure_template_plugin()
    plugin.add(template)
