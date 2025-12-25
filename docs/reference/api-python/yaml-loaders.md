# YAML Loaders

Why: Configuration-driven registration for repeatable deployments and non-Python authorship.
Jump to symbols: [API Exports Index](exports/index.md)

Exports: `load_tools_from_yaml`, `load_tools_from_directory`, `YAMLLoaderError`, `YAMLValidationError`, `WorkerResolutionError`

---

## Schema (example)
```yaml
name: add
description: Sum two numbers
provider: python
parameters:
  - name: a
    type: number
    required: true
  - name: b
    type: number
    required: true
metadata:
  domain: finance
```

Load a single file:
What: Register one YAML-defined tool.
When: You have a single definition to load or test.
```python
from orchestrator import load_tools_from_yaml
load_tools_from_yaml("add.yaml")
```

Load a directory:
What: Bulk-load multiple YAML tool definitions.
When: Deploy or refresh a set of tools from config.
```python
from orchestrator import load_tools_from_directory
load_tools_from_directory("./tools_yaml")
```

Errors:
- `YAMLLoaderError`: General load failure (file not found, parse error)
- `YAMLValidationError`: Schema invalid (missing fields, wrong types)
- `WorkerResolutionError`: Referenced worker/tool backend cannot be resolved

Related:
- Sample: [samples/23-adding-new-tools/three_ways.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/23-adding-new-tools/three_ways.py)