# How to Run Parallel Dispatch

Use `dispatch_agents` to fan out calls with guardrails.

```python
import asyncio
from orchestrator.tools.sub_agent import dispatch_agents
from orchestrator.tools.sub_agent_limits import DispatchResourceLimits

async def main():
    template = "classify {{text}}"
    arguments = [
        {"text": "receipt_001"},
        {"text": "receipt_002"},
    ]

    limits = DispatchResourceLimits(max_concurrent=3, max_total_cost_usd=1.0)

    results = await dispatch_agents(
        template=template,
        arguments=arguments,
        agent_name="classifier",
        model="haiku",
        limits=limits,
        aggregate_fn=lambda results: [r.output for r in results],
    )
    print(results)

asyncio.run(main())
```

Key guards:

See the full demo: [samples/25-parallel-agents/parallel_agents_main.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/25-parallel-agents/parallel_agents_main.py)
README: [samples/25-parallel-agents/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/25-parallel-agents/README.md)
