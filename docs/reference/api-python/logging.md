# Logging Helpers

Why: Enable observability and safe logging.
Jump to symbols: [API Exports Index](exports/index.md)

Exports: `get_logger`, `set_log_level`, `enable_debug_mode`

---

## Safe logging
- `enable_debug_mode()` installs a secrets redactor on the root logger to prevent token leakage.
- Use `set_log_level("INFO")` to control verbosity globally.

## Usage
What: Configure logging with safe defaults.
When: Set module logger, adjust verbosity, and install redaction before emitting logs.
```python
from orchestrator import get_logger, set_log_level, enable_debug_mode

logger = get_logger(__name__)
set_log_level("INFO")

enable_debug_mode()
logger.info("hello")
```

Related:
- Concepts: [Overview](../../concepts/overview.md)