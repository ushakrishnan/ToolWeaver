# Extending ToolWeaver

Preferred path: publish a separate package and register via the plugin registry.

Minimal pattern:
```python
from orchestrator.plugins import register_plugin
from my_package.tools import MyPlugin

register_plugin("my-tools", MyPlugin())
```

Add an entry point for auto-discovery:
```toml
[project.entry-points."toolweaver.plugins"]
my_tools = "my_package.tools:MyPlugin"
```

Ship your own extras for optional deps; keep core installs lean.
