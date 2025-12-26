# `a2a_agent`

- What: Wrap an agent for delegation via A2A client.
- When: Higher-level classifiers/evaluators callable by other agents.
- How:
```python
from orchestrator import a2a_agent

@a2a_agent(name="classifier", version="1.0")
async def classify(text: str) -> dict:
    """Classify text into predefined categories.
    
    Args:
        text: The text to classify
    
    Returns:
        Dictionary with classification label
    """
    return {"label": "electronics"}
```
- Returns: Registered agent callable.
- Links: [A2A Client](../../a2a-client.md), [Parallel Agents](../../../../tutorials/parallel-agents.md)
