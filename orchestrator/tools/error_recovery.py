"""Error recovery for tool execution with fallback and retry strategies."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    attempts: int = 0
    strategy_used: str = ""


class ErrorRecoveryExecutor:
    """Execute tools with error recovery policies."""
    
    async def execute_with_recovery(
        self,
        tool_func: Callable,
        tool_name: str,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        policy: Optional[Any] = None,  # ErrorRecoveryPolicy
        fallback_tools: Optional[List[Callable]] = None,
    ) -> RecoveryResult:
        """Execute tool with retry/fallback/partial success handling."""
        if kwargs is None:
            kwargs = {}
        
        if fallback_tools is None:
            fallback_tools = []
        
        # Extract policy settings
        max_retries = getattr(policy, "max_retries", 0) if policy else 0
        strategy = getattr(policy, "strategy", "raise") if policy else "raise"
        backoff = getattr(policy, "retry_backoff", 1.0) if policy else 1.0
        timeout_override = getattr(policy, "timeout_override", None) if policy else None
        
        # Try main tool with retries
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(*args, **kwargs)
                else:
                    result = tool_func(*args, **kwargs)
                
                return RecoveryResult(
                    success=True,
                    result=result,
                    attempts=attempt + 1,
                    strategy_used="main",
                )
            except Exception as e:
                logger.warning(
                    f"{tool_name} attempt {attempt + 1} failed: {e}"
                )
                if attempt < max_retries:
                    # Backoff before retry
                    wait_time = backoff ** attempt
                    await asyncio.sleep(wait_time)
                elif strategy == "raise":
                    return RecoveryResult(
                        success=False,
                        error=e,
                        attempts=attempt + 1,
                        strategy_used="main_failed_raise",
                    )
                elif strategy == "continue":
                    return RecoveryResult(
                        success=False,
                        error=e,
                        attempts=attempt + 1,
                        strategy_used="main_failed_continue",
                    )
                elif strategy == "fallback":
                    # Try fallback tools
                    return await self._try_fallback_tools(
                        fallback_tools, args, kwargs, attempt + 1
                    )
                elif strategy == "partial_success":
                    return RecoveryResult(
                        success=False,
                        result={"partial": True},
                        error=e,
                        attempts=attempt + 1,
                        strategy_used="partial_success",
                    )
        
        # Shouldn't reach here, but handle gracefully
        return RecoveryResult(
            success=False,
            error=Exception(f"{tool_name} exhausted retries"),
            attempts=max_retries + 1,
            strategy_used="exhausted",
        )
    
    async def _try_fallback_tools(
        self,
        fallback_tools: List[Callable],
        args: tuple,
        kwargs: Dict[str, Any],
        initial_attempts: int,
    ) -> RecoveryResult:
        """Try fallback tools sequentially."""
        for i, fallback in enumerate(fallback_tools):
            try:
                if asyncio.iscoroutinefunction(fallback):
                    result = await fallback(*args, **kwargs)
                else:
                    result = fallback(*args, **kwargs)
                
                return RecoveryResult(
                    success=True,
                    result=result,
                    attempts=initial_attempts + i,
                    strategy_used=f"fallback_{i}",
                )
            except Exception as e:
                logger.warning(
                    f"Fallback {i} failed: {e}"
                )
        
        return RecoveryResult(
            success=False,
            error=Exception(f"All {len(fallback_tools)} fallback tools failed"),
            attempts=initial_attempts + len(fallback_tools),
            strategy_used="all_fallbacks_failed",
        )
