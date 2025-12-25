# How to Run Parallel Dispatch

Use `dispatch_agents` to fan out calls with guardrails.

```python
import asyncio
from orchestrator.tools.sub_agent import dispatch_agents
from orchestrator.tools.sub_agent_limits import DispatchResourceLimits

async def main():
    tasks = [
        {"name": "model_a", "template": "classify {{text}}", "arguments": {"text": "receipt"}},
        {"name": "model_b", "template": "classify {{text}}", "arguments": {"text": "receipt"}},
    ]

    limits = DispatchResourceLimits(max_concurrent=3, max_total_cost_usd=1.0)

    results = await dispatch_agents(
        agent_configs=tasks,
        aggregation="majority_vote",
        limits=limits,
        idempotency_ttl_seconds=3600,
    )
    print(results)

asyncio.run(main())
```

Key guards:

See the full demo: [samples/25-parallel-agents/parallel_deep_dive.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/25-parallel-agents/parallel_deep_dive.py)
README: [samples/25-parallel-agents/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/25-parallel-agents/README.md)
