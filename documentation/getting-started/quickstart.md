# Quickstart (Package Users)

1. Install: `pip install toolweaver`
2. Configure env vars if needed: `TOOLWEAVER_SKILL_PATH`, `TOOLWEAVER_LOG_LEVEL`.
3. Define a tool with the `@tool` decorator (available now):
```python
from typing import Any, Dict
from orchestrator import tool
from orchestrator.shared.models import ToolParameter

@tool(
    description="Echo the provided text",
    parameters=[ToolParameter(name="text", type="string", description="Text to echo", required=True)],
)
def echo(params: Dict[str, Any]) -> Dict[str, Any]:
    return {"text": params["text"]}
```
4. Execute via the plugin registry:
```python
from orchestrator.plugins.registry import get_registry
import asyncio

registry = get_registry()
plugin = registry.get("decorators")
result = asyncio.get_event_loop().run_until_complete(plugin.execute("echo", {"text": "hello"}))
print(result)  # {"text": "hello"}
```
5. Alternatively, use templates (Phase 1):
```python
from orchestrator import FunctionToolTemplate, register_template
from orchestrator.shared.models import ToolParameter

class EchoTemplate(FunctionToolTemplate):
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"text": params["text"]}

tmpl = EchoTemplate(
    name="echo_tpl",
    description="Echo via template",
    parameters=[ToolParameter(name="text", type="string", description="Text to echo", required=True)],
)
register_template(tmpl)
```

> Decorators and templates are available now. Discovery/search APIs will land in Phase 1.6.

### Nested JSON (MCP-ready)
You can define nested input schemas for complex payloads (e.g., MCP tools):
```python
from orchestrator import tool

nested_schema = {
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "profile": {
                    "type": "object",
                    "properties": {"age": {"type": "integer"}},
                    "required": ["age"],
                },
            },
            "required": ["id"],
        }
    },
    "required": ["user"],
}

@tool(description="Process user", input_schema=nested_schema)
def process(params):
    return params
```
Tools registered via decorators/templates will surface `input_schema` and `output_schema` in plugin discovery.

### A2A (Agent-to-Agent) schemas
External agents registered via the A2A client can also declare nested schemas:
```python
from orchestrator.infra.a2a_client import A2AClient, AgentCapability

client = A2AClient()
cap = AgentCapability(
    name="chat_agent",
    description="Handles chat",
    agent_id="agent-1",
    endpoint="http://localhost:9999/agent",
    protocol="http",
    input_schema={"type":"object","properties":{"session":{"type":"object"}}},
    output_schema={"type":"object","properties":{"result":{"type":"object"}}},
)
client.register_agent(cap)
```
Then discover agents and inspect their schemas via `discover_agents()`.
