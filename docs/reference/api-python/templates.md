# Template Classes & Registration

Why: Maximum control over tool definitions, metadata, validation, and execution lifecycle.
Jump to symbols: [API Exports Index](exports/index.md)

Exports: `BaseTemplate`, `FunctionToolTemplate`, `MCPToolTemplate`, `CodeExecToolTemplate`, `AgentTemplate`, `register_template`

---

## `BaseTemplate`
- What: Abstract base for all tool templates.
- When: Subclass to build custom behaviors beyond built-ins.
- How: Define `name`, `description`, `parameters`, and `run()`.

---

## `FunctionToolTemplate`
- What: Define function-style tools with explicit schema.
- When: Prefer when you need strong schema control or custom validation.
- How: Set `parameters` with `ToolParameter` entries; implement `run()`.

Example:
```python
from orchestrator import FunctionToolTemplate
from orchestrator.shared.models import ToolParameter

class AddTool(FunctionToolTemplate):
    name = "add"
    description = "Sum two numbers"
    parameters = [
        ToolParameter(name="a", type="number", required=True),
        ToolParameter(name="b", type="number", required=True),
    ]
    async def run(self, a: float, b: float) -> dict:
        return {"sum": a + b}
```

---

## `MCPToolTemplate`
- What: MCP-flavored template with richer discovery metadata.
- When: Use when exposing tools to MCP-based planners/adapters.

---

## `CodeExecToolTemplate`
- What: Tools that execute user-provided code with sandbox controls.
- When: Use for safe code execution tasks; pairs with sandbox features.

---

## `AgentTemplate`
- What: Define agent-style tools (evaluators, classifiers, planners).
- When: Provide consistent schema and lifecycle around agent calls.

---

## `register_template()`
- What: Add a custom template to the registry.
- When: Make your custom template discoverable for use.
- How: Call with your class reference.

```python
from orchestrator import register_template
register_template(AddTool)
```

Related:
- Sample: [samples/23-adding-new-tools/three_ways.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/23-adding-new-tools/three_ways.py)