# Control Flow Patterns

## Simple Explanation
Common orchestration patterns to structure complex workflows: sequence, branch, map/reduce, retry with backoff, and circuit breakers. Use them to keep workflows predictable and resilient.

## Technical Explanation
Compose tasks using explicit control flow: DAG or step functions. Implement branching by predicates, fan-out/fan-in for parallel work, and resilience via retries, backoff, and circuit breakers. Track idempotency keys to avoid duplicate work.

**When to use**
- Multi-step workflows with conditional paths
- Parallelizable subtasks with aggregation
- External dependencies that can fail intermittently

**Key Primitives**
- DAG planner or step executor
- Branch predicates and guards
- Fan-out/fan-in with concurrency limits
- Retry/backoff; circuit breaker; idempotency cache

**Try it**
- Run the sample: [samples/15-control-flow/demo_patterns.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/15-control-flow/demo_patterns.py)
- See the README: [samples/15-control-flow/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/15-control-flow/README.md)

**Gotchas**
- Keep side-effects behind idempotent interfaces
- Make aggregation robust to partial failures
- Add timeouts and budget limits per branch
