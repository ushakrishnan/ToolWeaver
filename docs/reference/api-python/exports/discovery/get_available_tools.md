# `get_available_tools`

- What: Return all registered tools.
- When: Bootstrap catalogs for planners or REST adapters.
- Example:
```python
from orchestrator import get_available_tools
print(len(get_available_tools()))
```
- Links: [Discovery](../../discovery.md)