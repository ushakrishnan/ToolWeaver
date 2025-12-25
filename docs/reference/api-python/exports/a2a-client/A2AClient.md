# `A2AClient`

- What: Client to delegate requests to agents.
- When: Compose agent networks.
- Example:
```python
from orchestrator import A2AClient, AgentCapability, AgentDelegationRequest
client = A2AClient()
cap = AgentCapability(name="classifier", version="1.0")
req = AgentDelegationRequest(capability=cap, payload={"text": "Buy laptop"})
resp = await client.delegate(req)
print(resp)
```
- Links: [A2A Client](../../a2a-client.md)