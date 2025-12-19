# Plugin Registry

- Register at runtime:
```python
from orchestrator.plugins import register_plugin
from my_package.tools import MyPlugin

register_plugin("my-tools", MyPlugin())
```
- Optional: declare entry points for auto-discovery.
- Plugins must implement `get_tools()` and `execute(tool_name, params)`.
- Keep optional deps in your package extras; core stays lean.
