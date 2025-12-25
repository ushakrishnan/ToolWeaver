# `FunctionToolTemplate`

- What: Define function-style tools with explicit schema.
- When: Need strong parameter control or validation.
- Example:
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
- Links: [Templates](../../templates.md), [Samples](../../../../samples/index.md)
