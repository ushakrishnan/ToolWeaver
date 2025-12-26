"""Cost-aware tool selection and error recovery example.

This example demonstrates:
1. Registering tools with cost metadata
2. Selecting tools based on budget and efficiency
3. Error recovery with retry/fallback strategies
"""

import asyncio
from orchestrator.selection.registry import (
    ToolRegistry, ErrorRecoveryPolicy, ErrorStrategy, SelectionConfig,
)
from orchestrator.tools.error_recovery import ErrorRecoveryExecutor
from orchestrator.shared.models import ToolDefinition


# Define available text analysis tools with different cost/speed tradeoffs
async def main():
    registry = ToolRegistry()
    executor = ErrorRecoveryExecutor()
    
    # Fast, expensive vision analyzer
    fast_vision = ToolDefinition(
        name="fast_vision_analyzer",
        description="Fast, accurate vision using Claude",
        metadata={
            "cost_per_call": 0.10,
            "expected_latency_ms": 500,
            "success_rate": 0.99,
            "capabilities": ["vision", "text_extraction"],
        },
    )
    
    # Slow, cheap vision analyzer
    cheap_vision = ToolDefinition(
        name="cheap_vision_analyzer",
        description="Slow but budget-friendly vision using free tier",
        metadata={
            "cost_per_call": 0.01,
            "expected_latency_ms": 5000,
            "success_rate": 0.85,
            "capabilities": ["vision"],
        },
    )
    
    # Medium option with retry support
    medium_vision = ToolDefinition(
        name="medium_vision_analyzer",
        description="Balanced vision analyzer",
        metadata={
            "cost_per_call": 0.05,
            "expected_latency_ms": 1500,
            "success_rate": 0.92,
            "capabilities": ["vision", "ocr"],
        },
    )
    
    # Register tools with policies
    registry.register(fast_vision)
    registry.register(cheap_vision)
    
    # Medium vision with retry policy
    medium_policy = ErrorRecoveryPolicy(
        strategy=ErrorStrategy.FALLBACK,
        max_retries=2,
        retry_backoff=1.5,
        fallback_tools=["cheap_vision_analyzer"],
    )
    registry.register(medium_vision, error_policy=medium_policy)
    
    print("=" * 70)
    print("SCENARIO 1: Cost-optimized selection (budget: $0.02)")
    print("=" * 70)
    
    # When cost is critical
    config = SelectionConfig(
        cost_weight=0.8,  # Prioritize cost
        latency_weight=0.1,
        reliability_weight=0.1,
        cost_budget=0.02,
    )
    
    best = registry.get_best_tool(config)
    print(f"Selected: {best.name}")
    print(f"  Cost: ${best.metadata.get('cost_per_call', 'N/A')}")
    print(f"  Latency: {best.metadata.get('expected_latency_ms', 'N/A')}ms")
    print()
    
    print("=" * 70)
    print("SCENARIO 2: Speed-optimized selection (latency budget: 1000ms)")
    print("=" * 70)
    
    # When latency matters
    config = SelectionConfig(
        cost_weight=0.1,
        latency_weight=0.8,  # Prioritize speed
        reliability_weight=0.1,
        latency_budget=1000,
    )
    
    best = registry.get_best_tool(config)
    print(f"Selected: {best.name}")
    print(f"  Cost: ${best.metadata.get('cost_per_call', 'N/A')}")
    print(f"  Latency: {best.metadata.get('expected_latency_ms', 'N/A')}ms")
    print()
    
    print("=" * 70)
    print("SCENARIO 3: Rank all options for vision capability")
    print("=" * 70)
    
    config = SelectionConfig(
        cost_weight=0.33,
        latency_weight=0.33,
        reliability_weight=0.34,
        capability_filter="vision",
    )
    
    ranked = registry.rank_tools(config)
    for i, (tool, score) in enumerate(ranked, 1):
        print(f"{i}. {tool.name}")
        print(f"   Score: {score.score:.3f}")
        print(f"   Efficiency: cost={score.efficiency_metrics.get('normalized_cost', 'N/A'):.2f}, "
              f"latency={score.efficiency_metrics.get('normalized_latency', 'N/A'):.2f}, "
              f"reliability={score.efficiency_metrics.get('normalized_reliability', 'N/A'):.2f}")
    print()
    
    print("=" * 70)
    print("SCENARIO 4: Async execution with error recovery")
    print("=" * 70)
    
    # Simulate tool functions
    async def fast_vision_impl():
        """Simulate fast vision analyzer."""
        await asyncio.sleep(0.5)
        return {"text": "Hello World", "confidence": 0.99}
    
    async def unreliable_vision():
        """Simulate unreliable vision that might fail."""
        raise RuntimeError("Service temporarily unavailable")
    
    async def fallback_vision():
        """Fallback vision analyzer."""
        await asyncio.sleep(2)
        return {"text": "Hello World", "confidence": 0.80}
    
    # Execute with recovery
    print("Trying unreliable vision with fallback...")
    policy = ErrorRecoveryPolicy(
        strategy=ErrorStrategy.FALLBACK,
        fallback_tools=[fallback_vision],
    )
    
    result = await executor.execute_with_recovery(
        unreliable_vision,
        "unreliable",
        policy=policy,
        fallback_tools=[fallback_vision],
    )
    
    print(f"Success: {result.success}")
    print(f"Result: {result.result}")
    print(f"Strategy used: {result.strategy_used}")
    print()
    
    print("=" * 70)
    print("SCENARIO 5: Retry with exponential backoff")
    print("=" * 70)
    
    attempt_count = 0
    
    async def flaky_vision():
        """Vision that fails first 2 times, then succeeds."""
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            print(f"  Attempt {attempt_count}: Failing...")
            raise RuntimeError("Temporary failure")
        print(f"  Attempt {attempt_count}: Success!")
        return {"text": "Recovered", "confidence": 0.95}
    
    policy = ErrorRecoveryPolicy(
        strategy=ErrorStrategy.CONTINUE,
        max_retries=3,
        retry_backoff=0.5,
    )
    
    result = await executor.execute_with_recovery(
        flaky_vision,
        "flaky",
        policy=policy,
    )
    
    print(f"Final result: {result.result}")
    print(f"Total attempts: {result.attempts}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
