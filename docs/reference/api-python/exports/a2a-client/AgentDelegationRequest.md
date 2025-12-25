# `AgentDelegationRequest`

- What: Request payload to delegate to an agent.
- When: Invoke capabilities with inputs.
- Example:
```python
from orchestrator import AgentDelegationRequest, AgentCapability
cap = AgentCapability(name="classifier", version="1.0")
req = AgentDelegationRequest(capability=cap, payload={"text": "Buy laptop"})
```
- Links: [A2A Client](../../a2a-client.md)