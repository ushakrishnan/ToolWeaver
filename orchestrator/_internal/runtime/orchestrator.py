import asyncio
import json
import logging
import os
from collections.abc import Awaitable, Callable
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Any

from ...shared.models import PlanModel, ToolCatalog
from ..dispatch.hybrid_dispatcher import dispatch_step
from ..infra.a2a_client import A2AClient, AgentDelegationRequest
from ..infra.mcp_client import MCPClientShim
from ..observability.monitoring import ToolUsageMonitor

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global monitor instance (initialized on first use)
_monitor = None

def get_monitor() -> ToolUsageMonitor:
    """Get or create the global monitoring instance."""
    global _monitor
    if _monitor is None:
        backends_str = os.getenv("MONITORING_BACKENDS", "local")
        backends = [b.strip() for b in backends_str.split(',')]
        _monitor = ToolUsageMonitor(backends=backends)
        logger.info(f"Monitoring initialized with backends: {backends}")
    return _monitor

async def retry(coro_func: Callable[[], Awaitable[Any]], retries: int = 1, backoff_s: float = 1) -> Any:
    """
    Retry a coroutine function with exponential backoff.

    Args:
        coro_func: Async function to retry
        retries: Number of retry attempts
        backoff_s: Base backoff time in seconds

    Returns:
        Result from successful execution

    Raises:
        Last exception if all retries fail
    """
    last_exc: Exception | None = None
    for attempt in range(1, retries+1):
        try:
            return await coro_func()
        except Exception as e:
            last_exc = e
            logger.warning("Attempt %s failed: %s", attempt, e)
            if attempt < retries:
                await asyncio.sleep(backoff_s * attempt)
    if last_exc:
        raise last_exc
    raise RuntimeError("All retry attempts failed")


async def execute_agent_step(step: dict[str, Any], step_outputs: dict[str, Any], a2a_client: A2AClient | None, monitor: ToolUsageMonitor | None = None) -> Any:
    """Execute an agent delegation step with optional streaming."""
    if not a2a_client:
        raise ValueError("A2A client is required for agent steps")

    agent_id = step.get("agent_id")
    if not agent_id:
        raise ValueError("Agent step missing 'agent_id'")

    # Build context from prior outputs and inline context
    context_from_inputs = {
        key: step_outputs.get(key)
        for key in step.get("inputs", [])
        if key in step_outputs
    }
    inline_ctx = step.get("context") if isinstance(step.get("context"), dict) else {}
    merged_context: dict[str, Any] = {**context_from_inputs, **(inline_ctx if inline_ctx else {})}

    request = AgentDelegationRequest(
        agent_id=agent_id,
        task=step.get("task") or f"agent:{agent_id}",
        context=merged_context,
        timeout=step.get("timeout_s", 300),
        idempotency_key=step.get("idempotency_key"),
        metadata=step.get("metadata", {}),
    )

    if step.get("stream"):
        chunks = []
        async for chunk in a2a_client.delegate_stream(
            request,
            chunk_timeout=step.get("chunk_timeout_s"),
        ):
            chunks.append(chunk)
        return {"chunks": chunks}

    response = await a2a_client.delegate_to_agent(request)
    if not response.success:
        raise RuntimeError(response.metadata.get("error", "Agent delegation failed"))
    return response.result

def _normalize_step_for_dispatch(step: dict[str, Any], step_outputs: dict[str, Any]) -> dict[str, Any]:
    """Normalize agent-style steps into dispatcher-compatible format."""
    if step.get("type") != "agent":
        return step

    agent_id = step.get("agent_id")
    if not agent_id:
        raise ValueError("Agent step missing 'agent_id'")

    # Build context from referenced prior outputs and optional inline context
    context_from_inputs = {
        key: step_outputs.get(key)
        for key in step.get("inputs", [])
        if key in step_outputs
    }
    inline_ctx = step.get("context") if isinstance(step.get("context"), dict) else {}
    merged_context: dict[str, Any] = {**context_from_inputs, **(inline_ctx if inline_ctx else {})}

    # Preserve any explicit input payload while filling task/context defaults
    input_payload = dict(step.get("input", {}))
    input_payload.setdefault("task", step.get("task") or f"agent:{agent_id}")
    input_payload.setdefault("context", merged_context if merged_context else step.get("context", {}))

    normalized = dict(step)
    normalized.pop("type", None)
    normalized["tool"] = f"agent_{agent_id}"
    normalized["input"] = input_payload
    return normalized


async def run_step(step: dict[str, Any], step_outputs: dict[str, Any], mcp_client: MCPClientShim, monitor: ToolUsageMonitor | None = None, a2a_client: A2AClient | None = None) -> Any:
    """
    Execute a single step using the hybrid dispatcher.

    Supports retry policy and delegates to hybrid_dispatcher for tool routing.

    Args:
        step: Step definition with tool type, input, and config
        step_outputs: Dict of previous step outputs
        mcp_client: MCP client for deterministic tools
        monitor: Optional ToolUsageMonitor for observability
        a2a_client: Optional A2A client for agent delegation

    Returns:
        Result from the executed step
    """
    start_time = datetime.now()
    # Agent steps: delegate directly with helper for parity and monitoring
    if step.get("type") == "agent":
        step_id = step.get('id', 'unknown')
        tool_name = f"agent_{step.get('agent_id', 'unknown')}"

        async def call_agent() -> Any:
            return await execute_agent_step(step, step_outputs, a2a_client, monitor)

        retries = step.get('retry_policy', {}).get('retries', 1) if step.get('retry_policy') else 1
        backoff = step.get('retry_policy', {}).get('backoff_s', 1) if step.get('retry_policy') else 1

        try:
            result = await retry(partial(call_agent), retries=retries, backoff_s=backoff)
            if monitor:
                latency = (datetime.now() - start_time).total_seconds()
                monitor.log_tool_call(tool_name, success=True, latency=latency, execution_id=step_id)
            return result
        except Exception as e:
            if monitor:
                latency = (datetime.now() - start_time).total_seconds()
                monitor.log_tool_call(tool_name, success=False, latency=latency, error=str(e), execution_id=step_id)
            raise

    normalized_step = _normalize_step_for_dispatch(step, step_outputs)
    step_id = normalized_step.get('id', 'unknown')
    tool_name = normalized_step.get('tool', 'unknown')

    async def call() -> Any:
        return await dispatch_step(normalized_step, step_outputs, mcp_client, monitor, a2a_client)

    try:
        retries = normalized_step.get('retry_policy', {}).get('retries', 1) if normalized_step.get('retry_policy') else 1
        backoff = normalized_step.get('retry_policy', {}).get('backoff_s', 1) if normalized_step.get('retry_policy') else 1
        result = await retry(partial(call), retries=retries, backoff_s=backoff)

        # Log successful step execution
        if monitor:
            latency = (datetime.now() - start_time).total_seconds()
            monitor.log_tool_call(tool_name, success=True, latency=latency, execution_id=step_id)

        return result
    except Exception as e:
        # Log failed step execution
        if monitor:
            latency = (datetime.now() - start_time).total_seconds()
            monitor.log_tool_call(tool_name, success=False, latency=latency, error=str(e), execution_id=step_id)
        raise

async def execute_plan(plan: dict[str, Any], *, a2a_client: A2AClient | None = None) -> dict[str, Any]:
    """
    Execute a multi-step execution plan with dependency resolution.

    This orchestrator supports hybrid tool types:
    - MCP workers (deterministic tools)
    - Function calls (structured APIs)
    - Code execution (sandboxed Python)

    Args:
        plan: Plan dictionary with steps and final_synthesis config
        a2a_client: Optional A2A client for agent delegation

    Returns:
        Context dictionary with all step outputs

    Raises:
        RuntimeError: If plan is invalid, cyclic, or step execution fails
    """
    PlanModel(**plan)  # validate
    steps = {s['id']: s for s in plan['steps']}
    pending = set(steps.keys())
    completed: dict[str, Any] = {}
    mcp_client = MCPClientShim()
    a2a_client = a2a_client or None
    monitor = get_monitor()

    def ready_steps() -> list[str]:
        """Find steps whose dependencies are all completed."""
        return [sid for sid in pending if all(dep in completed for dep in steps[sid].get('depends_on', []))]

    # Log plan start
    plan.get('request_id', 'unknown')
    logger.info(f"Starting plan execution with {len(steps)} steps")

    while pending:
        ready = ready_steps()
        if not ready:
            raise RuntimeError(f"Stuck or cyclic plan; pending={pending}, completed={list(completed.keys())}")

        logger.info(f"Executing {len(ready)} ready steps: {ready}")
        coros = [run_step(steps[sid], completed, mcp_client, monitor, a2a_client) for sid in ready]
        results = await asyncio.gather(*coros, return_exceptions=True)

        for sid, res in zip(ready, results, strict=False):
            if isinstance(res, Exception):
                logger.exception("Step failed %s", sid)
                raise RuntimeError(f"Step {sid} failed: {res}")
            else:
                logger.info(f"Step {sid} completed successfully")
                completed[sid] = res
                pending.remove(sid)

    context = { 'steps': completed }
    logger.info("Plan execution completed successfully")

    # Flush monitoring logs to backends
    if monitor:
        monitor.flush()

    return context

async def final_synthesis(plan: dict[str, Any], context: dict[str, Any]) -> dict[str, str]:
    """
    Generate final synthesis from execution context.

    Args:
        plan: Plan with final_synthesis configuration
        context: Execution context with step outputs

    Returns:
        Dict with synthesis text
    """
    template = plan['final_synthesis']['prompt_template']
    filled = template.replace("{{steps}}", json.dumps(context, indent=2))
    logger.info("Generated final synthesis")
    return { 'synthesis': f"SYNTHESIS_PLACEHOLDER\n{filled}" }


class Orchestrator:
    """
    Simple facade for examples: provides discovery, tool calls, and agent delegation.

    - Uses MCPClientShim for deterministic tool calls
    - Uses A2AClient for agent delegation (reads agents.yaml by default)
    - Logs via ToolUsageMonitor when available
    """

    def __init__(
        self,
        catalog: ToolCatalog | None = None,
        *,
        agents_config_path: str | None = None,
        registry_url: str | None = None,
        monitoring: ToolUsageMonitor | None = None
    ):
        # catalog is accepted for backward compatibility; discovery still uses registry by default.
        self._catalog = catalog
        self.mcp = MCPClientShim()
        self.registry_url = registry_url or os.getenv("MCP_REGISTRY_URL")
        cfg = agents_config_path or os.getenv("AGENTS_CONFIG")
        if cfg is None and os.path.exists("agents.yaml"):
            cfg = "agents.yaml"
        self.a2a = A2AClient(config_path=cfg) if cfg else None
        self._monitor = monitoring or get_monitor()

    async def discover_tools(self, *, use_cache: bool = True) -> list[Any]:
        try:
            from ...tools.tool_discovery import discover_tools
        except ImportError as exc:
            raise RuntimeError("tool_discovery module not available") from exc
        function_modules = None
        catalog = await discover_tools(
            mcp_client=self.mcp,
            function_modules=function_modules,
            include_code_exec=True,
            use_cache=use_cache,
            a2a_client=self.a2a,
            registry_url=self.registry_url,
        )
        return list(catalog.tools) if isinstance(catalog.tools, list) else []

    async def execute_tool(self, name: str, params: dict[str, Any]) -> Any:
        start = datetime.now()
        try:
            result = await self.mcp.call_tool(name, params)
            if self._monitor:
                self._monitor.log_tool_call(name, success=True, latency=(datetime.now() - start).total_seconds())
            return result
        except Exception as e:
            if self._monitor:
                self._monitor.log_tool_call(name, success=False, latency=(datetime.now() - start).total_seconds(), error=str(e))
            raise

    async def execute_agent_step(self, *, agent_name: str, request: dict[str, Any], stream: bool = False) -> Any:
        if not self.a2a:
            raise RuntimeError("A2A client not configured. Provide agents_config_path or AGENTS_CONFIG.")
        req = AgentDelegationRequest(agent_id=agent_name, task=request.get("task", agent_name), context=request, timeout=request.get("timeout", 300))
        if stream:
            # Basic emulate by collecting streamed chunks if implemented in future
            resp = await self.a2a.delegate_to_agent(req)
            return resp.result
        resp = await self.a2a.delegate_to_agent(req)
        if not resp.success:
            raise RuntimeError(resp.metadata.get("error", "Agent delegation failed"))
        return resp.result
    async def execute_skill(self, skill_name: str, *, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute a saved skill (code snippet or workflow).

        Automatically tracks metrics (usage, latency, success rate).

        Args:
            skill_name: Name of the skill (must be saved in library)
            inputs: Optional input variables to pass to the skill

        Returns:
            Result from executing the skill code

        Raises:
            KeyError: If skill not found
            RuntimeError: If skill execution fails
        """
        try:
            from ..execution.skill_library import get_skill
            from ..execution.skill_metrics import SkillExecutionTimer
            from ..execution.validation import validate_stub
        except ImportError as exc:
            raise RuntimeError("Skill execution modules not available") from exc
        from pathlib import Path

        start = datetime.now()

        try:
            # Use timer context manager for automatic metrics tracking
            with SkillExecutionTimer(skill_name):
                skill = get_skill(skill_name)
                if not skill:
                    raise KeyError(f"Skill not found: {skill_name}")

                code = Path(skill.code_path).read_text()

                # Validate syntax at minimum
                validation = validate_stub(code, check_syntax=True)
                if not validation["valid"]:
                    raise RuntimeError(f"Skill {skill_name} failed validation: {validation['syntax']['error']}")

                # Execute in sandbox with optional inputs
                scope: dict[str, Any] = {}
                if inputs:
                    scope.update(inputs)
                exec(code, scope)

                # Extract result (by convention, last non-private assignment or explicit return)
                result = {k: v for k, v in scope.items() if not k.startswith("_")}

                if self._monitor:
                    self._monitor.log_tool_call(f"skill:{skill_name}", success=True, latency=(datetime.now() - start).total_seconds())

                return result
        except Exception as e:
            if self._monitor:
                self._monitor.log_tool_call(f"skill:{skill_name}", success=False, latency=(datetime.now() - start).total_seconds(), error=str(e))
            raise
