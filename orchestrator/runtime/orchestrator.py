import asyncio, json, logging, os
from functools import partial
from ..models import PlanModel
from ..infra.mcp_client import MCPClientShim
from ..dispatch.hybrid_dispatcher import dispatch_step
from ..observability.monitoring import ToolUsageMonitor
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global monitor instance (initialized on first use)
_monitor = None

def get_monitor():
    """Get or create the global monitoring instance."""
    global _monitor
    if _monitor is None:
        backends_str = os.getenv("MONITORING_BACKENDS", "local")
        backends = [b.strip() for b in backends_str.split(',')]
        _monitor = ToolUsageMonitor(backends=backends)
        logger.info(f"Monitoring initialized with backends: {backends}")
    return _monitor

async def retry(coro_func, retries=1, backoff_s=1):
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
    last_exc = None
    for attempt in range(1, retries+1):
        try:
            return await coro_func()
        except Exception as e:
            last_exc = e
            logger.warning("Attempt %s failed: %s", attempt, e)
            if attempt < retries:
                await asyncio.sleep(backoff_s * attempt)
    raise last_exc

async def run_step(step, step_outputs, mcp_client, monitor=None):
    """
    Execute a single step using the hybrid dispatcher.
    
    Supports retry policy and delegates to hybrid_dispatcher for tool routing.
    
    Args:
        step: Step definition with tool type, input, and config
        step_outputs: Dict of previous step outputs
        mcp_client: MCP client for deterministic tools
        monitor: Optional ToolUsageMonitor for observability
        
    Returns:
        Result from the executed step
    """
    start_time = datetime.now()
    step_id = step.get('id', 'unknown')
    tool_name = step.get('tool', 'unknown')
    
    async def call():
        return await dispatch_step(step, step_outputs, mcp_client, monitor)
    
    try:
        retries = step.get('retry_policy', {}).get('retries', 1) if step.get('retry_policy') else 1
        backoff = step.get('retry_policy', {}).get('backoff_s', 1) if step.get('retry_policy') else 1
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

async def execute_plan(plan):
    """
    Execute a multi-step execution plan with dependency resolution.
    
    This orchestrator supports hybrid tool types:
    - MCP workers (deterministic tools)
    - Function calls (structured APIs)
    - Code execution (sandboxed Python)
    
    Args:
        plan: Plan dictionary with steps and final_synthesis config
        
    Returns:
        Context dictionary with all step outputs
        
    Raises:
        RuntimeError: If plan is invalid, cyclic, or step execution fails
    """
    PlanModel(**plan)  # validate
    steps = {s['id']: s for s in plan['steps']}
    pending = set(steps.keys())
    completed = {}
    mcp_client = MCPClientShim()
    monitor = get_monitor()

    def ready_steps():
        """Find steps whose dependencies are all completed."""
        return [sid for sid in pending if all(dep in completed for dep in steps[sid].get('depends_on', []))]

    # Log plan start
    plan_id = plan.get('request_id', 'unknown')
    logger.info(f"Starting plan execution with {len(steps)} steps")
    
    while pending:
        ready = ready_steps()
        if not ready:
            raise RuntimeError(f"Stuck or cyclic plan; pending={pending}, completed={list(completed.keys())}")
        
        logger.info(f"Executing {len(ready)} ready steps: {ready}")
        coros = [run_step(steps[sid], completed, mcp_client, monitor) for sid in ready]
        results = await asyncio.gather(*coros, return_exceptions=True)
        
        for sid, res in zip(ready, results):
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

async def final_synthesis(plan, context):
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
