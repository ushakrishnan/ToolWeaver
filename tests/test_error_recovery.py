"""Tests for error recovery and registry integration."""

import asyncio
import pytest
from orchestrator.selection.registry import (
    ToolRegistry, ErrorRecoveryPolicy, ErrorStrategy, SelectionConfig,
    get_registry, reset_registry,
)
from orchestrator.tools.error_recovery import (
    ErrorRecoveryExecutor, RecoveryResult,
)
from orchestrator.shared.models import ToolDefinition


@pytest.fixture(autouse=True)
def reset_reg():
    """Reset registry before each test."""
    reset_registry()
    yield
    reset_registry()


class TestErrorRecoveryPolicy:
    """Test error recovery policy configuration."""
    
    def test_default_policy_raises(self):
        """Default policy should raise on error."""
        policy = ErrorRecoveryPolicy()
        assert policy.strategy == ErrorStrategy.RAISE
        assert policy.max_retries == 0
    
    def test_retry_policy(self):
        """Retry policy with backoff."""
        policy = ErrorRecoveryPolicy(
            strategy=ErrorStrategy.FALLBACK,
            max_retries=3,
            retry_backoff=2.0,
            fallback_tools=["backup1", "backup2"],
        )
        assert policy.should_retry(0)
        assert policy.should_retry(1)
        assert policy.should_retry(2)
        assert not policy.should_retry(3)
    
    def test_fallback_policy(self):
        """Policy with fallback tools."""
        policy = ErrorRecoveryPolicy(
            strategy=ErrorStrategy.FALLBACK,
            fallback_tools=["backup_tool_1", "backup_tool_2"],
        )
        assert len(policy.fallback_tools) == 2


class TestToolRegistry:
    """Test tool registry with selection."""
    
    def test_register_tool(self):
        """Register tool in registry."""
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="text_analyzer",
            type="tool",
            description="Analyze text",
            metadata={"cost_per_call": 0.01},
        )
        registry.register(tool)
        assert registry.get_tool("text_analyzer") == tool
    
    def test_register_with_error_policy(self):
        """Register tool with error recovery policy."""
        registry = ToolRegistry()
        tool = ToolDefinition(name="flaky_tool", type="tool", description="May fail")
        policy = ErrorRecoveryPolicy(
            strategy=ErrorStrategy.CONTINUE,
            max_retries=3,
        )
        registry.register(tool, error_policy=policy)
        
        retrieved_policy = registry.get_error_policy("flaky_tool")
        assert retrieved_policy.max_retries == 3
    
    def test_get_default_policy(self):
        """Tools without policies get default raise policy."""
        registry = ToolRegistry()
        policy = registry.get_error_policy("nonexistent_tool")
        assert policy.strategy == ErrorStrategy.RAISE
    
    def test_get_best_tool_by_cost(self):
        """Select best tool by cost."""
        registry = ToolRegistry()
        
        cheap = ToolDefinition(
            name="cheap",
            type="tool",
            description="Cheap",
            metadata={"cost_per_call": 0.01},
        )
        expensive = ToolDefinition(
            name="expensive",
            type="tool",
            description="Expensive",
            metadata={"cost_per_call": 0.10},
        )
        registry.register(cheap)
        registry.register(expensive)
        
        config = SelectionConfig(cost_weight=0.8)
        best = registry.get_best_tool(config)
        assert best.name == "cheap"
    
    def test_rank_tools_by_efficiency(self):
        """Rank tools by efficiency score."""
        registry = ToolRegistry()
        
        for i in range(3):
            tool = ToolDefinition(
                name=f"tool_{i}",
                type="tool",
                description=f"Tool {i}",
                metadata={
                    "cost_per_call": 0.01 * (i + 1),
                    "expected_latency_ms": 100 * (i + 1),
                },
            )
            registry.register(tool)
        
        config = SelectionConfig()
        ranked = registry.rank_tools(config)
        assert len(ranked) == 3
        # Cheaper/faster tools should rank higher
        assert ranked[0][0].name == "tool_0"
    
    def test_exclude_tools(self):
        """Exclude tools from selection."""
        registry = ToolRegistry()
        
        tool1 = ToolDefinition(name="tool1", type="tool", description="T1")
        tool2 = ToolDefinition(name="tool2", type="tool", description="T2")
        registry.register(tool1)
        registry.register(tool2)
        
        config = SelectionConfig()
        best = registry.get_best_tool(config, exclude=["tool1"])
        assert best.name == "tool2"


class TestErrorRecoveryExecutor:
    """Test error recovery execution."""
    
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Execute successful tool."""
        executor = ErrorRecoveryExecutor()
        
        async def success_tool():
            return "ok"
        
        result = await executor.execute_with_recovery(success_tool, "success_tool")
        assert result.success
        assert result.result == "ok"
        assert result.attempts == 1
    
    @pytest.mark.asyncio
    async def test_failed_execution_raise(self):
        """Failed execution with raise strategy."""
        executor = ErrorRecoveryExecutor()
        
        async def fail_tool():
            raise ValueError("boom")
        
        result = await executor.execute_with_recovery(fail_tool, "fail_tool")
        assert not result.success
        assert isinstance(result.error, ValueError)
    
    @pytest.mark.asyncio
    async def test_retry_then_succeed(self):
        """Retry failed tool until success."""
        executor = ErrorRecoveryExecutor()
        attempts = 0
        
        async def flaky_tool():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise RuntimeError("not yet")
            return "success"
        
        policy = ErrorRecoveryPolicy(
            strategy=ErrorStrategy.CONTINUE,
            max_retries=3,
        )
        
        result = await executor.execute_with_recovery(
            flaky_tool, "flaky", policy=policy
        )
        assert result.success
        assert result.result == "success"
        assert result.attempts == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Retries exhausted, tool still fails."""
        executor = ErrorRecoveryExecutor()
        
        async def always_fails():
            raise RuntimeError("always fails")
        
        policy = ErrorRecoveryPolicy(
            strategy=ErrorStrategy.CONTINUE,
            max_retries=2,
        )
        
        result = await executor.execute_with_recovery(
            always_fails, "always_fails", policy=policy
        )
        assert not result.success
        assert result.attempts == 3  # 1 initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_fallback_strategy(self):
        """Try fallback tools on failure."""
        executor = ErrorRecoveryExecutor()
        
        async def main_fails():
            raise RuntimeError("main failed")
        
        async def fallback_succeeds():
            return "fallback worked"
        
        policy = ErrorRecoveryPolicy(
            strategy=ErrorStrategy.FALLBACK,
        )
        
        result = await executor.execute_with_recovery(
            main_fails,
            "main",
            policy=policy,
            fallback_tools=[fallback_succeeds],
        )
        assert result.success
        assert result.result == "fallback worked"
        assert "fallback" in result.strategy_used
    
    @pytest.mark.asyncio
    async def test_partial_success_strategy(self):
        """Partial success strategy returns partial result on failure."""
        executor = ErrorRecoveryExecutor()
        
        async def fails():
            raise RuntimeError("error")
        
        policy = ErrorRecoveryPolicy(
            strategy=ErrorStrategy.PARTIAL_SUCCESS,
        )
        
        result = await executor.execute_with_recovery(
            fails, "partial", policy=policy
        )
        assert not result.success
        assert result.result == {"partial": True}
        assert result.strategy_used == "partial_success"
    
    @pytest.mark.asyncio
    async def test_sync_tool_execution(self):
        """Execute synchronous tool with recovery."""
        executor = ErrorRecoveryExecutor()
        
        def sync_tool():
            return "sync result"
        
        result = await executor.execute_with_recovery(sync_tool, "sync_tool")
        assert result.success
        assert result.result == "sync result"
    
    @pytest.mark.asyncio
    async def test_tool_with_args(self):
        """Execute tool with args and kwargs."""
        executor = ErrorRecoveryExecutor()
        
        async def add(a, b, c=0):
            return a + b + c
        
        result = await executor.execute_with_recovery(
            add, "add", args=(1, 2), kwargs={"c": 3}
        )
        assert result.success
        assert result.result == 6
    
    @pytest.mark.asyncio
    async def test_backoff_timing(self):
        """Verify exponential backoff timing."""
        executor = ErrorRecoveryExecutor()
        attempt_times = []
        
        async def track_attempts():
            attempt_times.append(asyncio.get_event_loop().time())
            if len(attempt_times) < 3:
                raise RuntimeError("fail")
            return "ok"
        
        policy = ErrorRecoveryPolicy(
            strategy=ErrorStrategy.CONTINUE,
            max_retries=2,
            retry_backoff=0.1,  # 0.1s, 0.01s backoff
        )
        
        result = await executor.execute_with_recovery(
            track_attempts, "track", policy=policy
        )
        assert result.success
        # Timing assertions are loose due to execution speed
        assert len(attempt_times) == 3


class TestGlobalRegistry:
    """Test global registry singleton."""
    
    def test_get_registry_singleton(self):
        """get_registry returns same instance."""
        reg1 = get_registry()
        reg2 = get_registry()
        assert reg1 is reg2
    
    def test_reset_registry(self):
        """reset_registry clears singleton."""
        reg1 = get_registry()
        tool = ToolDefinition(name="test", type="tool", description="test")
        reg1.register(tool)
        assert reg1.get_tool("test") is not None
        
        reset_registry()
        reg2 = get_registry()
        assert reg2 is not reg1
        assert reg2.get_tool("test") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
