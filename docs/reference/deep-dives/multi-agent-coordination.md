# Multi-Agent Coordination

## Simple Explanation
Coordinate multiple agents to work on parts of a problem in parallel, then combine the results. Use semaphores, quotas, and clear roles.

## Technical Explanation
Define roles and tasks, assign agents based on capabilities, and use a coordinator to manage fan-out/fan-in with resource limits and idempotency keys. Aggregate outputs deterministically and record provenance.

**When to use**
- Complex tasks that decompose into parallelizable subtasks
- Teams of specialized agents with shared context

**Key Primitives**
- Role definitions and task decomposition
- Coordinator with concurrency controls
- Idempotency cache and provenance tracking
- Deterministic aggregation and conflict resolution

**Try it**
- Coordinate agents: [samples/17-multi-agent-coordination/coordinate_agents.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/17-multi-agent-coordination/coordinate_agents.py)
- See the README: [samples/17-multi-agent-coordination/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/17-multi-agent-coordination/README.md)

**Gotchas**
- Avoid race conditions; use clear ownership and locks
- Keep shared context small; pass references not blobs
- Handle stragglers with timeouts and partial aggregates
