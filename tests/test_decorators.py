import asyncio
from typing import Any, Dict

import pytest

from orchestrator import tool
from orchestrator.plugins.registry import get_registry
from orchestrator.shared.models import ToolParameter


def test_tool_decorator_registers_and_executes():
    # Ensure a clean registry state for this test
    registry = get_registry()
    registry.clear()

    @tool(
        description="Echo the provided text",
        parameters=[
            ToolParameter(name="text", type="string", description="Text to echo", required=True)
        ],
        metadata={"category": "testing"},
    )
    def echo(params: Dict[str, Any]) -> Dict[str, Any]:
        return {"text": params["text"]}

    # Decorating registers under the 'decorators' plugin
    assert registry.has("decorators"), "decorators plugin should be registered"

    plugin = registry.get("decorators")

    # Tools should include our 'echo' tool definition
    tools = plugin.get_tools()
    assert isinstance(tools, list) and len(tools) == 1

    td = tools[0]
    assert td["name"] == "echo"
    assert td["type"] == "function"
    assert td["source"] == "decorator"
    assert td["metadata"].get("category") == "testing"

    # Execute the tool through the plugin
    result = asyncio.get_event_loop().run_until_complete(plugin.execute("echo", {"text": "hello"}))
    assert result == {"text": "hello"}


def test_tool_decorator_custom_name_and_provider():
    registry = get_registry()
    registry.clear()

    @tool(
        name="custom_echo",
        description="Echo with custom name",
        provider="local",
        parameters=[
            ToolParameter(name="text", type="string", description="Text to echo", required=True)
        ],
    )
    def echo(params: Dict[str, Any]) -> Dict[str, Any]:
        return {"text": params["text"]}

    plugin = registry.get("decorators")
    tools = plugin.get_tools()

    assert tools[0]["name"] == "custom_echo"
    assert tools[0]["provider"] == "local"

    # Execute with custom name
    result = asyncio.get_event_loop().run_until_complete(plugin.execute("custom_echo", {"text": "world"}))
    assert result == {"text": "world"}
