# `load_tools_from_yaml`

- What: Load tool definitions from a YAML file.
- When: Config-driven registration.
- Example:
```python
from orchestrator import load_tools_from_yaml
load_tools_from_yaml("add.yaml")
```
- Errors: `YAMLLoaderError`, `YAMLValidationError`
- Links: [YAML Loaders](../../yaml-loaders.md)