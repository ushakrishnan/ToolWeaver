# Workflow Architecture

## Simple Explanation
A plan becomes a graph of steps. We run ready steps in parallel with limits, retry on errors, and combine results.

## Technical Explanation
Planner outputs a DAG. Dispatcher executes ready nodes concurrently (`asyncio.gather`) under semaphores and budgets; applies retries/circuit breakers; sandboxes code; aggregates outputs; and emits metrics/logs with redaction.

Execution is a DAG with guarded fan-out, retries, and fallbacks.

Key components
- Planner output → steps with dependencies, parameters, and stop conditions.
- Dispatcher → runs ready nodes concurrently, enforces timeouts and budgets.
- Safety rails → retry with backoff, circuit breakers, idempotency keys, redaction.
- Sandboxed code → restricted builtins, no network, separate process.

Flow
1) Validate plan (shape + limits).
2) Resolve tools via registry/search.
3) Execute ready steps in parallel (`asyncio.gather`), apply retries/fallbacks.
4) Aggregate outputs; short-circuit on fatal errors per policy.

Tuning
- Concurrency: cap fan-out to avoid runaway spend.
- Timeouts: per-step + global; propagate cancellations.
- Fallbacks: define alternates for flaky integrations.

Observability
- Metrics: success/failure, latency, cache hit rates.
- Logs: structured with redaction; debug mode adds more detail safely.
