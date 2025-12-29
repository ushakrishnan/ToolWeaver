# Sample 25: Parallel Agents Deep Dive

Run multiple agents in parallel with comprehensive guardrails for cost, concurrency, and safety.

## Overview

This sample demonstrates ToolWeaver's parallel agent dispatch system with deep coverage of:
- **When** to use parallel agents (batch processing, consensus, search)
- **How** parallel dispatch works (semaphore, quotas, idempotency, security)
- **Why** it's powerful (speedup, ensemble intelligence, fail-safe, aggregation)
- Complete architecture and flow diagrams

## What You'll Learn

### WHEN to Use Parallel Agents
- ✅ **Batch Processing**: Process 100 receipts simultaneously
- ✅ **Multi-Model Consensus**: Get 5 models to vote on classification
- ✅ **Parallel Search**: Query 10 documents concurrently
- ❌ **Anti-patterns**: When NOT to use parallelism

### HOW It Works
1. **Semaphore Control**: Limit concurrent execution (e.g., max 3 at once)
2. **Resource Quotas**: Prevent cost bombs with `DispatchResourceLimits`
3. **Idempotency Caching**: Automatic deduplication with 1-hour TTL
4. **Security**: Template sanitization, PII filtering, rate limiting

### WHY It's Powerful
- **🚀 Speedup**: 1.7x faster for 50 items (parallel vs sequential)
- **🧠 Ensemble Intelligence**: Combine results from multiple models
- **🛡️ Fail-Safe**: Circuit breakers prevent cascading failures
- **📊 Aggregation**: rank_by_metric, majority_vote, best_result patterns

## How to run

### Quick Start (Main Demo)
```bash
python main.py
```

### Comprehensive Deep Dive
```bash
python parallel_deep_dive.py
```

## Expected Output

The deep dive demo shows:

```
WHEN TO USE PARALLEL AGENTS
✅ USE CASE 1: Batch Processing
	Processed 20 receipts in 0.21s (11ms avg per receipt)

✅ USE CASE 2: Multi-Model Consensus
	5 models completed in 0.11s
	Majority vote: electronics (4/5 votes)

✅ USE CASE 3: Parallel Search
	10 documents searched in 0.22s

HOW PARALLEL DISPATCH WORKS
🔧 MECHANISM 1: Semaphore Control
	10 tasks with max_parallel=3 completed in 0.43s
	Batching: [3] → [3] → [3] → [1]

🔧 MECHANISM 2: Resource Limits (Quota Protection)
	Protected! Would have cost $10.00, capped at $0.05

🔧 MECHANISM 3: Idempotency Caching
	Run 1: 107ms, $0.0020
	Run 2: 0ms (746x faster), $0.00

WHY PARALLEL AGENTS ARE POWERFUL
💪 BENEFIT 1: Speedup
	50 items: 3.12s parallel vs 5.40s sequential = 1.7x speedup

💪 BENEFIT 2: Ensemble Intelligence
	7 models voting → more reliable classification

💪 BENEFIT 3: Fail-Safe
	Quota prevented $10 cost bomb (limit: $0.05)
```

## Files

- **`main.py`** — Minimal runnable example using `dispatch_agents`
- **`parallel_deep_dive.py`** — Comprehensive guide covering when/how/why with live demonstrations
- **`README.md`** — This file

## Key Concepts

### Resource Limits
```python
limits = DispatchResourceLimits(
	 max_total_cost_usd=5.0,        # Stop if total cost > $5
	 max_total_agents=100,          # Max 100 agent calls
	 max_concurrent=10,             # Max 10 running at once
	 max_failure_rate=0.3,          # Stop if >30% fail
	 max_total_duration_s=600       # Timeout after 10 minutes
)
```

### Aggregation Functions
- **`collect_all()`**: Return all results as-is
- **`rank_by_metric(key="score")`**: Sort by numeric metric
- **`majority_vote(key="category")`**: Democratic consensus
- **`best_result(key="confidence")`**: Pick highest scorer

### Idempotency
Cache key: `hash(agent_name + template + str(arguments))`
- TTL: 1 hour
- Automatic deduplication
- Cost savings: Avoid re-running identical requests

## Architecture

```
User Call
	↓
dispatch_agents(agent_configs, limits)
	↓
Validation (template sanitization, PII filter)
	↓
Parallel Execution (asyncio.gather + semaphore)
	├─→ Agent 1 (check idempotency cache)
	├─→ Agent 2 (enforce resource limits)
	├─→ Agent 3 (capture cost/duration)
	└─→ ... (up to max_concurrent)
	↓
Post-Processing (aggregation function)
	↓
Results + Metadata
```

## Related Documentation

- [orchestrator/tools/sub_agent.py](../../orchestrator/tools/sub_agent.py#L78-L230) - Core dispatch implementation
- [orchestrator/tools/sub_agent_limits.py](../../orchestrator/tools/sub_agent_limits.py#L19-L211) - Resource quotas
- [Agent Delegation](https://ushakrishnan.github.io/ToolWeaver/reference/deep-dives/agent-delegation/) - Reference
- [Sample 16: Agent Delegation](../16-agent-delegation/) - Basic agent delegation patterns
- [Sample 17: Multi-Agent Coordination](../17-multi-agent-coordination/) - Advanced coordination
