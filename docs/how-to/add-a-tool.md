# How to Add a Tool

1) Decorator (fastest)
```python
from orchestrator import mcp_tool

@mcp_tool(domain="finance", description="Sum two amounts")
async def add(amount_a: float, amount_b: float) -> dict:
    return {"sum": amount_a + amount_b}
```

2) Template class (more control)
```python
from orchestrator import FunctionToolTemplate
from orchestrator.shared.models import ToolParameter

class AddTool(FunctionToolTemplate):
    name = "add"
    description = "Sum two amounts"
    parameters = [
        ToolParameter(name="amount_a", type="number", required=True),
        ToolParameter(name="amount_b", type="number", required=True),
    ]

    async def run(self, amount_a: float, amount_b: float) -> dict:
        return {"sum": amount_a + amount_b}
```

3) YAML (config-driven)
```yaml
# add.yaml
name: add
provider: python
parameters:
  - name: amount_a
    type: number
    required: true
  - name: amount_b
    type: number
    required: true
```
Load YAML:
```python
from orchestrator import load_tools_from_yaml
load_tools_from_yaml("add.yaml")
```

Check catalog:
```python
from orchestrator import search_tools
print(search_tools(domain="finance"))
```

Full demo: [samples/23-adding-new-tools/three_ways.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/23-adding-new-tools/three_ways.py)
