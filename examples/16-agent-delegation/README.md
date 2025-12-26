# Example 16: Basic Agent Delegation

This example demonstrates how to delegate tasks to external agents using the A2A (Agent-to-Agent) protocol.

## Setup

1. Create or configure `agents.yaml` with agent endpoints:
   ```yaml
   agents:
     - agent_id: data_analyst
       name: Data Analyst Agent
       description: Analyzes data and provides insights
       endpoint: http://localhost:8001/analyze
       protocol: http
       capabilities:
         - data_analysis
         - statistical_modeling
   ```

2. Set environment variable (optional):
   ```bash
   export AGENTS_CONFIG=./agents.yaml
   ```

## Key Concepts

- **Agent Discovery**: Use A2A client to discover available agents
- **Task Delegation**: Delegate tasks with context and idempotency keys
- **Error Handling**: Retries with exponential backoff on failures
- **Streaming Support**: Stream responses from agents
- **Observability**: Track delegation latency and costs

## Differences from MCP Tools

| Aspect | MCP Tools | A2A Agents |
|--------|-----------|-----------|
| **Execution** | Deterministic, sandboxed | Delegated to external service |
| **Latency** | Lower (local/nearby) | Higher (network dependent) |
| **Cost** | Free/minimal | Per-invocation cost |
| **State** | Stateless | Can be stateful |
| **Discovery** | Automatic from MCP manifest | Configured in agents.yaml |

## Best Practices

1. **Use idempotency keys for expensive operations** to prevent duplicate work
2. **Set appropriate timeouts** based on agent SLA
3. **Implement fallbacks** to alternative agents or tools
4. **Monitor agent costs** to optimize budget allocation
5. **Cache discovery results** to reduce startup overhead

## Files

- `delegate_to_agent.py` - Basic delegation example
- `discover_agents.py` - Agent discovery example
- `agents.yaml` - Agent configuration

## Running

```bash
python delegate_to_agent.py
```
