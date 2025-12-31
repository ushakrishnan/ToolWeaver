import asyncio
from typing import Any

from orchestrator.tools.sub_agent import dispatch_agents
from orchestrator.tools.sub_agent_limits import DispatchResourceLimits


async def simulated_executor(prompt: str, args: dict[str, Any], agent_name: str, model: str) -> Any:
    """Simulate variable runtime and return a simple dict with cost.
    If args contains delay > timeout, the dispatch will time out (handled upstream).
    """
    delay = float(args.get("delay", 0.05))
    await asyncio.sleep(delay)
    return {"output": f"{agent_name}:{model}:{prompt}", "args": args, "cost": 0.02}


async def main() -> None:
    template = "process: {text}"
    arguments = [
        {"text": "fast", "delay": 0.05},
        {"text": "also fast", "delay": 0.05},
        # This one will time out (set timeout_per_agent smaller than delay)
        {"text": "too slow", "delay": 0.5},
        # Duplicate to demonstrate idempotency cache
        {"text": "fast", "delay": 0.05},
    ]

    limits = DispatchResourceLimits(
        max_concurrent=2,
        requests_per_second=2.0,
        max_total_agents=10,
        max_total_cost_usd=5.0,
    )

    results = await dispatch_agents(
        template=template,
        arguments=arguments,
        agent_name="demo-agent",
        model="haiku",
        max_parallel=2,
        timeout_per_agent=0.2,  # will cause the slow one to time out
        limits=limits,
        executor=simulated_executor,
    )

    for idx, r in enumerate(results):
        print(
            f"#{idx} success={r.success} error={r.error} duration_ms={r.duration_ms:.1f} cost={r.cost} output={r.output}"
        )


if __name__ == "__main__":
    asyncio.run(main())
