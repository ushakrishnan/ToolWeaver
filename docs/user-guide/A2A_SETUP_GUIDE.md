# Agent-to-Agent (A2A) Protocol Setup Guide

**Document Version:** 1.0  
**Date:** December 18, 2025  
**Status:** Production Ready ✅

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Agent Discovery](#agent-discovery)
5. [Task Delegation](#task-delegation)
6. [Streaming Responses](#streaming-responses)
7. [Error Handling & Resilience](#error-handling--resilience)
8. [Cost Tracking](#cost-tracking)
9. [Monitoring & Observability](#monitoring--observability)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The A2A (Agent-to-Agent) protocol enables ToolWeaver to discover, communicate with, and delegate tasks to external agents. While **MCP focuses on tool discovery and execution**, **A2A focuses on agent discovery and coordination**.

### MCP vs. A2A at a Glance

| Aspect | MCP Tools | A2A Agents |
|--------|-----------|-----------|
| **Discovery** | Automatic from MCP manifest | Configured in agents.yaml |
| **Execution** | Deterministic, local/nearby | Delegated to external service |
| **Latency** | Low (ms) | Higher (100-1000ms) |
| **Cost** | Free/minimal | Per-invocation ($0.01-$1.00) |
| **State** | Stateless | Can be stateful |
| **Complexity** | Moderate | High (ML/AI intensive) |
| **Parallelization** | Fast async | Slower (network bound) |

### When to Use A2A Agents

✅ **Good fit:**
- Complex analysis requiring ML/AI (data analysis, sentiment analysis)
- Specialized domains (legal, medical, financial)
- Heavy computation (simulations, modeling)
- Custom business logic (internal microservices)

❌ **Not ideal:**
- Simple transformations (use MCP tools instead)
- Real-time critical operations (<10ms)
- Cost-sensitive operations (use MCP tools)

---

## Quick Start

### 1. Create agents.yaml

```yaml
a2a:
  enabled: true
  default_timeout: 300

agents:
  - agent_id: data_analyst
    name: Data Analysis Agent
    description: Analyzes datasets and generates insights
    endpoint: http://localhost:8001/analyze
    protocol: http
    capabilities:
      - data_analysis
      - statistical_modeling
    cost_estimate: 0.05
    latency_estimate: 120
```

### 2. Initialize A2A Client

```python
from orchestrator.infra.a2a_client import A2AClient

# With config file
async with A2AClient(config_path="agents.yaml") as client:
    agents = await client.discover_agents()
    print(f"Found {len(agents)} agents")
```

### 3. Delegate a Task

```python
from orchestrator.infra.a2a_client import AgentDelegationRequest

request = AgentDelegationRequest(
    agent_id="data_analyst",
    task="Analyze customer churn patterns",
    context={"dataset": data},
    timeout=120,
    idempotency_key="analysis_001"
)

response = await client.delegate_to_agent(request)
if response.success:
    print(f"Analysis complete: {response.result}")
```

---

## Configuration

### agents.yaml Schema

```yaml
a2a:
  enabled: bool                    # Enable/disable A2A
  registry_url: str?              # Optional: A2A registry endpoint
  default_timeout: int            # Default timeout in seconds

agents:
  - agent_id: str                 # Unique agent identifier
    name: str                      # Human-readable name
    description: str              # What the agent does
    endpoint: str                 # API endpoint (with ${VAR} support)
    protocol: enum                # "http", "sse", "websocket"
    capabilities: list[str]       # ["data_analysis", "forecasting"]
    input_schema: object?         # JSON Schema for inputs
    output_schema: object?        # JSON Schema for outputs
    cost_estimate: float?         # USD per invocation
    latency_estimate: int?        # P95 latency in seconds
    metadata:
      tags: list[str]?           # ["production", "critical"]
      version: str?              # Agent version
      auth:                       # Optional authentication
        type: enum               # "bearer", "api_key"
        token_env: str          # Environment variable name
        header: str?            # Custom header name (default: Authorization)
```

### Environment Variable Expansion

All fields support `${VAR}` expansion:

```yaml
agents:
  - agent_id: secure_agent
    endpoint: ${AGENT_ENDPOINT}    # Expands from os.environ
    metadata:
      auth:
        type: bearer
        token_env: AGENT_API_KEY   # Uses os.getenv("AGENT_API_KEY")
```

**Example:**
```bash
export AGENT_ENDPOINT=https://agent.example.com/api
export AGENT_API_KEY=sk-agent-xyz123
python my_script.py
```

---

## Agent Discovery

### Discover All Agents

```python
agents = await client.discover_agents()
for agent in agents:
    print(f"- {agent.name}: {agent.description}")
```

### Filter by Capability

```python
# Find agents that do data analysis
analysts = await client.discover_agents(capability="data_analysis")
```

### Filter by Tags

```python
# Find critical production agents
critical = await client.discover_agents(tags=["critical"])
```

### Discovery Caching

```python
# Use cached results (default: 5 min TTL)
agents = await client.discover_agents(
    use_cache=True,
    cache_ttl_s=300
)

# Force fresh discovery
agents = await client.discover_agents(use_cache=False)

# Clear cache manually
client.invalidate_discovery_cache()
```

---

## Task Delegation

### Basic Delegation

```python
request = AgentDelegationRequest(
    agent_id="data_analyst",
    task="Analyze revenue trends",
    context={"data": revenue_data},
    timeout=120
)

response = await client.delegate_to_agent(request)
```

### Idempotent Operations

Prevent duplicate expensive operations with idempotency keys:

```python
request = AgentDelegationRequest(
    agent_id="expensive_agent",
    task="Complex simulation",
    context={...},
    idempotency_key="simulation_batch_001"  # Same key = cached result
)

# First call: runs simulation
response1 = await client.delegate_to_agent(request)

# Second call: returns cached result (for 10 minutes)
response2 = await client.delegate_to_agent(request)

assert response1.result == response2.result
```

### With Metadata

```python
request = AgentDelegationRequest(
    agent_id="agent_1",
    task="analyze",
    context={...},
    idempotency_key="req_001",
    metadata={
        "priority": "high",
        "customer_id": "cust_123",
        "request_id": "req_001"
    }
)
```

---

## Streaming Responses

Handle long-running operations with streaming:

### Stream Example

```python
request = AgentDelegationRequest(
    agent_id="streaming_agent",
    task="Process large dataset",
    context={"dataset": large_data}
)

chunks = []
async for chunk in client.delegate_stream(
    request,
    chunk_timeout=5.0  # Timeout per chunk
):
    chunks.append(chunk)
    print(f"Received: {chunk}")

result = {"chunks": chunks}
```

### Streaming Protocols

```yaml
agents:
  # HTTP chunked transfer
  - agent_id: http_stream
    protocol: http
    endpoint: http://agent:8000/stream

  # Server-Sent Events
  - agent_id: sse_stream
    protocol: sse
    endpoint: http://agent:8000/events

  # WebSocket
  - agent_id: ws_stream
    protocol: websocket
    endpoint: ws://agent:8000/stream
```

---

## Error Handling & Resilience

### Automatic Retries

Built-in retry logic with exponential backoff:

```python
# Configure retries when creating client
client = A2AClient(
    config_path="agents.yaml",
    max_retries=3,              # Up to 3 retries
    retry_backoff_s=0.1,        # Start at 100ms backoff
)

# Response includes retry metadata
response = await client.delegate_to_agent(request)
print(f"Attempts: {response.metadata['attempt']}")
```

### Circuit Breaker Pattern

Prevents cascading failures:

```python
client = A2AClient(
    config_path="agents.yaml",
    circuit_breaker_threshold=3,    # Open after 3 failures
    circuit_reset_s=30              # Reset after 30 seconds
)

try:
    response = await client.delegate_to_agent(request)
except RuntimeError as e:
    if "circuit" in str(e):
        print("Agent service temporarily unavailable")
        # Fallback to alternative agent or tool
```

### Timeout Handling

```python
request = AgentDelegationRequest(
    agent_id="slow_agent",
    task="Long computation",
    context={...},
    timeout=300  # 5 minute timeout
)

try:
    response = await client.delegate_to_agent(request)
except asyncio.TimeoutError:
    print("Agent request timed out")
    # Fallback logic
```

---

## Cost Tracking

### Per-Invocation Cost

```python
response = await client.delegate_to_agent(request)

if response.cost:
    print(f"Cost: ${response.cost:.4f}")

# Aggregate costs across multiple operations
total_cost = sum(r.cost or 0.0 for r in responses)
```

### Cost-Aware Selection

```python
budget = 1.00  # $1.00 budget
agents = await client.discover_agents()

# Filter by cost
affordable = [
    a for a in agents
    if (a.cost_estimate or 0) < budget
]

# Or select cheapest
cheapest = min(agents, key=lambda a: a.cost_estimate or 0)
```

### Cost Estimation

```yaml
agents:
  - agent_id: expensive
    cost_estimate: 0.50          # $0.50 per invocation
    latency_estimate: 120        # 2 minutes

  - agent_id: cheap
    cost_estimate: 0.01          # $0.01 per invocation
    latency_estimate: 5          # 5 seconds
```

---

## Monitoring & Observability

### Observer Events

Hook into delegation lifecycle:

```python
def on_event(event_name: str, data: dict):
    print(f"{event_name}: {data}")

client = A2AClient(
    config_path="agents.yaml",
    observer=on_event
)

# Events emitted:
# - a2a.start: Delegation started
# - a2a.complete: Delegation complete (success or failure)
# - a2a.cache_hit: Idempotency cache hit
# - a2a.stream.start: Streaming started
# - a2a.stream.chunk: Chunk received
# - a2a.stream.complete: Streaming complete
```

### Structured Logging

```python
from orchestrator.observability.monitoring import ToolUsageMonitor

monitor = ToolUsageMonitor(backends=["local"])

# Log agent delegation
monitor.log_tool_call(
    tool_name="agent_data_analyst",
    success=True,
    latency=45.2,
    execution_id="req_001"
)

# Query logs
logs = monitor.get_logs(tool_name="agent_data_analyst")
```

---

## Best Practices

### 1. Use Idempotency Keys

```python
# ✅ Good: Unique, deterministic keys
idempotency_key = f"task_{task_id}_{date}"

# ❌ Bad: Random/non-deterministic
idempotency_key = str(uuid.uuid4())
```

### 2. Set Appropriate Timeouts

```python
# Based on agent's latency_estimate
if agent.latency_estimate:
    timeout = agent.latency_estimate * 1.5  # 50% buffer
else:
    timeout = 300  # Safe default
```

### 3. Implement Fallbacks

```python
try:
    response = await client.delegate_to_agent(request)
except Exception as e:
    # Try alternative agent
    request.agent_id = "backup_agent"
    response = await client.delegate_to_agent(request)
```

### 4. Filter Agents by Capability

```python
# Instead of hardcoding agent_id
request.agent_id = "agent_123"

# Use capability-based selection
agents = await client.discover_agents(capability="sentiment_analysis")
if agents:
    request.agent_id = agents[0].agent_id
```

### 5. Monitor Costs

```python
costs = []
for request in requests:
    response = await client.delegate_to_agent(request)
    costs.append(response.cost or 0.0)

total = sum(costs)
if total > budget:
    alert(f"Cost exceeded: ${total:.2f} > ${budget:.2f}")
```

---

## Troubleshooting

### Agent Not Found

**Error:** `ValueError: Agent agent_1 not found`

**Solutions:**
1. Check agent_id matches config
2. Verify agents.yaml is loaded: `client.list_agents()`
3. Check environment variables are expanded: `print(agent.endpoint)`

### Connection Refused

**Error:** `ClientError: Cannot connect to agent endpoint`

**Solutions:**
1. Verify endpoint is correct: `ping endpoint_host`
2. Check agent service is running
3. Verify firewall allows connection
4. Test with curl: `curl -X POST http://endpoint/path`

### Timeout

**Error:** `asyncio.TimeoutError: Agent agent_1 timed out`

**Solutions:**
1. Increase timeout: `timeout=600`
2. Check agent service performance
3. Reduce payload size (context data)
4. Use streaming for large responses

### Idempotency Not Working

**Error:** Different results for same request

**Solutions:**
1. Check idempotency_key is set and identical
2. Verify cache TTL hasn't expired: `idempotency_ttl_s=3600`
3. Disable cache to diagnose: `use_cache=False`

### Cost Estimate Mismatch

**Issue:** Actual cost differs from estimate

**Solution:**
```yaml
agents:
  - agent_id: agent_1
    cost_estimate: 0.10          # Update based on actual usage
    metadata:
      cost_range: [0.05, 0.15]  # Min-max range
```

---

## Integration with MCP

A2A agents work seamlessly with MCP tools in unified workflows:

```python
# Both tools (MCP) and agents (A2A) in same workflow
from orchestrator.tools.tool_discovery import discover_tools
from orchestrator.runtime.orchestrator import run_step

# Step 1: MCP tool (deterministic)
tool_step = {
    "tool": "fetch_csv",
    "input": {"file": "data.csv"}
}
data = await run_step(tool_step, {}, mcp_client, a2a_client=client)

# Step 2: A2A agent (intelligent)
agent_step = {
    "type": "agent",
    "agent_id": "data_analyst",
    "task": "Analyze data",
    "inputs": ["fetch_csv"]  # Reference tool output
}
analysis = await run_step(agent_step, outputs, mcp_client, a2a_client=client)

# Benefits:
# - Tools for deterministic operations (faster, cheaper)
# - Agents for complex analysis (flexible, powerful)
# - Combined: Cost-effective yet intelligent
```

See [FEATURES_GUIDE.md](FEATURES_GUIDE.md) for integrated tool + agent examples.

---

## Next Steps

- [Examples](../examples/16-agent-delegation/) - Runnable examples
- [FEATURES_GUIDE.md](FEATURES_GUIDE.md) - Full capabilities overview
- [WORKFLOW_USAGE_GUIDE.md](WORKFLOW_USAGE_GUIDE.md) - Compose workflows
