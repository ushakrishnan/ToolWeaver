"""
Tests for cost-benefit tool selection.
"""

import pytest

from orchestrator.selection.cost_optimizer import (
    CostOptimizer,
)
from orchestrator.shared.models import ToolDefinition


@pytest.fixture
def tool_slow_expensive():
    """Slow, expensive tool (accurate but costly)."""
    return ToolDefinition(
        name="gpt4_analyzer",
        type="tool",
        description="High accuracy analysis",
        metadata={
            "cost_per_call": 0.05,
            "expected_latency_ms": 5000,
            "success_rate": 0.99,
            "capabilities": ["text", "vision"],
        },
    )


@pytest.fixture
def tool_fast_cheap():
    """Fast, cheap tool (less accurate but efficient)."""
    return ToolDefinition(
        name="phi3_classifier",
        type="tool",
        description="Fast classification",
        metadata={
            "cost_per_call": 0.001,
            "expected_latency_ms": 100,
            "success_rate": 0.85,
            "capabilities": ["text"],
        },
    )


@pytest.fixture
def tool_balanced():
    """Balanced tool (mid-range on all metrics)."""
    return ToolDefinition(
        name="claude_extractor",
        type="tool",
        description="Balanced extraction",
        metadata={
            "cost_per_call": 0.01,
            "expected_latency_ms": 1000,
            "success_rate": 0.92,
            "capabilities": ["text", "code"],
        },
    )


def test_extract_metrics():
    tool = ToolDefinition(
        name="test",
        type="tool",
        description="Test",
        metadata={
            "cost_per_call": 0.05,
            "expected_latency_ms": 2000,
            "success_rate": 0.95,
        },
    )

    optimizer = CostOptimizer()
    metrics = optimizer.extract_metrics(tool)

    assert metrics.cost_per_call == 0.05
    assert metrics.expected_latency_ms == 2000
    assert metrics.success_rate == 0.95


def test_calculate_efficiency_score(tool_balanced):
    optimizer = CostOptimizer(cost_weight=0.5, latency_weight=0.3, reliability_weight=0.2)
    score = optimizer.calculate_efficiency(tool_balanced)

    assert score is not None
    assert 0 <= score.score <= 1
    assert score.tool_name == "claude_extractor"


def test_calculate_efficiency_with_cost_constraint_violated():
    optimizer = CostOptimizer()
    tool = ToolDefinition(
        name="expensive",
        type="tool",
        description="Too expensive",
        metadata={"cost_per_call": 0.10},
    )

    score = optimizer.calculate_efficiency(tool, cost_budget=0.05)
    assert score is None


def test_calculate_efficiency_with_latency_constraint_violated():
    optimizer = CostOptimizer()
    tool = ToolDefinition(
        name="slow",
        type="tool",
        description="Too slow",
        metadata={"expected_latency_ms": 15000},
    )

    score = optimizer.calculate_efficiency(tool, latency_budget=10000)
    assert score is None


def test_select_best_tool_cost_optimized(tool_slow_expensive, tool_fast_cheap, tool_balanced):
    optimizer = CostOptimizer(cost_weight=0.8, latency_weight=0.1, reliability_weight=0.1)
    tools = [tool_slow_expensive, tool_fast_cheap, tool_balanced]

    best = optimizer.select_best_tool(tools)
    assert best.name == "phi3_classifier"


def test_select_best_tool_reliability_optimized(tool_slow_expensive, tool_fast_cheap, tool_balanced):
    optimizer = CostOptimizer(cost_weight=0.1, latency_weight=0.1, reliability_weight=0.8)
    tools = [tool_slow_expensive, tool_fast_cheap, tool_balanced]

    best = optimizer.select_best_tool(tools)
    assert best.name == "gpt4_analyzer"


def test_select_best_tool_latency_optimized(tool_slow_expensive, tool_fast_cheap, tool_balanced):
    optimizer = CostOptimizer(cost_weight=0.1, latency_weight=0.8, reliability_weight=0.1)
    tools = [tool_slow_expensive, tool_fast_cheap, tool_balanced]

    best = optimizer.select_best_tool(tools)
    assert best.name == "phi3_classifier"


def test_select_best_tool_with_budget(tool_slow_expensive, tool_fast_cheap, tool_balanced):
    optimizer = CostOptimizer()
    tools = [tool_slow_expensive, tool_fast_cheap, tool_balanced]

    # Only cheap and balanced qualify
    best = optimizer.select_best_tool(tools, cost_budget=0.02)
    assert best.name in ["phi3_classifier", "claude_extractor"]


def test_select_best_tool_with_capability_filter(tool_slow_expensive, tool_fast_cheap, tool_balanced):
    optimizer = CostOptimizer()
    tools = [tool_slow_expensive, tool_fast_cheap, tool_balanced]

    # Only slow_expensive and balanced have vision
    best = optimizer.select_best_tool(tools, capability_filter="vision")
    assert best is not None
    metrics = optimizer.extract_metrics(best)
    assert "vision" in metrics.capabilities


def test_select_best_tool_no_qualify():
    optimizer = CostOptimizer()
    tool = ToolDefinition(
        name="expensive_tool",
        type="tool",
        description="Too expensive",
        metadata={"cost_per_call": 1.0},
    )

    best = optimizer.select_best_tool([tool], cost_budget=0.01)
    assert best is None


def test_rank_tools(tool_slow_expensive, tool_fast_cheap, tool_balanced):
    optimizer = CostOptimizer()
    tools = [tool_slow_expensive, tool_fast_cheap, tool_balanced]

    ranked = optimizer.rank_tools(tools)

    assert len(ranked) == 3
    # Fast cheap should be best with default weights (cost:0.5, latency:0.3, reliability:0.2)
    # Since it has very low cost and latency, even though reliability is lower
    assert ranked[0][0].name == "phi3_classifier"


def test_rank_tools_with_constraints(tool_slow_expensive, tool_fast_cheap, tool_balanced):
    optimizer = CostOptimizer()
    tools = [tool_slow_expensive, tool_fast_cheap, tool_balanced]

    ranked = optimizer.rank_tools(tools, cost_budget=0.02)

    # Only cheap and balanced qualify
    assert len(ranked) == 2
    assert tool_slow_expensive not in [t for t, _ in ranked]


def test_weight_normalization():
    optimizer = CostOptimizer(cost_weight=2.0, latency_weight=3.0, reliability_weight=5.0)

    # Weights should sum to 1.0
    assert abs(optimizer.cost_weight + optimizer.latency_weight + optimizer.reliability_weight - 1.0) < 0.001
