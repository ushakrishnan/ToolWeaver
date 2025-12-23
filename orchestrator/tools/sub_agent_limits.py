"""
Sub-Agent Resource Quotas for Safe Multi-Agent Dispatch

This module provides resource limits and quota tracking for parallel agent dispatch,
preventing cost exhaustion, recursive spawning, and DoS attacks.

Threats Mitigated:
- AS-1: Cost Bomb ($1000s+ in one dispatch)
- AS-2: Recursive Agent Spawn (exponential DoS)
"""

from dataclasses import dataclass, field
from typing import Optional
import time
import asyncio


@dataclass
class DispatchResourceLimits:
    """
    Aggregate resource limits for parallel agent dispatch.
    
    These limits prevent resource exhaustion and attacks during multi-agent orchestration.
    """
    
    # Cost controls
    max_total_cost_usd: Optional[float] = 5.0  # Default: $5 per dispatch
    cost_per_agent_estimate: float = 0.01  # Estimate for pre-check (in USD)
    
    # Concurrency controls
    max_concurrent: Optional[int] = 10  # Max agents running at once
    max_total_agents: Optional[int] = 100  # Total agents in one dispatch
    
    # Time controls
    max_agent_duration_s: Optional[float] = 300.0  # 5 min per agent
    max_total_duration_s: Optional[float] = 600.0  # 10 min total dispatch
    
    # Rate limiting
    requests_per_second: Optional[float] = 10.0  # Max API requests/sec
    
    # Failure controls
    max_failure_rate: Optional[float] = 0.3  # Fail-fast if >30% fail
    min_success_count: int = 0  # Require explicit opt-in for success threshold
    
    # Recursion controls
    max_dispatch_depth: int = 3  # Max nested dispatch levels
    current_depth: int = 0  # Current nesting level


class DispatchQuotaExceeded(Exception):
    """Raised when dispatch exceeds resource quotas."""
    pass


class DispatchLimitTracker:
    """
    Tracks and enforces resource limits during agent dispatch.
    
    Usage:
        limits = DispatchResourceLimits(max_total_cost_usd=10.0)
        tracker = DispatchLimitTracker(limits)
        
        # Pre-check before dispatch
        tracker.check_pre_dispatch(num_agents=100)
        
        # Track during execution
        tracker.record_agent_completion(cost=0.05, success=True)
    """
    
    def __init__(self, limits: DispatchResourceLimits):
        self.limits = limits
        self.start_time = time.time()
        
        # Runtime tracking
        self.total_cost = 0.0
        self.total_agents = 0
        self.completed_agents = 0
        self.failed_agents = 0
        self.concurrent_count = 0
        
        # Thread safety
        self._lock = asyncio.Lock()
    
    def check_pre_dispatch(self, num_agents: int) -> None:
        """
        Validate dispatch request BEFORE starting.
        
        Raises:
            DispatchQuotaExceeded: If dispatch would exceed limits
        """
        # Check recursion depth
        if self.limits.max_dispatch_depth is not None:
            if self.limits.current_depth > self.limits.max_dispatch_depth:
                raise DispatchQuotaExceeded(
                    f"Recursion depth {self.limits.current_depth} exceeds max "
                    f"{self.limits.max_dispatch_depth}"
                )
        
        # Check total agent count
        if self.limits.max_total_agents is not None:
            if num_agents > self.limits.max_total_agents:
                raise DispatchQuotaExceeded(
                    f"Requested {num_agents} agents exceeds max {self.limits.max_total_agents}"
                )
        
        # Check estimated cost
        if self.limits.max_total_cost_usd is not None:
            estimated_cost = num_agents * self.limits.cost_per_agent_estimate
            if estimated_cost > self.limits.max_total_cost_usd:
                raise DispatchQuotaExceeded(
                    f"Estimated cost ${estimated_cost:.2f} exceeds budget "
                    f"${self.limits.max_total_cost_usd:.2f}"
                )
    
    async def record_agent_completion(
        self,
        cost: float,
        success: bool,
        duration: Optional[float] = None
    ) -> None:
        """
        Track agent completion and enforce runtime limits.
        
        Args:
            cost: Actual cost in USD
            success: Whether agent succeeded
            duration: Agent execution time in seconds
            
        Raises:
            DispatchQuotaExceeded: If limits exceeded during execution
        """
        async with self._lock:
            # Update counters
            self.completed_agents += 1
            self.total_cost += cost
            
            if not success:
                self.failed_agents += 1
            
            # Check cost limit
            if self.limits.max_total_cost_usd is not None:
                if self.total_cost > self.limits.max_total_cost_usd:
                    raise DispatchQuotaExceeded(
                        f"Total cost ${self.total_cost:.2f} exceeds budget "
                        f"${self.limits.max_total_cost_usd:.2f}"
                    )
            
            # Check failure rate (fail-fast)
            if self.completed_agents >= 5:  # Only check after reasonable sample
                failure_rate = self.failed_agents / self.completed_agents
                if self.limits.max_failure_rate is not None:
                    if failure_rate > self.limits.max_failure_rate:
                        raise DispatchQuotaExceeded(
                            f"Failure rate {failure_rate:.1%} exceeds max "
                            f"{self.limits.max_failure_rate:.1%}"
                        )
            
            # Check agent duration
            if duration and self.limits.max_agent_duration_s is not None:
                if duration > self.limits.max_agent_duration_s:
                    raise DispatchQuotaExceeded(
                        f"Agent duration {duration:.1f}s exceeds max "
                        f"{self.limits.max_agent_duration_s:.1f}s"
                    )
            
            # Check total dispatch duration
            if self.limits.max_total_duration_s is not None:
                elapsed = time.time() - self.start_time
                if elapsed > self.limits.max_total_duration_s:
                    raise DispatchQuotaExceeded(
                        f"Total dispatch duration {elapsed:.1f}s exceeds max "
                        f"{self.limits.max_total_duration_s:.1f}s"
                    )
    
    async def acquire_slot(self) -> None:
        """
        Acquire a concurrency slot (blocks if at max concurrent).
        Call this before starting an agent.
        """
        while True:
            async with self._lock:
                if self.limits.max_concurrent is None or \
                   self.concurrent_count < self.limits.max_concurrent:
                    self.concurrent_count += 1
                    self.total_agents += 1
                    return
            
            # Wait before retrying
            await asyncio.sleep(0.1)
    
    async def release_slot(self) -> None:
        """
        Release a concurrency slot after agent completes.
        """
        async with self._lock:
            self.concurrent_count -= 1
    
    def get_stats(self) -> dict:
        """Return current dispatch statistics."""
        elapsed = time.time() - self.start_time
        
        return {
            "total_agents": self.total_agents,
            "completed_agents": self.completed_agents,
            "failed_agents": self.failed_agents,
            "concurrent_count": self.concurrent_count,
            "total_cost_usd": self.total_cost,
            "elapsed_seconds": elapsed,
            "failure_rate": self.failed_agents / self.completed_agents if self.completed_agents > 0 else 0.0,
        }
