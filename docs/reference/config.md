# Configuration

Use `get_config()` to read runtime settings and environment overrides.

Common env vars:
- `REDIS_URL`: Redis connection for cache (optional; file cache is fallback).
- `TOOLWEAVER_CACHE_PATH`: Override local cache directory.
- Provider credentials: set per tool (e.g., Azure/OpenAI keys) as needed.

Validate config:
```python
from orchestrator import validate_config
print(validate_config())
```

Reset cached config:
```python
from orchestrator import reset_config
reset_config()
```
