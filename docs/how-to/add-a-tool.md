# How to Add a Tool

1) Decorator (fastest)
```python
from orchestrator import mcp_tool

@mcp_tool(domain="finance", description="Sum two amounts")
async def add(amount_a: float, amount_b: float) -> dict:
    """Add two monetary amounts and return their sum."""
    return {"sum": amount_a + amount_b}
```

> Registration note: Decorators auto-register the tool at import time. Simply importing the module that defines the tool will register it.

2) Template class (more control)
```python
from orchestrator import FunctionToolTemplate
from orchestrator.shared.models import ToolParameter
from orchestrator.tools.templates import register_template

class AddTool(FunctionToolTemplate):
    name = "add"
    description = "Sum two amounts"
    parameters = [
        ToolParameter(name="amount_a", type="number", required=True),
        ToolParameter(name="amount_b", type="number", required=True),
    ]

    async def run(self, amount_a: float, amount_b: float) -> dict:
        return {"sum": amount_a + amount_b}

# Register explicitly when ready (keep imports side-effect free)
if __name__ == "__main__":
    register_template(AddTool())
    # Optional: verify registration
    from orchestrator import search_tools
    print(search_tools(domain="finance"))
```

> Registration note: Template-based tools do **not** auto-register. Call `register_template(AddTool())` when you are ready (e.g., in `main` or app startup) to add it to the catalog.

3) YAML (config-driven)
```yaml
# add.yaml
tools:
  - name: add
    type: function
    description: "Sum two amounts"
    provider: python
    worker: "builtins:sum"
    parameters:
      - name: amount_a
        type: number
        description: "First amount"
        required: true
      - name: amount_b
        type: number
        description: "Second amount"
        required: true
```
Load YAML:
```python
from orchestrator import load_tools_from_yaml
load_tools_from_yaml("add.yaml")
```

> Registration note: YAML tools register when `load_tools_from_yaml(...)` is called. If you want to keep imports side-effect free, invoke this during app startup or in `main`, not at module import.

Check catalog:
```python
from orchestrator import search_tools
print(search_tools(domain="finance"))
```

Full demo: [samples/23-adding-new-tools/three_ways.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/23-adding-new-tools/three_ways.py)
