"""
Parallel Sub-Agent Dispatch API

Provides safe, concurrent dispatch of sub-agents with security controls from
Phase 0 (quotas, rate limiting, PII filtering, template sanitization, secrets
redaction, and idempotency).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from orchestrator._internal.infra.idempotency import (
    generate_idempotency_key,
    get_global_cache,
)
from orchestrator._internal.infra.rate_limiter import RateLimiter
from orchestrator._internal.security.pii_detector import ResponseFilter
from orchestrator._internal.security.template_sanitizer import sanitize_template
from orchestrator.tools.sub_agent_limits import (
    DispatchLimitTracker,
    DispatchQuotaExceeded,
    DispatchResourceLimits,
)

# Type for agent executor callables
AgentExecutor = Callable[[str, dict[str, Any], str, str], Awaitable[Any]]


@dataclass
class SubAgentTask:
    """Task definition for a sub-agent invocation."""
    prompt_template: str
    arguments: dict[str, Any]
    agent_name: str = "default"
    model: str = "haiku"
    timeout_sec: int = 30
    idempotency_key: str | None = None

    def with_generated_key(self) -> SubAgentTask:
        """Return a copy with idempotency_key populated if missing."""
        key = self.idempotency_key or generate_idempotency_key(
            self.agent_name,
            self.prompt_template,
            self.arguments,
        )
        return SubAgentTask(
            prompt_template=self.prompt_template,
            arguments=self.arguments,
            agent_name=self.agent_name,
            model=self.model,
            timeout_sec=self.timeout_sec,
            idempotency_key=key,
        )


@dataclass
class SubAgentResult:
    """Result of a sub-agent execution."""
    task_args: dict[str, Any]
    output: Any
    error: str | None
    duration_ms: float
    success: bool
    cost: float = 0.0


async def _default_executor(prompt: str, args: dict[str, Any], agent_name: str, model: str) -> Any:
    """Default executor stub that echoes the prompt and args."""
    return {"output": prompt, "agent": agent_name, "model": model, "args": args, "cost": 0.0}


async def dispatch_agents(
    template: str,
    arguments: list[dict[str, Any]],
    agent_name: str = "default",
    model: str = "haiku",
    max_parallel: int = 10,
    timeout_per_agent: int = 30,
    limits: DispatchResourceLimits | None = None,
    executor: AgentExecutor | None = None,
    aggregate_fn: Callable[[list[SubAgentResult]], Any] | None = None,
) -> Any:
    """
    Dispatch multiple agents in parallel with safety controls.

    Args:
        template: Prompt template string (Python format syntax)
        arguments: List of argument dictionaries for the template
        agent_name: Target agent name
        model: Model identifier
        max_parallel: Maximum concurrent executions
        timeout_per_agent: Per-agent timeout in seconds
        limits: Optional resource limits (uses defaults if None)
        executor: Optional async callable(prompt, args, agent_name, model)

    Returns:
        List of SubAgentResult objects preserving input order.
    """
    if max_parallel <= 0:
        raise ValueError("max_parallel must be positive")

    # Phase 0 integrations
    sanitized_template = sanitize_template(template)
    limits = limits or DispatchResourceLimits()
    tracker = DispatchLimitTracker(limits)
    tracker.check_pre_dispatch(len(arguments))

    rate_limiter: RateLimiter | None = None
    if limits.requests_per_second:
        rate_limiter = RateLimiter(limits.requests_per_second)

    response_filter = ResponseFilter()
    cache = get_global_cache()
    exec_fn = executor or _default_executor

    semaphore = asyncio.Semaphore(max_parallel)
    results: list[SubAgentResult] = []

    async def run_single(arg: dict[str, Any]) -> SubAgentResult:
        task = SubAgentTask(
            prompt_template=sanitized_template,
            arguments=arg,
            agent_name=agent_name,
            model=model,
            timeout_sec=timeout_per_agent,
        ).with_generated_key()

        # Idempotency: return cached if available
        cached = cache.get(task.idempotency_key)
        if cached is not None:
            return SubAgentResult(
                task_args=arg,
                output=cached,
                error=None,
                duration_ms=0.0,
                success=True,
                cost=0.0,
            )

        await tracker.acquire_slot()
        start = time.monotonic()
        try:
            if rate_limiter:
                await rate_limiter.acquire()

            prompt = task.prompt_template.format(**task.arguments)
            # Execute with timeout
            async def _call_executor():
                return await exec_fn(prompt, task.arguments, task.agent_name, task.model)

            try:
                raw_result = await asyncio.wait_for(_call_executor(), timeout=task.timeout_sec)
            except asyncio.TimeoutError:
                duration = (time.monotonic() - start) * 1000
                await tracker.record_agent_completion(cost=0.0, success=False, duration=duration / 1000)
                return SubAgentResult(
                    task_args=arg,
                    output=None,
                    error="timeout",
                    duration_ms=duration,
                    success=False,
                    cost=0.0,
                )

            # Normalize output and cost
            cost = 0.0
            if isinstance(raw_result, dict):
                cost = float(raw_result.get("cost", 0.0))
                filtered = response_filter.filter_response(raw_result)
            else:
                filtered = raw_result

            duration_s = time.monotonic() - start
            await tracker.record_agent_completion(cost=cost, success=True, duration=duration_s)
            cache.store(task.idempotency_key, filtered)

            return SubAgentResult(
                task_args=arg,
                output=filtered,
                error=None,
                duration_ms=duration_s * 1000,
                success=True,
                cost=cost,
            )
        except DispatchQuotaExceeded as exc:
            duration_s = time.monotonic() - start
            return SubAgentResult(
                task_args=arg,
                output=None,
                error=str(exc),
                duration_ms=duration_s * 1000,
                success=False,
                cost=0.0,
            )
        except Exception as exc:  # pragma: no cover - safety net
            duration_s = time.monotonic() - start
            await tracker.record_agent_completion(cost=0.0, success=False, duration=duration_s)
            return SubAgentResult(
                task_args=arg,
                output=None,
                error=str(exc),
                duration_ms=duration_s * 1000,
                success=False,
                cost=0.0,
            )
        finally:
            await tracker.release_slot()

    # Launch tasks with concurrency control
    async def runner(arg: dict[str, Any]) -> SubAgentResult:
        async with semaphore:
            return await run_single(arg)

    coro_list = [runner(arg) for arg in arguments]
    results = await asyncio.gather(*coro_list)

    # Enforce min_success_count threshold (opt-in if >0)
    success_count = sum(1 for r in results if r.success)
    if limits.min_success_count and limits.min_success_count > 0:
        if success_count < limits.min_success_count:
            raise DispatchQuotaExceeded(
                f"Success count {success_count} below minimum {limits.min_success_count}"
            )

    # Apply optional aggregation
    if aggregate_fn:
        return aggregate_fn(results)

    return results


# Aggregation utilities

def collect_all(results: list[SubAgentResult]) -> list[SubAgentResult]:
    """Return all results as-is."""
    return results


def rank_by_metric(results: list[SubAgentResult], field: str, reverse: bool = True) -> list[SubAgentResult]:
    """Sort results by a numeric field inside result.output dict."""
    return sorted(
        results,
        key=lambda r: (r.output or {}).get(field, float('-inf')) if isinstance(r.output, dict) else float('-inf'),
        reverse=reverse,
    )


def majority_vote(results: list[SubAgentResult], field: str) -> Any | None:
    """Return the most common value for a field in result.output dicts."""
    counts: dict[Any, int] = {}
    for res in results:
        if isinstance(res.output, dict) and field in res.output:
            val = res.output[field]
            counts[val] = counts.get(val, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda item: item[1])[0]


def best_result(results: list[SubAgentResult], score_fn: Callable[[SubAgentResult], float]) -> SubAgentResult | None:
    """Return the result with highest score from score_fn."""
    if not results:
        return None
    return max(results, key=score_fn)
