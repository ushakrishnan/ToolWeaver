from typing import Any, Dict

from orchestrator import tool, FunctionToolTemplate, register_template
from orchestrator.plugins.registry import get_registry


def test_decorator_supports_nested_input_schema():
    registry = get_registry()
    registry.clear()

    nested_schema = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "profile": {
                        "type": "object",
                        "properties": {
                            "age": {"type": "integer"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["age"],
                    },
                },
                "required": ["id"],
            }
        },
        "required": ["user"],
    }

    @tool(description="Process nested user payload", input_schema=nested_schema)
    def process(params: Dict[str, Any]) -> Dict[str, Any]:
        return params

    plugin = registry.get("decorators")
    tools = plugin.get_tools()
    td = tools[0]
    assert td["name"] == "process"
    assert td["input_schema"] == nested_schema


def test_template_supports_nested_input_schema():
    registry = get_registry()
    registry.clear()

    nested_schema = {
        "type": "object",
        "properties": {
            "order": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {"type": "object", "properties": {"sku": {"type": "string"}}},
                    },
                },
                "required": ["id"],
            }
        },
        "required": ["order"],
    }

    class OrderTemplate(FunctionToolTemplate):
        def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
            return params

    tmpl = OrderTemplate(name="order_process", description="Process order", input_schema=nested_schema)
    register_template(tmpl)

    plugin = registry.get("templates")
    tools = plugin.get_tools()
    td = tools[0]
    assert td["name"] == "order_process"
    assert td["input_schema"] == nested_schema
