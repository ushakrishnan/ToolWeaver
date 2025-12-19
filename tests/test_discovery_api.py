from typing import Any, Dict

import asyncio

from orchestrator import (
    tool,
    FunctionToolTemplate,
    register_template,
    get_available_tools,
    search_tools,
    get_tool_info,
    list_tools_by_domain,
)
from orchestrator.plugins.registry import get_registry
from orchestrator.shared.models import ToolParameter


def test_discovery_lists_decorator_and_template():
    registry = get_registry()
    registry.clear()

    @tool(description="Echo", parameters=[ToolParameter(name="text", type="string", description="", required=True)])
    def echo(params: Dict[str, Any]) -> Dict[str, Any]:
        return {"text": params["text"]}

    class EchoTemplate(FunctionToolTemplate):
        def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
            return {"text": params["text"]}

    tmpl = EchoTemplate(name="echo_tpl", description="Echo template")
    register_template(tmpl)

    tools = get_available_tools()
    names = sorted(t.name for t in tools)
    assert names == ["echo", "echo_tpl"]


def test_search_and_get_info():
    registry = get_registry()
    registry.clear()

    @tool(description="Process order", metadata={"tags": ["order"]})
    def process_order(params: Dict[str, Any]) -> Dict[str, Any]:
        return params

    results = search_tools(query="order")
    assert any(t.name == "process_order" for t in results)

    info = get_tool_info("process_order")
    assert info is not None and info.name == "process_order"


def test_list_by_domain():
    registry = get_registry()
    registry.clear()

    @tool(description="Finance tool", metadata={"tags": ["finance"]})
    def fin(params: Dict[str, Any]) -> Dict[str, Any]:
        return params

    # Default domain is "general" per models
    tools = list_tools_by_domain("general")
    assert any(t.name == "fin" for t in tools)
