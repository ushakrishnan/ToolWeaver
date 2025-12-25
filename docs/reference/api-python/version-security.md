# Version & Security

Why: Understand package version and built-in safety features.
Jump to symbols: [API Exports Index](exports/index.md)

Exports:
- `__version__`: package version string
- Auto-installed secrets redactor: prevents credentials from appearing in logs

## Usage
```python
import orchestrator
print(orchestrator.__version__)
```

Security:
- On import, a secrets redactor is installed on the root logger.
- Combine with `enable_debug_mode()` for consistent safe logging.

Related:
- Concepts: [Overview](../../concepts/overview.md)