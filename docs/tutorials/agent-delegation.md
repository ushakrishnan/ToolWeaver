# Agent Delegation Tutorial

Learn when and how to delegate tasks to external agents using the A2A (Agent-to-Agent) protocol, and when to use local MCP tools instead.

## What You'll Learn

By the end of this tutorial, you'll understand:

- **A2A vs MCP**: When to delegate vs when to execute locally
- **Agent discovery**: Finding available agents and their capabilities
- **Delegation patterns**: Streaming, batch, consensus
- **Configuration**: Setting up `agents.yaml`
- **Best practices**: Idempotency, timeouts, fallbacks

## Prerequisites

- Basic understanding of [ToolWeaver orchestration](../get-started/quickstart.md)
- Familiarity with [agent architecture](../concepts/agents.md)

## The Delegation Decision

**Core Question:** Should I use an external agent or a local tool?

### Use A2A Agents When:

| Scenario | Why A2A | Example |
|----------|---------|---------|
| **Non-deterministic** | Requires reasoning/judgment | "Summarize this report from a CFO's perspective" |
| **Specialized expertise** | Agent has domain knowledge | Legal document analysis |
| **Stateful workflows** | Agent maintains context | Multi-turn conversation with user |
| **Resource-intensive** | Agent has GPU/large model | Video processing, ML training |
| **Third-party service** | External API/system | CRM updates, payment processing |

### Use MCP Tools When:

| Scenario | Why MCP | Example |
|----------|---------|---------|
| **Deterministic** | Fixed logic/calculation | Format date, parse JSON |
| **Local/fast** | No network overhead | File read, regex match |
| **Sandboxed** | Security/isolation required | Code execution in container |
| **Free** | No per-invocation cost | String manipulation |
| **Synchronous** | Immediate response needed | Validation, type checking |

---

## Core Concepts

### 1. Agent Discovery

**Purpose:** Find available agents and their capabilities at runtime.

```python
from orchestrator.a2a.client import A2AClient

client = A2AClient(config_path="agents.yaml")

# Discover all agents
agents = await client.discover_agents()

for agent in agents:
    print(f"Agent: {agent.name}")
    print(f"  ID: {agent.agent_id}")
    print(f"  Capabilities: {agent.capabilities}")
    print(f"  Cost: ${agent.cost_estimate}")
    print(f"  Latency: ~{agent.latency_estimate}s")
```

**Output:**
```
Agent: Data Analysis Agent
  ID: data_analyst
  Capabilities: ['data_analysis', 'statistical_modeling', 'visualization']
  Cost: $0.05
  Latency: ~120s

Agent: Code Generation Agent
  ID: code_generator
  Capabilities: ['code_generation', 'testing']
  Cost: $0.10
  Latency: ~60s
```

### 2. Task Delegation

**Purpose:** Send task to external agent with context and track results.

```python
# Delegate task to data analyst agent
result = await client.delegate(
    agent_id="data_analyst",
    request={
        "dataset": "sales_2024.csv",
        "metrics": ["revenue", "growth_rate", "top_customers"]
    },
    idempotency_key="sales-analysis-2024-q1",  # Prevent duplicate work
    timeout=300  # 5 minutes
)

print(result)
```

### 3. Streaming Responses

**Purpose:** Get incremental results for long-running tasks.

```python
async for chunk in client.delegate_streaming(
    agent_id="code_generator",
    request={"specification": "REST API for user management"}
):
    print(chunk, end="", flush=True)
```

---

## Configuration: agents.yaml

### Basic Structure

```yaml
a2a:
  enabled: true
  default_timeout: 300  # 5 minutes

agents:
  - agent_id: data_analyst
    name: Data Analysis Agent
    description: Analyzes datasets and provides insights
    endpoint: http://localhost:8001/analyze
    protocol: http
    capabilities:
      - data_analysis
      - statistical_modeling
    input_schema:
      type: object
      properties:
        dataset:
          type: string
        metrics:
          type: array
      required: [dataset]
    cost_estimate: 0.05
    latency_estimate: 120
```

### Environment Variable Overrides

Use environment variables for production:

```yaml
agents:
  - agent_id: data_analyst
    endpoint: ${DATA_ANALYST_ENDPOINT:-http://localhost:8001/analyze}
    # Falls back to localhost:8001 if env var not set
```

```bash
export DATA_ANALYST_ENDPOINT=https://prod-analyst.company.com/analyze
```

### Multiple Endpoints (Fallback)

```yaml
agents:
  - agent_id: data_analyst
    endpoints:
      - url: https://primary.company.com/analyze
        priority: 1
      - url: https://backup.company.com/analyze
        priority: 2
    fallback_strategy: sequential  # Try in order of priority
```

---

## Delegation Patterns

### Pattern 1: Basic Delegation

**Use Case:** Single task to single agent.

```python
from orchestrator.a2a.client import A2AClient

async def analyze_sales_data(dataset_path: str):
    """Delegate data analysis to specialized agent."""
    
    client = A2AClient()
    
    result = await client.delegate(
        agent_id="data_analyst",
        request={
            "dataset": dataset_path,
            "metrics": ["revenue", "growth_rate"],
            "period": "2024-Q1"
        },
        idempotency_key=f"sales-{dataset_path}-2024q1",
        timeout=300
    )
    
    return result
```

---

### Pattern 2: Streaming Delegation

**Use Case:** Long-running task with incremental output (code generation, report writing).

```python
async def generate_code_with_progress(specification: str):
    """Stream code generation with progress updates."""
    
    client = A2AClient()
    
    generated_code = []
    
    async for chunk in client.delegate_streaming(
        agent_id="code_generator",
        request={
            "specification": specification,
            "language": "python",
            "include_tests": True
        }
    ):
        # Show progress to user
        print(chunk, end="", flush=True)
        generated_code.append(chunk)
    
    return "".join(generated_code)
```

---

### Pattern 3: Batch Delegation

**Use Case:** Process multiple items in parallel.

```python
import asyncio

async def analyze_multiple_datasets(datasets: list[str]):
    """Analyze multiple datasets in parallel."""
    
    client = A2AClient()
    
    tasks = [
        client.delegate(
            agent_id="data_analyst",
            request={"dataset": ds},
            idempotency_key=f"analysis-{ds}"
        )
        for ds in datasets
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Separate successes and failures
    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]
    
    return {
        "successes": successes,
        "failures": failures,
        "success_rate": len(successes) / len(results)
    }
```

---

### Pattern 4: Consensus Delegation

**Use Case:** Get multiple opinions, pick best answer (high-stakes decisions).

```python
async def legal_review_with_consensus(document: str):
    """Get consensus from multiple legal agents."""
    
    client = A2AClient()
    
    # Delegate to 3 different legal agents
    agent_ids = ["legal_agent_1", "legal_agent_2", "legal_agent_3"]
    
    reviews = await asyncio.gather(*[
        client.delegate(
            agent_id=agent_id,
            request={"document": document, "review_type": "compliance"}
        )
        for agent_id in agent_ids
    ])
    
    # Count votes for each risk level
    risk_votes = {}
    for review in reviews:
        risk = review.get("risk_level", "unknown")
        risk_votes[risk] = risk_votes.get(risk, 0) + 1
    
    # Pick majority vote
    consensus = max(risk_votes, key=risk_votes.get)
    
    return {
        "consensus_risk": consensus,
        "votes": risk_votes,
        "reviews": reviews
    }
```

---

### Pattern 5: Fallback Chain

**Use Case:** Primary agent unavailable, fallback to alternatives.

```python
async def analyze_with_fallback(dataset: str):
    """Try primary agent, fallback to secondary if unavailable."""
    
    client = A2AClient()
    
    # Try primary (expensive, accurate)
    try:
        return await client.delegate(
            agent_id="premium_analyst",
            request={"dataset": dataset},
            timeout=120
        )
    except Exception as e:
        print(f"Primary agent failed: {e}, trying fallback...")
    
    # Try secondary (cheaper, decent)
    try:
        return await client.delegate(
            agent_id="basic_analyst",
            request={"dataset": dataset},
            timeout=60
        )
    except Exception as e:
        print(f"Secondary agent failed: {e}, using local tool...")
    
    # Fallback to local MCP tool (free, basic)
    return await execute_tool("local_stats", {"dataset": dataset})
```

---

## Idempotency Keys

**Problem:** Network failures can cause duplicate work.

**Solution:** Use idempotency keys to make requests safe to retry.

```python
# Without idempotency key (BAD)
result = await client.delegate(
    agent_id="payment_processor",
    request={"amount": 1000, "account": "12345"}
)
# If network fails after agent processes but before response,
# retry will charge $1000 again!

# With idempotency key (GOOD)
result = await client.delegate(
    agent_id="payment_processor",
    request={"amount": 1000, "account": "12345"},
    idempotency_key="payment-invoice-9876"
)
# Agent remembers this key, returns cached result on retry
```

**Key Format:**
```python
# Format: {operation}-{resource}-{timestamp/version}
idempotency_key = f"analysis-{dataset_id}-{date}"
idempotency_key = f"payment-{invoice_id}"
idempotency_key = f"generation-{user_id}-{request_hash}"
```

---

## Error Handling

### Timeout Errors

```python
from orchestrator.a2a.client import A2ATimeoutError

try:
    result = await client.delegate(
        agent_id="slow_agent",
        request={"task": "complex_analysis"},
        timeout=60  # 1 minute
    )
except A2ATimeoutError:
    # Agent took too long
    print("Agent exceeded timeout, trying faster alternative...")
    result = await client.delegate(
        agent_id="fast_agent",
        request={"task": "quick_analysis"},
        timeout=30
    )
```

### Agent Unavailable

```python
from orchestrator.a2a.client import A2AConnectionError

try:
    result = await client.delegate(agent_id="data_analyst", request={})
except A2AConnectionError as e:
    # Agent is down or unreachable
    print(f"Agent unavailable: {e}")
    # Fallback to local tool
    result = await execute_tool("local_analysis", {})
```

### Validation Errors

```python
from orchestrator.a2a.client import A2AValidationError

try:
    result = await client.delegate(
        agent_id="data_analyst",
        request={"invalid_field": "value"}  # Missing required 'dataset' field
    )
except A2AValidationError as e:
    # Request doesn't match agent's input schema
    print(f"Invalid request: {e}")
```

---

## Monitoring & Observability

### Track Delegation Metrics

```python
from orchestrator.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()

async def monitored_delegation(agent_id: str, request: dict):
    """Delegate with metrics tracking."""
    
    start_time = time.time()
    
    try:
        result = await client.delegate(agent_id=agent_id, request=request)
        
        # Log success
        metrics.record({
            "agent_id": agent_id,
            "status": "success",
            "latency": time.time() - start_time,
            "cost": result.get("cost", 0)
        })
        
        return result
    except Exception as e:
        # Log failure
        metrics.record({
            "agent_id": agent_id,
            "status": "failed",
            "latency": time.time() - start_time,
            "error": str(e)
        })
        raise

# Analyze metrics
print(f"Avg latency: {metrics.avg_latency('data_analyst'):.1f}s")
print(f"Success rate: {metrics.success_rate('data_analyst'):.1f}%")
print(f"Total cost: ${metrics.total_cost():.2f}")
```

---

## Real-World Example: Multi-Agent Analysis Pipeline

```python
from orchestrator.a2a.client import A2AClient

async def analyze_company_financials(company_id: str):
    """Delegate analysis to specialized agents."""
    
    client = A2AClient()
    
    # Step 1: Data extraction (agent)
    raw_data = await client.delegate(
        agent_id="data_extractor",
        request={"company_id": company_id, "sources": ["sec_filings", "earnings_calls"]},
        idempotency_key=f"extract-{company_id}",
        timeout=300
    )
    
    # Step 2: Financial analysis (agent)
    financial_analysis = await client.delegate(
        agent_id="financial_analyst",
        request={"data": raw_data, "metrics": ["revenue_growth", "margins"]},
        idempotency_key=f"analyze-{company_id}",
        timeout=180
    )
    
    # Step 3: Risk assessment (agent)
    risk_analysis = await client.delegate(
        agent_id="risk_analyst",
        request={"company_id": company_id, "financials": financial_analysis},
        idempotency_key=f"risk-{company_id}",
        timeout=120
    )
    
    # Step 4: Report generation (local tool - deterministic)
    report = await execute_tool(
        "format_report",
        {
            "financials": financial_analysis,
            "risks": risk_analysis,
            "template": "executive_summary"
        }
    )
    
    return report
```

---

## Best Practices

### ✅ Do's

1. **Always use idempotency keys** for expensive/stateful operations
2. **Set realistic timeouts** based on agent SLA (60-300s typical)
3. **Implement fallback chains** (primary → secondary → local tool)
4. **Monitor agent costs** to optimize budget
5. **Cache discovery results** (agents don't change often)
6. **Use streaming for long tasks** to show progress
7. **Validate requests** before delegating (check schema)

### ❌ Don'ts

1. **Don't delegate deterministic tasks** (use MCP tools instead)
2. **Don't skip idempotency keys** for payments/mutations
3. **Don't use short timeouts** for complex tasks (<30s)
4. **Don't ignore agent failures** (implement retry logic)
5. **Don't hardcode endpoints** (use environment variables)
6. **Don't delegate without fallbacks** (always have plan B)

---

## Decision Tree: A2A vs MCP

```
Is the task deterministic (same input → same output)?
├─ YES → Use MCP Tool
└─ NO → Continue

Does the task require specialized domain knowledge?
├─ YES → Use A2A Agent
└─ NO → Continue

Is the task resource-intensive (GPU, large model)?
├─ YES → Use A2A Agent
└─ NO → Continue

Is low latency critical (<100ms)?
├─ YES → Use MCP Tool
└─ NO → Continue

Is the task stateful (requires memory)?
├─ YES → Use A2A Agent
└─ NO → Use MCP Tool
```

---

## Next Steps

- **How-To Guide:** [Configure A2A Agents](../how-to/configure-a2a-agents.md) - Step-by-step setup
- **Deep Dive:** [A2A Protocol](../reference/deep-dives/a2a-protocol.md) - Technical specification
- **Sample:** [16-agent-delegation](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/16-agent-delegation) - Working examples

## Related Topics

- [Multi-Agent Coordination](multi-agent-coordination.md) - Orchestrating multiple agents
- [Cost Optimization](cost-optimization.md) - Minimize agent delegation costs
- [Error Recovery](error-recovery.md) - Handle agent failures gracefully

