# `search_tools`

- What: Filter tools by domain/keywords.
- When: Narrow selection for a task.
- Example:
```python
from orchestrator import search_tools
print([t.name for t in search_tools(domain="github")])
```
- Links: [Discovery](../../discovery.md)