# Idempotency & Retry (Dispatch)

## Simple Explanation
Run many agent calls safely: avoid duplicate work with idempotency keys, enforce timeouts and rate limits, and apply fail‑fast policies.

## Technical Explanation
Use `dispatch_agents()` with `ResourceLimits` for quotas and tracking. Idempotency cache stores results by key; repeated inputs return cached outputs. Rate limiter controls request pace; timeouts and failure‑rate guards enforce resilience.

**When to use**
- Parallel orchestration with potential retries
- Budget and reliability constraints

**Key Primitives**
- `dispatch_agents()` — parallel execution with guardrails
- `ResourceLimits` — quotas and thresholds
- Idempotency cache — avoids duplicates

**Try it**
- Run the sample: [samples/32-idempotency-retry/idempotency_retry_demo.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/32-idempotency-retry/idempotency_retry_demo.py)
- See the README: [samples/32-idempotency-retry/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/32-idempotency-retry/README.md)

**Why run this**
- See cache hits in action for duplicate inputs
- Observe timeouts and failure‑rate guards under load
- Tune rate limits and quotas to your API budgets

**Gotchas**
- Bound retries; treat timeouts as failures when appropriate
- Tune rate limits to API quotas
- Use deterministic aggregation for partial results
