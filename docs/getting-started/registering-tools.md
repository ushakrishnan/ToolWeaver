# Registering Tools

You can register tools today using:

- Decorators: `@tool` — simplest path for function-based tools
- Templates: `FunctionToolTemplate`, `MCPToolTemplate`, `CodeExecToolTemplate`, `AgentTemplate`
- Plugin Registry: runtime integration surface for discovery/execution

## Decorator Registration
```python
from orchestrator import tool
from orchestrator.shared.models import ToolParameter

@tool(
	description="Echo text",
	parameters=[ToolParameter(name="text", type="string", description="Text", required=True)],
)
def echo(params):
	return {"text": params["text"]}
```

Runtime: tools decorated are available under the `decorators` plugin.

## Template Registration
```python
from orchestrator import FunctionToolTemplate, register_template
from orchestrator.shared.models import ToolParameter

class EchoTemplate(FunctionToolTemplate):
	def execute(self, params):
		return {"text": params["text"]}

tmpl = EchoTemplate(
	name="echo_tpl",
	description="Echo via template",
	parameters=[ToolParameter(name="text", type="string", description="Text", required=True)],
)
register_template(tmpl)
```

Runtime: templates are exposed via the `templates` plugin.

## Roadmap
- YAML loader (Phase 3)
- Discovery/search APIs (Phase 1.6)
 - A2A client capabilities: Nested `input_schema`/`output_schema` already supported and discoverable via `A2AClient`
