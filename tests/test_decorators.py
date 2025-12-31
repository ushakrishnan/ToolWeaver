import asyncio
from typing import Any

import pytest

from orchestrator import a2a_agent, mcp_tool, tool
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
    def echo(params: dict[str, Any]) -> dict[str, Any]:
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
    result = asyncio.run(plugin.execute("echo", {"text": "hello"}))
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
    def echo(params: dict[str, Any]) -> dict[str, Any]:
        return {"text": params["text"]}

    plugin = registry.get("decorators")
    tools = plugin.get_tools()

    assert tools[0]["name"] == "custom_echo"
    assert tools[0]["provider"] == "local"

    # Execute with custom name
    result = asyncio.run(plugin.execute("custom_echo", {"text": "world"}))
    assert result == {"text": "world"}


def test_mcp_tool_auto_params_and_async_execution():
    registry = get_registry()
    registry.clear()

    @mcp_tool(domain="finance")
    async def get_balance(account: str, include_pending: bool = False) -> dict[str, Any]:
        return {"account": account, "pending": include_pending}

    plugin = registry.get("decorators")
    tools = plugin.get_tools()

    td = tools[0]
    assert td["type"] == "mcp"
    assert td["domain"] == "finance"

    params = {p["name"]: p for p in td["parameters"]}
    assert params["account"]["required"] is True
    assert params["include_pending"]["required"] is False

    result = asyncio.run(plugin.execute("get_balance", {"account": "123"}))
    assert result == {"account": "123", "pending": False}


def test_a2a_agent_decorator_sync_function():
    registry = get_registry()
    registry.clear()

    @a2a_agent(description="Route work to agents")
    def route(task: str, priority: int = 1) -> dict[str, Any]:
        return {"task": task, "priority": priority}

    plugin = registry.get("decorators")
    td = plugin.get_tools()[0]

    assert td["type"] == "agent"
    assert td["parameters"][0]["name"] == "task"
    assert td["parameters"][0]["required"] is True
    assert td["parameters"][1]["name"] == "priority"
    assert td["parameters"][1]["required"] is False

    result = asyncio.run(plugin.execute("route", {"task": "triage"}))
    assert result == {"task": "triage", "priority": 1}


def test_decorator_validates_function_signature():
    """Test that decorator validation works on function signatures."""
    registry = get_registry()
    registry.clear()

    # Test that missing docstring triggers warning (but still registers)
    @tool()
    def no_docstring(x: int) -> int:
        return x

    # Should register successfully despite warning
    assert registry.has("decorators")

    # Clean up for next test
    registry.clear()


def test_decorator_rejects_signature_mismatch_for_kwargs():
    registry = get_registry()
    registry.clear()

    with pytest.raises(ValueError, match="parameter mismatch"):
        @mcp_tool(parameters=[ToolParameter(name="only_one", type="string", required=True, description="Test param")])
        def expect_two(a: str, b: str) -> dict[str, Any]:
            return {"a": a, "b": b}
