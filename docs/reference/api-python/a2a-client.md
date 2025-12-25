# Agent-to-Agent Client (A2A)

Why: Delegate work to other agents securely and compose agent networks.
Jump to symbols: [API Exports Index](exports/index.md)

Exports: `AgentCapability`, `AgentDelegationRequest`, `AgentDelegationResponse`, `A2AClient`

---

## Concepts
- Capability: a named function an agent can perform (e.g., `classifier`)
- Delegation request: payload and desired capability
- Response: result and metadata

## Example
What: Delegate a request to another agent via `A2AClient`.
When: Compose multi-agent workflows or offload specialized tasks.
```python
from orchestrator import AgentCapability, AgentDelegationRequest, A2AClient

client = A2AClient()
cap = AgentCapability(name="classifier", version="1.0")
req = AgentDelegationRequest(capability=cap, payload={"text": "Buy laptop"})
resp = await client.delegate(req)
print(resp)
```

Related:
- Tutorial: [Parallel Agents](../../tutorials/parallel-agents.md)