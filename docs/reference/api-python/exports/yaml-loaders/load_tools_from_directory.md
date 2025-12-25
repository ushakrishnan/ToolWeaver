# `load_tools_from_directory`

- What: Load tool definitions from a directory of YAML files.
- When: Bulk registration.
- Example:
```python
from orchestrator import load_tools_from_directory
load_tools_from_directory("./tools_yaml")
```
- Errors: `YAMLLoaderError`, `YAMLValidationError`, `WorkerResolutionError`
- Links: [YAML Loaders](../../yaml-loaders.md)