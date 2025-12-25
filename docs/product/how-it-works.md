# How It Works

## Simple Explanation
Plan with a large model once, then run many small, safe steps. ToolWeaver finds the right tools and executes them in parallel with guardrails (cost, time, failures), caching results so repeated work is cheap.

## Technical Explanation
Planner produces a DAG of tool steps. The orchestrator discovers tools, narrows via hybrid search (BM25 + embeddings), dispatches steps concurrently with semaphores and limits, retries/fallbacks on errors, aggregates outputs, and records metrics. Code execution runs in a sandbox with restricted builtins and timeouts.

## Architecture
1. Register tools (decorators, templates, or YAML)
2. Discover tools (catalog + search)
3. Dispatch agents in parallel with guardrails
4. Aggregate outputs (vote, rank, best)
5. Cache results and enforce idempotency

### Diagram
```
User Code / Planner
	 │
	 ▼
 Register Tools  ──────────────┐
 (decorators/templates/YAML)   │
	 │                      │
	 ▼                      │
 Discover Catalog ─────────────┤
 (search/semantic/browse)      │
	 │                      │
	 ▼                      │
 Parallel Dispatch (semaphore, limits, idempotency)
	 │                      │
	 ├─► Tool/Agent 1       │
	 ├─► Tool/Agent 2       │
	 └─► Tool/Agent N       │
	 │                      │
	 ▼                      │
 Aggregate (vote/rank/best/collect)
	 │                      │
	 ▼                      │
 Cache + Metrics + Safety (PII, secrets redactor, sandbox)
	 │
	 ▼
 Results
```

## Parallel Dispatch
- Concurrency control via semaphore (`max_concurrent`)
- Resource limits: cost caps, total agents, duration, failure rate
- Idempotency: cache identical requests for instant reuse
- Safety: template sanitization, PII filter

## Sandboxed Execution
- Restricted builtins and forbidden modules
- Timeout enforcement; captured output

## Caching
- Redis + file fallback
- TTL per layer; graceful circuit breaker on outages

See:
- [Tutorial: Parallel Agents](../tutorials/parallel-agents.md)
- [Tutorial: Caching Deep Dive](../tutorials/caching-deep-dive.md)
- [Tutorial: Sandbox Execution](../tutorials/sandbox-execution.md)
