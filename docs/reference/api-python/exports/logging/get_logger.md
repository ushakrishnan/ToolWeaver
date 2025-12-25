# `get_logger`

- What: Get a module-specific logger.
- When: Emit logs with secrets-safe behavior.
- Example:
```python
from orchestrator import get_logger
logger = get_logger(__name__)
logger.info("hello")
```
- Links: [Logging](../../logging.md)