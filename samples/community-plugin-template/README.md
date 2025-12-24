# Community Plugin Template

This example shows how to ship a ToolWeaver plugin as a separate package.

## Structure
```
community-plugin-template/
  README.md
  example_plugin/
    __init__.py
    tools.py
```

## Usage
```python
from orchestrator.plugins import register_plugin
from example_plugin.tools import ExamplePlugin

register_plugin("community-example", ExamplePlugin())
```

Optionally declare an entry point in your package metadata so it can be auto-discovered:
```toml
[project.entry-points."toolweaver.plugins"]
community_example = "example_plugin.tools:ExamplePlugin"
```

Keep your optional dependencies in your package extras; core ToolWeaver stays lean.
