"""
Tool Executor

Executes tool calls from generated stubs, routing to appropriate backends.

Features:
- Route to MCP servers
- Route to programmatic functions
- Handle errors and timeouts
- Track metrics

Usage:
    result = await call_tool(
        server="google_drive",
        tool_name="get_document",
        parameters={"doc_id": "123"}
    )
"""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def call_tool(
    server: str,
    tool_name: str,
    parameters: dict[str, Any],
    timeout: int = 30
) -> Any:
    """
    Execute a tool call, routing to the appropriate backend.

    Args:
        server: Server/domain name (e.g., "google_drive", "default")
        tool_name: Name of tool to execute
        parameters: Tool parameters
        timeout: Execution timeout in seconds

    Returns:
        Tool execution result

    Raises:
        TimeoutError: If execution exceeds timeout
        Exception: If tool execution fails
    """
    logger.info(f"Executing tool: {server}/{tool_name}")
    logger.debug(f"Parameters: {parameters}")

    try:
        # Route to appropriate backend
        if server == "default" or server == "function":
            # Programmatic function
            result = await _execute_function(tool_name, parameters, timeout)
        else:
            # MCP server
            result = await _execute_mcp_tool(server, tool_name, parameters, timeout)

        logger.info(f"Tool {tool_name} executed successfully")
        return result

    except asyncio.TimeoutError:
        logger.error(f"Tool {tool_name} timed out after {timeout}s")
        raise TimeoutError(f"Tool execution timed out after {timeout}s")

    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        raise


async def _execute_function(
    tool_name: str,
    parameters: dict[str, Any],
    timeout: int
) -> Any:
    """Execute a programmatic Python function"""
    from orchestrator._internal.dispatch import functions

    # Get function by name
    if not hasattr(functions, tool_name):
        raise AttributeError(f"Function not found: {tool_name}")

    func = getattr(functions, tool_name)

    # Execute with timeout
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(func, **parameters),
            timeout=timeout
        )
        return result
    except TypeError as e:
        # Try without unpacking if signature doesn't match
        logger.warning(f"Parameter mismatch for {tool_name}, trying direct call: {e}")
        result = await asyncio.wait_for(
            asyncio.to_thread(func, parameters),
            timeout=timeout
        )
        return result


async def _execute_mcp_tool(
    server: str,
    tool_name: str,
    parameters: dict[str, Any],
    timeout: int
) -> Any:
    """Execute an MCP server tool"""
    from orchestrator._internal.infra.mcp_client import MCPClientShim

    # Create shim client and execute tool
    client = MCPClientShim()
    result = await asyncio.wait_for(
        client.call_tool(tool_name, parameters),
        timeout=timeout,
    )
    return result
