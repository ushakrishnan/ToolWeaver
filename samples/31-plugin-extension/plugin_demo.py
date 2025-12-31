import asyncio
from typing import Any

from orchestrator import get_plugin, list_plugins, register_plugin


class DemoPlugin:
    def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "echo_text",
                "description": "Echo back provided text",
                "parameters": [
                    {"name": "text", "type": "string", "required": True, "description": "Text to echo"}
                ],
                "domain": "demo",
            },
            {
                "name": "word_count",
                "description": "Count words in text",
                "parameters": [
                    {"name": "text", "type": "string", "required": True, "description": "Input text"}
                ],
                "domain": "demo",
            },
        ]

    async def execute(self, tool_name: str, params: dict[str, Any]) -> Any:
        if tool_name == "echo_text":
            return {"output": params.get("text", ""), "cost": 0.0}
        if tool_name == "word_count":
            text = params.get("text", "")
            return {"output": len(text.split()), "cost": 0.0}
        raise ValueError(f"Unknown tool: {tool_name}")


async def main() -> None:
    # Register plugin
    register_plugin("demo", DemoPlugin())

    # List plugins
    print("Plugins:", list_plugins())

    # Retrieve plugin and execute tools
    plugin = get_plugin("demo")
    out1 = await plugin.execute("echo_text", {"text": "hello ToolWeaver"})
    out2 = await plugin.execute("word_count", {"text": "count these three words"})
    print("echo_text ->", out1)
    print("word_count ->", out2)


if __name__ == "__main__":
    asyncio.run(main())
