# `enable_debug_mode`

- What: Install secrets redactor and enable debug-friendly logging.
- When: Prevent credentials from appearing in logs.
- Example:
```python
from orchestrator import enable_debug_mode
enable_debug_mode()
```
- Links: [Logging](../../logging.md), [Version & Security](../../version-security.md)