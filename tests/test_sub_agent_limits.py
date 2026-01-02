"""
Tests for sub-agent resource quotas and limit tracking.
"""

import asyncio

import pytest

from orchestrator.tools.sub_agent_limits import (
    DispatchLimitTracker,
    DispatchQuotaExceeded,
    DispatchResourceLimits,
)


class TestDispatchResourceLimits:
    """Test the DispatchResourceLimits dataclass."""

    def test_default_limits(self):
        """Test default limit values."""
        limits = DispatchResourceLimits()

        assert limits.max_total_cost_usd == 5.0
        assert limits.cost_per_agent_estimate == 0.01
        assert limits.max_concurrent == 10
        assert limits.max_total_agents == 100
        assert limits.max_agent_duration_s == 300.0
        assert limits.max_total_duration_s == 600.0
        assert limits.requests_per_second == 10.0
        assert limits.max_failure_rate == 0.3
        assert limits.min_success_count == 0  # Default is 0, requires explicit opt-in
        assert limits.max_dispatch_depth == 3
        assert limits.current_depth == 0

    def test_custom_limits(self):
        """Test custom limit configuration."""
        limits = DispatchResourceLimits(
            max_total_cost_usd=10.0,
            max_concurrent=5,
            max_dispatch_depth=2,
        )

        assert limits.max_total_cost_usd == 10.0
        assert limits.max_concurrent == 5
        assert limits.max_dispatch_depth == 2


class TestDispatchLimitTracker:
    """Test the DispatchLimitTracker enforcement."""

    def test_pre_dispatch_agent_count_limit(self):
        """Test pre-dispatch agent count validation."""
        limits = DispatchResourceLimits(max_total_agents=50)
        tracker = DispatchLimitTracker(limits)

        # Should pass
        tracker.check_pre_dispatch(num_agents=50)

        # Should fail
        with pytest.raises(DispatchQuotaExceeded, match="exceeds max 50"):
            tracker.check_pre_dispatch(num_agents=51)

    def test_pre_dispatch_cost_limit(self):
        """Test pre-dispatch cost estimation validation."""
        limits = DispatchResourceLimits(
            max_total_cost_usd=5.0,
            cost_per_agent_estimate=0.10,
        )
        tracker = DispatchLimitTracker(limits)

        # Should pass: 40 agents × $0.10 = $4.00
        tracker.check_pre_dispatch(num_agents=40)

        # Should fail: 60 agents × $0.10 = $6.00 > $5.00
        with pytest.raises(DispatchQuotaExceeded, match="Estimated cost"):
            tracker.check_pre_dispatch(num_agents=60)

    def test_pre_dispatch_recursion_depth_limit(self):
        """Test recursion depth enforcement."""
        limits = DispatchResourceLimits(
            max_dispatch_depth=2,
            current_depth=3,  # Already too deep
        )
        tracker = DispatchLimitTracker(limits)

        with pytest.raises(DispatchQuotaExceeded, match="Recursion depth"):
            tracker.check_pre_dispatch(num_agents=10)

    @pytest.mark.asyncio
    async def test_runtime_cost_enforcement(self):
        """Test cost limit enforcement during execution."""
        limits = DispatchResourceLimits(max_total_cost_usd=1.0)
        tracker = DispatchLimitTracker(limits)

        # First few agents should pass
        await tracker.record_agent_completion(cost=0.20, success=True)
        await tracker.record_agent_completion(cost=0.30, success=True)

        assert tracker.total_cost == 0.50

        # Next agent pushes over limit
        with pytest.raises(DispatchQuotaExceeded, match="Total cost"):
            await tracker.record_agent_completion(cost=0.60, success=True)

    @pytest.mark.asyncio
    async def test_failure_rate_enforcement(self):
        """Test fail-fast on high failure rate."""
        limits = DispatchResourceLimits(max_failure_rate=0.3)
        tracker = DispatchLimitTracker(limits)

        # 2 successes, 3 failures = 60% failure rate
        await tracker.record_agent_completion(cost=0.01, success=True)
        await tracker.record_agent_completion(cost=0.01, success=True)
        await tracker.record_agent_completion(cost=0.01, success=False)
        await tracker.record_agent_completion(cost=0.01, success=False)

        # 5th completion triggers check: 2 success, 3 fail = 60% > 30%
        with pytest.raises(DispatchQuotaExceeded, match="Failure rate"):
            await tracker.record_agent_completion(cost=0.01, success=False)

    @pytest.mark.asyncio
    async def test_agent_duration_enforcement(self):
        """Test individual agent duration limit."""
        limits = DispatchResourceLimits(max_agent_duration_s=10.0)
        tracker = DispatchLimitTracker(limits)

        # Short duration should pass
        await tracker.record_agent_completion(
            cost=0.01,
            success=True,
            duration=5.0
        )

        # Long duration should fail
        with pytest.raises(DispatchQuotaExceeded, match="Agent duration"):
            await tracker.record_agent_completion(
                cost=0.01,
                success=True,
                duration=15.0
            )

    @pytest.mark.asyncio
    async def test_total_duration_enforcement(self):
        """Test total dispatch wall-clock timeout."""
        limits = DispatchResourceLimits(max_total_duration_s=0.5)
        tracker = DispatchLimitTracker(limits)

        # Wait past timeout
        await asyncio.sleep(0.6)

        # Should fail due to elapsed time
        with pytest.raises(DispatchQuotaExceeded, match="Total dispatch duration"):
            await tracker.record_agent_completion(cost=0.01, success=True)

    @pytest.mark.asyncio
    async def test_concurrency_slot_management(self):
        """Test concurrency slot acquire/release."""
        limits = DispatchResourceLimits(max_concurrent=2)
        tracker = DispatchLimitTracker(limits)

        # Acquire 2 slots (should succeed)
        await tracker.acquire_slot()
        await tracker.acquire_slot()

        assert tracker.concurrent_count == 2
        assert tracker.total_agents == 2

        # Try to acquire 3rd slot (should block briefly)
        async def try_acquire():
            await asyncio.sleep(0.1)
            await tracker.release_slot()  # Release one

        acquire_task = asyncio.create_task(try_acquire())
        await tracker.acquire_slot()  # Should succeed after release
        await acquire_task

        assert tracker.concurrent_count == 2
        assert tracker.total_agents == 3

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test statistics reporting."""
        limits = DispatchResourceLimits()
        tracker = DispatchLimitTracker(limits)

        await tracker.record_agent_completion(cost=0.50, success=True)
        await tracker.record_agent_completion(cost=0.30, success=False)

        stats = tracker.get_stats()

        assert stats["completed_agents"] == 2
        assert stats["failed_agents"] == 1
        assert stats["total_cost_usd"] == 0.80
        assert stats["failure_rate"] == 0.5
        assert stats["elapsed_seconds"] > 0

    def test_no_limits(self):
        """Test that None limits are not enforced."""
        limits = DispatchResourceLimits(
            max_total_cost_usd=None,
            max_total_agents=None,
            max_concurrent=None,
        )
        tracker = DispatchLimitTracker(limits)

        # Should not raise even with large values
        tracker.check_pre_dispatch(num_agents=10000)


class TestThreadSafety:
    """Test concurrent access to tracker."""

    @pytest.mark.asyncio
    async def test_concurrent_completions(self):
        """Test thread-safe completion recording."""
        limits = DispatchResourceLimits(max_total_cost_usd=100.0)
        tracker = DispatchLimitTracker(limits)

        async def record_many():
            for _ in range(10):
                await tracker.record_agent_completion(cost=0.10, success=True)

        # Run 5 tasks concurrently
        await asyncio.gather(*[record_many() for _ in range(5)])

        # Should have 50 completions, ~$5 total cost (floating point)
        assert tracker.completed_agents == 50
        assert abs(tracker.total_cost - 5.0) < 0.01  # Allow floating point error
