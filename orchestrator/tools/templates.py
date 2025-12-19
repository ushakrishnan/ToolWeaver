from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..shared.models import ToolDefinition, ToolParameter
from ..plugins.registry import PluginProtocol, register_plugin, get_registry


class BaseTemplate:
    """Abstract base for tool/agent templates that produce `ToolDefinition` and execute.

    Subclasses should set `type` appropriately and implement `execute()`.
    """

    name: str
    description: str
    type: str
    provider: Optional[str]
    parameters: List[ToolParameter]
    metadata: Dict[str, Any]
    input_schema: Optional[Dict[str, Any]]
    output_schema: Optional[Dict[str, Any]]
    returns: Optional[Dict[str, Any]]

    def __init__(
        self,
        *,
        name: str,
        description: str = "",
        type: str,
        provider: Optional[str] = None,
        parameters: Optional[List[ToolParameter]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        returns: Optional[Dict[str, Any]] = None,
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

    def execute(self, params: Dict[str, Any]) -> Any:  # pragma: no cover - abstract
        raise NotImplementedError("Subclasses must implement execute()")


class FunctionToolTemplate(BaseTemplate):
    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("type", "function")
        super().__init__(**kwargs)


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
        self._templates: Dict[str, BaseTemplate] = {}
        self._defs: Dict[str, ToolDefinition] = {}

    def get_tools(self) -> List[Dict[str, Any]]:
        # Serialize ToolDefinition to dict, including nested models
        return [td.model_dump() for td in self._defs.values()]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
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
