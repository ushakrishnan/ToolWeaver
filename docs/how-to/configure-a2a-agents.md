# How to Configure A2A Agents

Step-by-step guide to set up Agent-to-Agent (A2A) protocol for delegating tasks to external agents.

## Prerequisites

- Working ToolWeaver project
- Basic understanding of [Agent Delegation](../tutorials/agent-delegation.md)
- External agent endpoint (or use sample agent for testing)

## What You'll Accomplish

By the end of this guide, you'll have:

✅ Created `agents.yaml` configuration file  
✅ Registered external agents with capabilities  
✅ Implemented agent discovery  
✅ Delegated tasks to agents  
✅ Set up error handling and fallbacks  

**Estimated time:** 20 minutes

---

## Step 1: Create agents.yaml Configuration

### 1.1 Basic Configuration Structure

**File:** `agents.yaml`

```yaml
# Global A2A settings
a2a:
  enabled: true
  default_timeout: 300  # 5 minutes
  discovery_cache_ttl: 3600  # Cache agent list for 1 hour

agents:
  # Agent 1: Data Analyst
  - agent_id: data_analyst
    name: Data Analysis Agent
    description: Analyzes datasets and provides statistical insights
    endpoint: http://localhost:8001/analyze
    protocol: http
    capabilities:
      - data_analysis
      - statistical_modeling
      - visualization
    
    # Input/output schema
    input_schema:
      type: object
      properties:
        dataset:
          type: string
          description: Path or ID of dataset to analyze
        metrics:
          type: array
          description: Metrics to compute (e.g., mean, median, variance)
      required: [dataset]
    
    output_schema:
      type: object
      properties:
        results:
          type: object
        summary:
          type: string
    
    # Cost and performance estimates
    cost_estimate: 0.05  # $0.05 per call
    latency_estimate: 120  # ~120 seconds
    
    # Metadata
    metadata:
      tags: [analytics, statistics]
      version: 1.0.0
      sla: 99.5
```

### 1.2 Multiple Agents Example

```yaml
a2a:
  enabled: true
  default_timeout: 300

agents:
  # Agent 1: Data Analyst
  - agent_id: data_analyst
    name: Data Analysis Agent
    endpoint: http://localhost:8001/analyze
    capabilities: [data_analysis]
    cost_estimate: 0.05
  
  # Agent 2: Code Generator
  - agent_id: code_generator
    name: Code Generation Agent
    endpoint: http://localhost:8002/generate
    capabilities: [code_generation, testing]
    cost_estimate: 0.10
  
  # Agent 3: Legal Reviewer
  - agent_id: legal_reviewer
    name: Legal Document Reviewer
    endpoint: http://localhost:8003/review
    capabilities: [legal_analysis, compliance]
    cost_estimate: 0.20
```

---

## Step 2: Environment Variable Configuration

### 2.1 Use Environment Variables for Production

**agents.yaml** (with env var placeholders):

```yaml
agents:
  - agent_id: data_analyst
    # Use env var, fallback to localhost
    endpoint: ${DATA_ANALYST_ENDPOINT:-http://localhost:8001/analyze}
    # Authentication token from env
    auth_token: ${DATA_ANALYST_TOKEN}
    cost_estimate: ${DATA_ANALYST_COST:-0.05}
```

### 2.2 Set Environment Variables

**Linux/macOS:**
```bash
export DATA_ANALYST_ENDPOINT=https://prod-analyst.company.com/analyze
export DATA_ANALYST_TOKEN=sk-abc123xyz789
export DATA_ANALYST_COST=0.05
```

**Windows PowerShell:**
```powershell
$env:DATA_ANALYST_ENDPOINT = "https://prod-analyst.company.com/analyze"
$env:DATA_ANALYST_TOKEN = "sk-abc123xyz789"
$env:DATA_ANALYST_COST = "0.05"
```

**.env file:**
```bash
# .env
DATA_ANALYST_ENDPOINT=https://prod-analyst.company.com/analyze
DATA_ANALYST_TOKEN=sk-abc123xyz789
DATA_ANALYST_COST=0.05
```

Load with `python-dotenv`:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Step 3: Initialize A2A Client

### 3.1 Basic Client Setup

**File:** `client/a2a_client.py`

```python
from orchestrator.a2a.client import A2AClient

# Load configuration from agents.yaml
client = A2AClient(config_path="agents.yaml")

# Or specify custom path
client = A2AClient(config_path="config/production_agents.yaml")
```

### 3.2 Programmatic Configuration (No YAML)

```python
from orchestrator.a2a.client import A2AClient
from orchestrator.a2a.config import AgentConfig, A2AConfig

# Define agent configuration
data_analyst_config = AgentConfig(
    agent_id="data_analyst",
    name="Data Analysis Agent",
    endpoint="http://localhost:8001/analyze",
    capabilities=["data_analysis", "statistics"],
    cost_estimate=0.05,
    latency_estimate=120
)

# Create A2A config
a2a_config = A2AConfig(
    enabled=True,
    default_timeout=300,
    agents=[data_analyst_config]
)

# Initialize client with config object
client = A2AClient(config=a2a_config)
```

---

## Step 4: Discover Available Agents

### 4.1 List All Agents

```python
async def discover_agents():
    """Discover all configured agents."""
    
    client = A2AClient(config_path="agents.yaml")
    
    agents = await client.discover_agents()
    
    print(f"Found {len(agents)} agents:\n")
    
    for agent in agents:
        print(f"Agent: {agent.name}")
        print(f"  ID: {agent.agent_id}")
        print(f"  Endpoint: {agent.endpoint}")
        print(f"  Capabilities: {', '.join(agent.capabilities)}")
        print(f"  Cost: ${agent.cost_estimate}/call")
        print(f"  Latency: ~{agent.latency_estimate}s")
        print()

# Run discovery
await discover_agents()
```

**Output:**
```
Found 3 agents:

Agent: Data Analysis Agent
  ID: data_analyst
  Endpoint: http://localhost:8001/analyze
  Capabilities: data_analysis, statistical_modeling
  Cost: $0.05/call
  Latency: ~120s

Agent: Code Generation Agent
  ID: code_generator
  Endpoint: http://localhost:8002/generate
  Capabilities: code_generation, testing
  Cost: $0.10/call
  Latency: ~60s
```

### 4.2 Find Agent by Capability

```python
async def find_agents_by_capability(capability: str):
    """Find agents with specific capability."""
    
    client = A2AClient(config_path="agents.yaml")
    agents = await client.discover_agents()
    
    matching = [a for a in agents if capability in a.capabilities]
    
    if not matching:
        print(f"No agents found with capability: {capability}")
        return None
    
    # Return cheapest agent
    cheapest = min(matching, key=lambda a: a.cost_estimate)
    print(f"Found {len(matching)} agents, cheapest: {cheapest.name} (${cheapest.cost_estimate})")
    return cheapest

# Usage
agent = await find_agents_by_capability("data_analysis")
```

---

## Step 5: Delegate Tasks to Agents

### 5.1 Basic Delegation

```python
async def delegate_analysis(dataset_path: str):
    """Delegate data analysis to external agent."""
    
    client = A2AClient(config_path="agents.yaml")
    
    result = await client.delegate(
        agent_id="data_analyst",
        request={
            "dataset": dataset_path,
            "metrics": ["mean", "median", "std_dev"]
        }
    )
    
    return result

# Usage
result = await delegate_analysis("sales_2024.csv")
print(result)
```

### 5.2 Delegation with Idempotency Key

```python
async def delegate_with_idempotency(dataset_path: str):
    """Delegate with idempotency key to prevent duplicate work."""
    
    client = A2AClient(config_path="agents.yaml")
    
    # Generate idempotency key
    idempotency_key = f"analysis-{dataset_path}-v1"
    
    result = await client.delegate(
        agent_id="data_analyst",
        request={"dataset": dataset_path},
        idempotency_key=idempotency_key,  # Agent will cache this
        timeout=300
    )
    
    return result
```

### 5.3 Streaming Delegation

```python
async def delegate_streaming(specification: str):
    """Stream results from agent for long-running tasks."""
    
    client = A2AClient(config_path="agents.yaml")
    
    print("Generating code...")
    
    async for chunk in client.delegate_streaming(
        agent_id="code_generator",
        request={
            "specification": specification,
            "language": "python",
            "include_tests": True
        }
    ):
        print(chunk, end="", flush=True)
    
    print("\n✓ Code generation complete")

# Usage
await delegate_streaming("REST API for user management")
```

---

## Step 6: Add Authentication

### 6.1 Bearer Token Authentication

**agents.yaml:**
```yaml
agents:
  - agent_id: secure_agent
    endpoint: https://api.company.com/analyze
    auth:
      type: bearer
      token: ${AGENT_AUTH_TOKEN}  # From environment variable
```

**Python code:**
```python
import os

# Set token in environment
os.environ["AGENT_AUTH_TOKEN"] = "sk-abc123xyz789"

# Client will automatically use token from config
client = A2AClient(config_path="agents.yaml")
result = await client.delegate(agent_id="secure_agent", request={...})
```

### 6.2 API Key Authentication

**agents.yaml:**
```yaml
agents:
  - agent_id: secure_agent
    endpoint: https://api.company.com/analyze
    auth:
      type: api_key
      header: X-API-Key
      key: ${API_KEY}
```

### 6.3 Custom Headers

**agents.yaml:**
```yaml
agents:
  - agent_id: custom_agent
    endpoint: https://api.company.com/analyze
    headers:
      Authorization: Bearer ${AUTH_TOKEN}
      X-Client-ID: ${CLIENT_ID}
      X-Request-Origin: ToolWeaver
```

---

## Step 7: Configure Fallback Endpoints

### 7.1 Multiple Endpoints with Priority

**agents.yaml:**
```yaml
agents:
  - agent_id: data_analyst
    name: Data Analysis Agent
    
    # Primary endpoint
    endpoints:
      - url: https://primary.company.com/analyze
        priority: 1
        region: us-east-1
      
      # Fallback endpoint
      - url: https://backup.company.com/analyze
        priority: 2
        region: us-west-2
      
      # Local fallback
      - url: http://localhost:8001/analyze
        priority: 3
        region: local
    
    fallback_strategy: sequential  # Try in order of priority
```

### 7.2 Implement Fallback Logic

```python
async def delegate_with_fallback(dataset: str):
    """Delegate with automatic fallback to alternative endpoints."""
    
    client = A2AClient(config_path="agents.yaml")
    
    try:
        result = await client.delegate(
            agent_id="data_analyst",
            request={"dataset": dataset},
            enable_fallback=True  # Try fallback endpoints on failure
        )
        return result
    
    except Exception as e:
        print(f"All endpoints failed: {e}")
        # Final fallback: local tool
        return await execute_local_analysis(dataset)
```

---

## Step 8: Error Handling

### 8.1 Handle Common Errors

```python
from orchestrator.a2a.client import (
    A2ATimeoutError,
    A2AConnectionError,
    A2AValidationError
)

async def delegate_with_error_handling(dataset: str):
    """Delegate with comprehensive error handling."""
    
    client = A2AClient(config_path="agents.yaml")
    
    try:
        result = await client.delegate(
            agent_id="data_analyst",
            request={"dataset": dataset},
            timeout=300
        )
        return result
    
    except A2ATimeoutError:
        print("Agent took too long, trying faster alternative...")
        return await client.delegate(
            agent_id="fast_analyst",
            request={"dataset": dataset},
            timeout=60
        )
    
    except A2AConnectionError:
        print("Agent unavailable, using local tool...")
        return await execute_local_tool("analysis", {"dataset": dataset})
    
    except A2AValidationError as e:
        print(f"Invalid request: {e}")
        raise ValueError(f"Dataset format invalid: {dataset}")
```

### 8.2 Retry Logic for Transient Failures

```python
async def delegate_with_retry(dataset: str, max_retries: int = 3):
    """Delegate with retry logic for transient failures."""
    
    client = A2AClient(config_path="agents.yaml")
    
    for attempt in range(max_retries):
        try:
            result = await client.delegate(
                agent_id="data_analyst",
                request={"dataset": dataset}
            )
            return result
        
        except A2AConnectionError as e:
            if attempt == max_retries - 1:
                raise
            
            delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
            print(f"Retry {attempt + 1} after {delay}s...")
            await asyncio.sleep(delay)
```

---

## Step 9: Monitor Agent Performance

### 9.1 Track Delegation Metrics

```python
from orchestrator.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()

async def delegate_with_monitoring(agent_id: str, request: dict):
    """Delegate with performance monitoring."""
    
    client = A2AClient(config_path="agents.yaml")
    
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
print(f"Agent 'data_analyst':")
print(f"  Avg latency: {metrics.avg_latency('data_analyst'):.1f}s")
print(f"  Success rate: {metrics.success_rate('data_analyst'):.1%}")
print(f"  Total cost: ${metrics.total_cost('data_analyst'):.2f}")
```

---

## Step 10: Real-World Example

Complete A2A setup for multi-agent pipeline.

**File:** `pipeline/financial_analysis.py`

```python
from orchestrator.a2a.client import A2AClient

async def analyze_company_financials(company_id: str):
    """Multi-agent financial analysis pipeline."""
    
    client = A2AClient(config_path="agents.yaml")
    
    # Step 1: Extract data (agent)
    print("Step 1: Extracting financial data...")
    raw_data = await client.delegate(
        agent_id="data_extractor",
        request={
            "company_id": company_id,
            "sources": ["sec_filings", "earnings_calls"]
        },
        idempotency_key=f"extract-{company_id}",
        timeout=300
    )
    
    # Step 2: Financial analysis (agent)
    print("Step 2: Analyzing financials...")
    financial_analysis = await client.delegate(
        agent_id="financial_analyst",
        request={
            "data": raw_data,
            "metrics": ["revenue_growth", "profit_margins", "debt_ratio"]
        },
        idempotency_key=f"analyze-{company_id}",
        timeout=180
    )
    
    # Step 3: Risk assessment (agent)
    print("Step 3: Assessing risks...")
    risk_analysis = await client.delegate(
        agent_id="risk_analyst",
        request={
            "company_id": company_id,
            "financials": financial_analysis
        },
        idempotency_key=f"risk-{company_id}",
        timeout=120
    )
    
    # Step 4: Generate report (local tool - deterministic)
    print("Step 4: Generating report...")
    report = await execute_tool(
        "format_report",
        {
            "financials": financial_analysis,
            "risks": risk_analysis,
            "template": "executive_summary"
        }
    )
    
    return report

# Usage
report = await analyze_company_financials("AAPL")
print(report)
```

---

## Verification

Test your A2A setup:

```python
async def verify_a2a_setup():
    """Verify A2A configuration is working."""
    
    client = A2AClient(config_path="agents.yaml")
    
    # Test 1: Discovery
    print("Test 1: Agent discovery...")
    agents = await client.discover_agents()
    assert len(agents) > 0, "No agents discovered"
    print(f"✓ Discovered {len(agents)} agents")
    
    # Test 2: Basic delegation (using echo agent for testing)
    print("\nTest 2: Basic delegation...")
    try:
        result = await client.delegate(
            agent_id="data_analyst",
            request={"test": "data"},
            timeout=30
        )
        print("✓ Delegation successful")
    except Exception as e:
        print(f"✗ Delegation failed: {e}")
    
    # Test 3: Idempotency
    print("\nTest 3: Idempotency...")
    key = "test-idempotency-123"
    
    result1 = await client.delegate(
        agent_id="data_analyst",
        request={"test": "data"},
        idempotency_key=key
    )
    
    result2 = await client.delegate(
        agent_id="data_analyst",
        request={"test": "data"},
        idempotency_key=key
    )
    
    assert result1 == result2, "Idempotency not working"
    print("✓ Idempotency working")
    
    print("\n✅ All checks passed!")

# Run verification
await verify_a2a_setup()
```

---

## Common Issues

### Issue 1: Agent Not Found

**Symptom:** `AgentNotFoundError: Agent 'data_analyst' not found`

**Solution:** Check agent_id in agents.yaml matches code

```bash
# Verify agent_id in config
cat agents.yaml | grep agent_id
```

### Issue 2: Connection Refused

**Symptom:** `A2AConnectionError: Connection refused to http://localhost:8001`

**Solution:** Verify agent endpoint is running

```bash
# Check if agent is running
curl http://localhost:8001/health

# Or check with telnet
telnet localhost 8001
```

### Issue 3: Authentication Failed

**Symptom:** `401 Unauthorized`

**Solution:** Verify auth token is set correctly

```python
# Debug: Print auth token (NEVER in production!)
import os
print(f"Token: {os.getenv('DATA_ANALYST_TOKEN')}")

# Verify token in config
client = A2AClient(config_path="agents.yaml")
agent = await client.get_agent("data_analyst")
print(f"Auth config: {agent.auth}")
```

---

## Next Steps

- **Tutorial:** [Agent Delegation](../tutorials/agent-delegation.md) - Learn delegation patterns
- **Deep Dive:** [Agent Delegation](../reference/deep-dives/agent-delegation.md) - Technical details
- **Sample:** [16-agent-delegation](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/16-agent-delegation) - Working example

## Related Guides

- [Implement Retry Logic](implement-retry-logic.md) - Handle agent failures
- [Optimize Tool Costs](optimize-tool-costs.md) - Minimize delegation costs

