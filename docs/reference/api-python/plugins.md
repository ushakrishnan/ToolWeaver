# Plugins

Why: Extend ToolWeaver with third-party integrations, additional discovery sources, or custom behaviors.
Jump to symbols: [API Exports Index](exports/index.md)

Exports: `register_plugin`, `unregister_plugin`, `get_plugin`, `list_plugins`, `discover_plugins`

---

## Lifecycle
- Register: `register_plugin(name, instance)`
- Discover: `discover_plugins()` (optional scanning)
- Get: `get_plugin(name)`
- List: `list_plugins()`
- Unregister: `unregister_plugin(name)`

## Register a plugin
What: Add a plugin instance to the registry.
When: Enable a custom integration or discovery source.
```python
from orchestrator import register_plugin

class MyPlugin:
    def setup(self):
        print("hello from plugin")

register_plugin("my_plugin", MyPlugin())
```

## Discover & list
What: Auto-scan for discoverable plugins and enumerate them.
When: Bootstrap plugins without manual registration or audit what is loaded.
```python
from orchestrator import discover_plugins, list_plugins
discover_plugins()
print(list_plugins())
```

Related:
- Concepts: [Overview](../../concepts/overview.md)