"""
Minimal demo of using the ToolWeaver `@tool` decorator.

This example declares a simple echo tool and executes it via the plugin registry.
"""
from typing import Any

from orchestrator import tool
from orchestrator.plugins.registry import get_registry
from orchestrator.shared.models import ToolParameter


@tool(
    description="Echo the provided text",
    parameters=[
        ToolParameter(name="text", type="string", description="Text to echo", required=True)
    ],
    metadata={"example": True},
)
def echo(params: dict[str, Any]) -> dict[str, Any]:
    """Echo the input text."""
    return {"text": params["text"]}


def main() -> None:
    registry = get_registry()
    plugin = registry.get("decorators")

    tools = plugin.get_tools()
    print("Discovered decorator tools:", tools)

    import asyncio
    result = asyncio.get_event_loop().run_until_complete(plugin.execute("echo", {"text": "hello"}))
    print("Execution result:", result)


if __name__ == "__main__":
    main()
