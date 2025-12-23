import asyncio
from orchestrator.tools.sub_agent import dispatch_agents, rank_by_metric
from orchestrator.tools.sub_agent_limits import DispatchResourceLimits


async def exec_fn(prompt: str, args: dict, agent_name: str, model: str):
    # Replace with your model/tool call; here we just score by length
    score = 1.0 / (1 + len(prompt))
    return {"output": prompt, "score": score, "cost": 0.001}


async def main():
    args = [{"item": f"task-{i}"} for i in range(5)]
    limits = DispatchResourceLimits(max_parallel=3, min_success_count=3)

    results = await dispatch_agents(
        template="Handle {item}",
        arguments=args,
        limits=limits,
        executor=exec_fn,
    )

    ranked = rank_by_metric(results, "score")
    print("Top choice:", ranked[0].output)


if __name__ == "__main__":
    asyncio.run(main())
