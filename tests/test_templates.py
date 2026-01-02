import asyncio
from typing import Any

from orchestrator import FunctionToolTemplate, register_template
import pytest

from orchestrator.plugins.registry import get_registry
from orchestrator.shared.models import ToolParameter


class EchoTemplate(FunctionToolTemplate):
    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        return {"text": params["text"]}


@pytest.mark.asyncio
async def test_template_registration_and_execution():
    registry = get_registry()
    registry.clear()

    tmpl = EchoTemplate(
        name="echo_tpl",
        description="Echo via template",
        parameters=[
            ToolParameter(name="text", type="string", description="Text to echo", required=True)
        ],
        metadata={"category": "testing"},
    )

    register_template(tmpl)

    assert registry.has("templates")
    plugin = registry.get("templates")

    tools = plugin.get_tools()
    assert len(tools) == 1
    td = tools[0]
    assert td["name"] == "echo_tpl"
    assert td["type"] == "function"
    assert td["source"] == "template"

    # Execute using await instead of get_event_loop
    result = await plugin.execute("echo_tpl", {"text": "hi"})
    assert result == {"text": "hi"}
