# `tool`

- What: Register a generic tool from a Python function.
- When: Quick utilities and internal helpers.
- How:
```python
from orchestrator import tool

@tool(domain="demo")
async def echo(message: str) -> dict:
    """Echo back the provided message.
    
    Args:
        message: The message to echo back
    
    Returns:
        Dictionary with the echoed message
    """
    return {"echo": message}
```
- Returns: Registered tool callable.
- Links: [Decorators](../../decorators.md), [Samples](../../../../samples/index.md)
