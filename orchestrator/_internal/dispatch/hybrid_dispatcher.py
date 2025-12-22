"""
Hybrid dispatcher for orchestrating MCP workers, function calls, and code execution.

This module provides a unified interface for dispatching to:
- MCP Workers: Deterministic, safe tools (OCR, parser, categorizer)
- Function Call Workers: Structured API calls with schema enforcement
- Code-Exec Workers: Dynamic transformations in sandboxed environment
"""

import asyncio
import logging
from typing import Dict, Any, Callable, Optional
from .execution.code_exec_worker import code_exec_worker
from ..shared.models import FunctionCallInput, FunctionCallOutput
from .infra.a2a_client import AgentDelegationRequest

logger = logging.getLogger(__name__)

# Global function registry for structured function calls
_function_map: Dict[str, Callable] = {}


def register_function(name: str):
    """
    Decorator to register a function for structured function calls.
    
    Usage:
        @register_function("my_function")
        def my_function(arg1: str, arg2: int) -> dict:
            return {"result": arg1 * arg2}
    """
    def decorator(func):
        _function_map[name] = func
        logger.info(f"Registered function: {name}")
        return func
    return decorator


def get_registered_functions() -> Dict[str, Callable]:
    """Return all registered functions."""
    return _function_map.copy()


async def function_call_worker(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a registered function with validated inputs.
    
    Args:
        payload: Dict containing 'name' and 'args' keys
        
    Returns:
        Dict with 'result' key containing function output
        
    Raises:
        RuntimeError: If function name is not registered
    """
    validated = FunctionCallInput(**payload)
    func = _function_map.get(validated.name)
    
    if not func:
        available = ', '.join(_function_map.keys())
        raise RuntimeError(
            f"Unknown function: {validated.name}. "
            f"Available functions: {available or 'none'}"
        )
    
    logger.info(f"Executing function call: {validated.name}")
    try:
        result = func(**validated.args)
        return FunctionCallOutput(result=result).model_dump()
    except Exception as e:
        logger.error(f"Function call failed: {validated.name}", exc_info=True)
        raise RuntimeError(f"Function '{validated.name}' execution failed: {e}")


async def dispatch_step(
    step: Dict[str, Any],
    step_outputs: Dict[str, Any],
    mcp_client: Any,
    monitor: Optional[Any] = None,
    a2a_client: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Main hybrid dispatcher that routes to appropriate worker based on tool type.
    
    Args:
        step: Step definition containing tool type and input
        step_outputs: Dictionary of previous step outputs for reference resolution
        mcp_client: MCP client instance for deterministic tools
        
    Returns:
        Result dictionary from the executed worker
        
    Raises:
        RuntimeError: If tool type is unknown or execution fails
    """
    tool_type = step['tool']
    
    # Resolve input references from previous steps
    resolved_input = {}
    for k, v in step.get('input', {}).items():
        if isinstance(v, str) and v.startswith("step:"):
            ref = v.split("step:", 1)[1]
            resolved_input[k] = step_outputs.get(ref)
        elif isinstance(v, dict):
            # Recursively resolve nested references
            resolved_input[k] = _resolve_nested(v, step_outputs)
        elif isinstance(v, list):
            # Resolve references in lists
            resolved_input[k] = [
                step_outputs.get(item.split("step:", 1)[1]) if isinstance(item, str) and item.startswith("step:") else item
                for item in v
            ]
        else:
            resolved_input[k] = v
    
    logger.info(f"Dispatching tool: {tool_type}")
    
    # Route to appropriate worker
    if tool_type in mcp_client.tool_map:
        # MCP deterministic tool (supports optional streaming)
        if step.get("stream"):
            chunks = []
            async for chunk in mcp_client.call_tool_stream(
                tool_type,
                resolved_input,
                timeout=step.get('timeout_s', 30),
                chunk_timeout=step.get('chunk_timeout_s'),
            ):
                chunks.append(chunk)
            return {"chunks": chunks}
        return await mcp_client.call_tool(
            tool_type,
            resolved_input,
            idempotency_key=step.get('idempotency_key'),
            timeout=step.get('timeout_s', 30)
        )
    elif tool_type.startswith("agent_") and a2a_client:
        agent_id = tool_type[len("agent_"):]
        task = resolved_input.get("task") or step.get("task") or tool_type
        context = resolved_input.get("context", resolved_input)
        req = AgentDelegationRequest(
            agent_id=agent_id,
            task=task,
            context=context if isinstance(context, dict) else {"context": context},
            timeout=step.get('timeout_s', 30),
            idempotency_key=step.get('idempotency_key'),
            metadata=step.get('metadata', {}),
        )

        if step.get("stream"):
            chunks = []
            async for chunk in a2a_client.delegate_stream(
                req,
                chunk_timeout=step.get('chunk_timeout_s'),
            ):
                chunks.append(chunk)
            return {"chunks": chunks}
        resp = await a2a_client.delegate_to_agent(req)
        return resp.result
    elif tool_type == "function_call":
        # Structured function call
        return await function_call_worker(resolved_input)
    elif tool_type == "code_exec":
        # Sandboxed code execution
        return await code_exec_worker(resolved_input)
    else:
        available_mcp = ', '.join(mcp_client.tool_map.keys())
        available_funcs = ', '.join(_function_map.keys())
        raise RuntimeError(
            f"Unknown tool type: {tool_type}. "
            f"Available MCP tools: {available_mcp}. "
            f"Available functions: {available_funcs or 'none'}. "
            f"Also supports: code_exec, function_call"
        )


def _resolve_nested(obj: Dict[str, Any], step_outputs: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively resolve step references in nested dictionaries."""
    resolved = {}
    for k, v in obj.items():
        if isinstance(v, str) and v.startswith("step:"):
            ref = v.split("step:", 1)[1]
            resolved[k] = step_outputs.get(ref)
        elif isinstance(v, dict):
            resolved[k] = _resolve_nested(v, step_outputs)
        elif isinstance(v, list):
            resolved[k] = [
                step_outputs.get(item.split("step:", 1)[1]) if isinstance(item, str) and item.startswith("step:") else item
                for item in v
            ]
        else:
            resolved[k] = v
    return resolved
