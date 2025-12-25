# Plugin Extension

Shows how to register a simple plugin that provides tools, then list and execute them via the registry.

## Run
```bash
python samples/31-plugin-extension/plugin_demo.py
```

## Prerequisites
- Install from PyPI:
```bash
pip install toolweaver
```

## What it shows
- Define a minimal plugin class implementing `get_tools()` and `execute()`
- Register the plugin via `register_plugin()`
- List plugins and tools; execute a tool by name
