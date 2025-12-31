"""Tool registry with cost-aware selection and error recovery policies."""

from dataclasses import dataclass, field
from enum import Enum

from orchestrator.selection.cost_optimizer import CostOptimizer, EfficiencyScore
from orchestrator.shared.models import ToolDefinition


class ErrorStrategy(str, Enum):
    """Strategy for handling tool failures."""
    RAISE = "raise"           # Fail fast
    CONTINUE = "continue"     # Return None, continue
    FALLBACK = "fallback"     # Try next available tool
    PARTIAL_SUCCESS = "partial_success"  # Accept partial results


@dataclass
class ErrorRecoveryPolicy:
    """Policy for recovering from tool execution errors."""
    strategy: ErrorStrategy = ErrorStrategy.RAISE
    max_retries: int = 0
    retry_backoff: float = 1.0  # Exponential backoff multiplier
    fallback_tools: list[str] = field(default_factory=list)  # Tool names to try
    timeout_override: float | None = None  # Override timeout on retry

    def should_retry(self, attempt: int) -> bool:
        """Whether to retry at this attempt number."""
        return attempt < self.max_retries


@dataclass
class SelectionConfig:
    """Configuration for cost-aware tool selection."""
    cost_weight: float = 0.5
    latency_weight: float = 0.3
    reliability_weight: float = 0.2
    cost_budget: float | None = None
    latency_budget: float | None = None
    capability_filter: str | None = None


class ToolRegistry:
    """Registry with cost-aware selection and error recovery."""

    def __init__(self):
        self.tools: dict[str, ToolDefinition] = {}
        self.error_policies: dict[str, ErrorRecoveryPolicy] = {}
        self.optimizer = CostOptimizer()

    def register(
        self,
        tool: ToolDefinition,
        error_policy: ErrorRecoveryPolicy | None = None,
    ) -> None:
        """Register a tool with optional error policy."""
        self.tools[tool.name] = tool
        if error_policy:
            self.error_policies[tool.name] = error_policy

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Get tool by name."""
        return self.tools.get(name)

    def get_best_tool(
        self,
        config: SelectionConfig,
        exclude: list[str] | None = None,
    ) -> ToolDefinition | None:
        """Find best tool matching config."""
        candidates = [
            t for name, t in self.tools.items()
            if exclude is None or name not in exclude
        ]

        if not candidates:
            return None

        best = self.optimizer.select_best_tool(
            tools=candidates,
            cost_budget=config.cost_budget,
            latency_budget=config.latency_budget,
            capability_filter=config.capability_filter,
        )
        return best

    def rank_tools(
        self,
        config: SelectionConfig,
        exclude: list[str] | None = None,
    ) -> list[tuple[ToolDefinition, EfficiencyScore]]:
        """Rank all tools matching config."""
        candidates = [
            t for name, t in self.tools.items()
            if exclude is None or name not in exclude
        ]

        if not candidates:
            return []

        return self.optimizer.rank_tools(
            tools=candidates,
            cost_budget=config.cost_budget,
            latency_budget=config.latency_budget,
            capability_filter=config.capability_filter,
        )

    def get_error_policy(self, tool_name: str) -> ErrorRecoveryPolicy:
        """Get error policy for tool, or default."""
        return self.error_policies.get(
            tool_name,
            ErrorRecoveryPolicy(strategy=ErrorStrategy.RAISE),
        )


# Global registry instance
_default_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Get or create default tool registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry


def reset_registry() -> None:
    """Reset default registry (for testing)."""
    global _default_registry
    _default_registry = None
