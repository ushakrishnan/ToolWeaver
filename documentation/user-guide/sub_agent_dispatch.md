# Sub-Agent Dispatch

Safe parallel fan-out for 100+ agent calls with built-in guardrails.

## What it does
- Runs many agent/tool calls concurrently with a `max_parallel` cap.
- Enforces resource limits (cost, concurrency, total agents, duration, rate limits, recursion depth, optional `min_success_count`).
- Applies safety defaults: template sanitization, PII/secrets redaction, idempotency cache.
- Aggregates results (collect all, rank, majority vote, best score) or supports custom aggregation.

## API
```python
from orchestrator.tools.sub_agent import dispatch_agents, SubAgentTask, SubAgentResult
from orchestrator.tools.sub_agent_limits import DispatchResourceLimits

results_or_agg = await dispatch_agents(
    template: str,
    arguments: list[dict],
    agent_name: str = "default",
    model: str = "haiku",
    max_parallel: int = 10,
    timeout_per_agent: int = 30,
    limits: DispatchResourceLimits | None = None,
    executor: AgentExecutor | None = None,
    aggregate_fn: Callable[[list[SubAgentResult]], Any] | None = None,
)
```

- `arguments` are applied to `template` via Python format syntax.
- Provide `executor(prompt, args, agent_name, model)` to call your model/tool; defaults to an echo stub.
- `limits` defaults are safe; set `min_success_count` > 0 to enforce a success threshold.

## Resource limits (DispatchResourceLimits)
- Cost: `max_total_cost_usd`, `cost_per_agent_estimate`
- Concurrency: `max_concurrent`, `max_total_agents`
- Time: `max_agent_duration_s`, `max_total_duration_s`
- Rate: `requests_per_second`
- Failures: `max_failure_rate`, `min_success_count`
- Recursion: `max_dispatch_depth`, `current_depth`

## Safety controls
- **Template sanitization:** Blocks common injection patterns before dispatch.
- **PII/secrets redaction:** Filters executor outputs via `ResponseFilter`; metadata marks redacted fields.
- **Idempotency:** Reuses cached results when the same task repeats (`idempotency_key` auto-generated).
- **Rate limiting:** Optional token bucket if `requests_per_second` is set.

## Aggregation options
- `collect_all(results)` — return ordered results.
- `rank_by_metric(results, field)` — sort by numeric field in `output`.
- `majority_vote(results, field)` — most common value.
- `best_result(results, score_fn)` — highest score from custom function.
- Or pass `aggregate_fn` to return any custom aggregate value.

## Minimal example
```python
from orchestrator.tools.sub_agent import dispatch_agents, rank_by_metric
from orchestrator.tools.sub_agent_limits import DispatchResourceLimits

async def exec_fn(prompt, args, agent_name, model):
    # Call your model here
    score = 1.0 / (1 + args["i"])
    return {"output": prompt, "score": score, "cost": 0.002}

limits = DispatchResourceLimits(max_parallel=5, min_success_count=3)
args = [{"i": i} for i in range(5)]

results = await dispatch_agents(
    template="Rate {i}",
    arguments=args,
    limits=limits,
    executor=exec_fn,
)
ranked = rank_by_metric(results, "score")
```

## When to use
- Divide-and-conquer tasks (e.g., chunked analysis, scraping, retrieval).
- Ensembles/self-consistency: vote or rank multiple model/tool outputs.
- Batch scoring/classification with cost and failure guardrails.

## Notes
- If `min_success_count > 0` and not met, a `DispatchQuotaExceeded` is raised after runs complete.
- For secrets redaction in logs, call `install_secrets_redactor()` (auto-install wiring in progress).
- Examples and advanced patterns: `examples/25-parallel-agents/` (planned).
