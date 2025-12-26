from typing import Any


class ExamplePlugin:
    """Minimal plugin example for ToolWeaver.

    Implements get_tools() and execute() so it can be registered via
    orchestrator.plugins.register_plugin.
    """

    def get_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "hello_plugin",
                "description": "Return a greeting from the plugin template",
                "parameters": {"name": {"type": "string", "required": False}},
            }
        ]

    async def execute(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        if tool_name != "hello_plugin":
            raise ValueError(f"Unknown tool: {tool_name}")
        name = params.get("name", "there")
        return {"message": f"Hello, {name} (from plugin)"}
