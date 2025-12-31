"""
Cost-Benefit Tool Selection

Enables planners to choose tools based on cost, latency, and efficiency constraints.
Adds metadata fields to ToolDefinition and provides selection algorithms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from orchestrator.shared.models import ToolDefinition


@dataclass
class ToolMetrics:
    """Metrics for cost/efficiency calculation."""
    cost_per_call: float = 0.0  # USD per invocation
    expected_latency_ms: int = 100  # Expected execution time
    success_rate: float = 1.0  # 0-1, based on historical data
    capabilities: list[str] = None  # e.g., ["text", "vision", "code"]

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


@dataclass
class EfficiencyScore:
    """Efficiency score combining cost, latency, and reliability."""
    tool_name: str
    score: float  # 0-1, higher is better
    cost_component: float  # Weighted cost factor
    latency_component: float  # Weighted latency factor
    reliability_component: float  # Success rate factor


class CostOptimizer:
    """
    Optimizes tool selection based on cost and performance constraints.
    
    Scoring algorithm:
        efficiency = (1/cost_normalized) * success_rate / (1 + latency_normalized)
    
    Weights can be tuned to prioritize cost vs. speed vs. reliability.
    """

    def __init__(
        self,
        cost_weight: float = 0.5,
        latency_weight: float = 0.3,
        reliability_weight: float = 0.2,
    ):
        """
        Args:
            cost_weight: Importance of cost in scoring (0-1)
            latency_weight: Importance of latency in scoring (0-1)
            reliability_weight: Importance of success rate in scoring (0-1)
        """
        total = cost_weight + latency_weight + reliability_weight
        self.cost_weight = cost_weight / total
        self.latency_weight = latency_weight / total
        self.reliability_weight = reliability_weight / total

    def extract_metrics(self, tool_def: ToolDefinition) -> ToolMetrics:
        """Extract metrics from ToolDefinition metadata."""
        meta = tool_def.metadata or {}
        return ToolMetrics(
            cost_per_call=float(meta.get("cost_per_call", 0.0)),
            expected_latency_ms=int(meta.get("expected_latency_ms", 100)),
            success_rate=float(meta.get("success_rate", 1.0)),
            capabilities=meta.get("capabilities", []),
        )

    def calculate_efficiency(
        self,
        tool_def: ToolDefinition,
        cost_budget: float | None = None,
        latency_budget: int | None = None,
    ) -> EfficiencyScore | None:
        """
        Calculate efficiency score for a tool.
        
        Returns None if tool violates hard constraints (cost_budget, latency_budget).
        """
        metrics = self.extract_metrics(tool_def)

        # Check hard constraints
        if cost_budget is not None and metrics.cost_per_call > cost_budget:
            return None
        if latency_budget is not None and metrics.expected_latency_ms > latency_budget:
            return None

        # Normalize metrics to 0-1 range (using max values as bounds)
        # Assumes: cost up to $1, latency up to 10s, success_rate 0-1
        cost_norm = min(metrics.cost_per_call / 1.0, 1.0)
        latency_norm = min(metrics.expected_latency_ms / 10000.0, 1.0)

        # Cost: lower is better (invert)
        cost_score = 1.0 - cost_norm if cost_norm > 0 else 1.0

        # Latency: lower is better (invert)
        latency_score = 1.0 - latency_norm

        # Reliability: higher is better (use as-is)
        reliability_score = metrics.success_rate

        # Combined efficiency score
        score = (
            self.cost_weight * cost_score +
            self.latency_weight * latency_score +
            self.reliability_weight * reliability_score
        )

        return EfficiencyScore(
            tool_name=tool_def.name,
            score=score,
            cost_component=self.cost_weight * cost_score,
            latency_component=self.latency_weight * latency_score,
            reliability_component=self.reliability_weight * reliability_score,
        )

    def select_best_tool(
        self,
        tools: list[ToolDefinition],
        cost_budget: float | None = None,
        latency_budget: int | None = None,
        capability_filter: str | None = None,
    ) -> ToolDefinition | None:
        """
        Select the best tool based on efficiency score.
        
        Args:
            tools: List of tools to choose from
            cost_budget: Max cost per call (hard constraint)
            latency_budget: Max latency in ms (hard constraint)
            capability_filter: Optional capability to filter on
            
        Returns:
            Best tool or None if none qualify
        """
        candidates = tools

        # Filter by capability if specified
        if capability_filter:
            candidates = [
                t for t in candidates
                if capability_filter in self.extract_metrics(t).capabilities
            ]

        if not candidates:
            return None

        # Score all candidates
        scores = []
        for tool in candidates:
            score = self.calculate_efficiency(tool, cost_budget, latency_budget)
            if score is not None:
                scores.append((tool, score))

        if not scores:
            return None

        # Return tool with highest score
        best_tool, _ = max(scores, key=lambda x: x[1].score)
        return best_tool

    def rank_tools(
        self,
        tools: list[ToolDefinition],
        cost_budget: float | None = None,
        latency_budget: int | None = None,
    ) -> list[tuple[ToolDefinition, EfficiencyScore]]:
        """
        Rank tools by efficiency score (highest first).
        
        Returns list of (tool, score) tuples.
        """
        scores = []
        for tool in tools:
            score = self.calculate_efficiency(tool, cost_budget, latency_budget)
            if score is not None:
                scores.append((tool, score))

        # Sort by score descending
        return sorted(scores, key=lambda x: x[1].score, reverse=True)
