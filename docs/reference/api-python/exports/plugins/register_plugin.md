# `register_plugin`

- What: Register a plugin instance.
- When: Extend ToolWeaver with new behaviors or sources.
- Example:
```python
from orchestrator import register_plugin
class MyPlugin:
    def setup(self):
        print("hello")
register_plugin("my_plugin", MyPlugin())
```
- Links: [Plugins](../../plugins.md)