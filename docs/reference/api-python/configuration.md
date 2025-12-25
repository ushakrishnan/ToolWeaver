# Configuration

Why: Control runtime behavior via environment variables and defaults.
Jump to symbols: [API Exports Index](exports/index.md)

Exports: `get_config`, `reset_config`, `validate_config`

---

## Typical fields
- Cache path: local cache directory
- Redis URL: distributed cache endpoint (optional)
- Skill path: location for skill packages
- Logging level: default log verbosity

## Read config
What: Fetch current runtime configuration.
When: Inspect defaults or confirm environment overrides.
```python
from orchestrator import get_config
cfg = get_config()
print(cfg)
```

## Validate
What: Validate configuration values and surface warnings/errors.
When: CI checks or startup validation.
```python
from orchestrator import validate_config
print(validate_config())
```

## Reset
What: Clear cached configuration state.
When: After changing env vars or during tests to ensure fresh loads.
```python
from orchestrator import reset_config
reset_config()
```

Related:
- Reference: [Configuration](../config.md)