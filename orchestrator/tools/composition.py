"""
Tool Composition API

Chains multiple tools where output of one becomes input to the next.
Supports linear chains (sequential) and DAG-based execution (future).
"""

from __future__ import annotations

import asyncio
import functools
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class CompositionStep:
    """Definition of a single step in a composition chain."""
    name: str
    tool_ref: str  # Reference to tool name or callable
    input_schema: dict[str, Any] = field(default_factory=dict)  # Expected input fields
    output_mapping: dict[str, str] = field(default_factory=dict)  # Map output field names
    timeout_sec: int = 30
    retry_count: int = 0
    on_error: str = "raise"  # "raise", "continue", "fallback"

    def __post_init__(self):
        if self.on_error not in ("raise", "continue", "fallback"):
            raise ValueError(f"on_error must be 'raise', 'continue', or 'fallback', got {self.on_error}")


@dataclass
class CompositionChain:
    """A sequence of tool invocations forming a workflow."""
    name: str
    steps: list[CompositionStep] = field(default_factory=list)
    description: str = ""
    is_linear: bool = True  # True for sequential, False for DAG (future)

    def add_step(self, step: CompositionStep) -> CompositionChain:
        """Add a step and return self for chaining."""
        self.steps.append(step)
        return self

    def validate(self) -> list[str]:
        """Validate chain for issues; return list of warnings/errors."""
        issues = []
        if not self.steps:
            issues.append("Chain has no steps")
        for i, step in enumerate(self.steps):
            if not step.name:
                issues.append(f"Step {i} has no name")
            if not step.tool_ref:
                issues.append(f"Step {i} ({step.name}) has no tool_ref")
        return issues


@dataclass
class CompositionResult:
    """Result of a composition execution."""
    chain_name: str
    step_results: dict[str, Any]  # step_name -> output
    final_output: Any
    success: bool
    error: str | None = None
    total_duration_ms: float = 0.0


@dataclass
class StepExecutionError(Exception):
    """Error during step execution."""
    step_name: str
    error_msg: str
    cause: Exception | None = None


class ToolResolver(Protocol):
    """Protocol for resolving tool references to callables."""
    async def __call__(self, tool_ref: str) -> Callable:
        ...


class CompositionExecutor:
    """Executes tool composition chains sequentially (linear chains only)."""

    def __init__(self, tool_resolver: ToolResolver | None = None):
        """
        Args:
            tool_resolver: Optional callable(tool_ref) -> Callable;
                          defaults to a simple lookup that expects callables as tool_refs
        """
        self.tool_resolver = tool_resolver or self._default_resolver

    async def _default_resolver(self, tool_ref: str) -> Callable:
        """Default resolver: assumes tool_ref is callable or raises."""
        if callable(tool_ref):
            return tool_ref
        raise ValueError(f"Tool {tool_ref} is not callable and no resolver provided")

    async def execute(
        self,
        chain: CompositionChain,
        initial_input: dict[str, Any],
    ) -> CompositionResult:
        """
        Execute a composition chain sequentially.

        Args:
            chain: CompositionChain to execute
            initial_input: Initial input dict for first step

        Returns:
            CompositionResult with step outputs and final result
        """
        issues = chain.validate()
        if issues:
            return CompositionResult(
                chain_name=chain.name,
                step_results={},
                final_output=None,
                success=False,
                error=f"Chain validation failed: {'; '.join(issues)}",
                total_duration_ms=0.0,
            )

        start = time.monotonic()
        step_results = {}
        current_input = initial_input.copy()

        try:
            for step in chain.steps:
                try:
                    step_output = await self._execute_step(step, current_input)
                    step_results[step.name] = step_output

                    # Prepare input for next step
                    current_input = build_parameter_mapping(
                        source_output=step_output,
                        target_input_schema=chain.steps[chain.steps.index(step) + 1].input_schema
                        if chain.steps.index(step) + 1 < len(chain.steps)
                        else {},
                        explicit_mapping=chain.steps[chain.steps.index(step) + 1].output_mapping
                        if chain.steps.index(step) + 1 < len(chain.steps)
                        else {},
                    )
                except StepExecutionError:
                    if step.on_error == "raise":
                        raise
                    elif step.on_error == "continue":
                        # Skip and use None for next step
                        step_results[step.name] = None
                        current_input = {}
                    # "fallback" would be handled here later

            duration_ms = (time.monotonic() - start) * 1000
            return CompositionResult(
                chain_name=chain.name,
                step_results=step_results,
                final_output=step_results.get(chain.steps[-1].name if chain.steps else None),
                success=True,
                error=None,
                total_duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.monotonic() - start) * 1000
            return CompositionResult(
                chain_name=chain.name,
                step_results=step_results,
                final_output=None,
                success=False,
                error=str(e),
                total_duration_ms=duration_ms,
            )

    async def _execute_step(self, step: CompositionStep, step_input: dict[str, Any]) -> Any:
        """Execute a single step with timeout and retry logic."""
        for attempt in range(step.retry_count + 1):
            try:
                # Handle both async and sync resolvers
                if asyncio.iscoroutinefunction(self.tool_resolver):
                    tool = await self.tool_resolver(step.tool_ref)
                else:
                    tool = self.tool_resolver(step.tool_ref)

                # Call with timeout
                async def _call():
                    if asyncio.iscoroutinefunction(tool):
                        return await tool(**step_input)
                    else:
                        return tool(**step_input)

                result = await asyncio.wait_for(_call(), timeout=step.timeout_sec)
                return result
            except asyncio.TimeoutError as e:
                if attempt == step.retry_count:
                    raise StepExecutionError(step.name, f"Timeout after {step.timeout_sec}s", e)
                await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
            except Exception as e:
                if attempt == step.retry_count:
                    raise StepExecutionError(step.name, str(e), e)
                await asyncio.sleep(0.1 * (2 ** attempt))



def composite_tool(
    name: str,
    description: str = "",
) -> Callable:
    """
    Decorator to register a tool composition chain.

    Usage:
        @composite_tool(name="fetch_parse_extract")
        def my_chain():
            return (
                CompositionChain(name="fetch_parse_extract")
                .add_step(CompositionStep(name="fetch", tool_ref="http_get", ...))
                .add_step(CompositionStep(name="parse", tool_ref="parse_html", ...))
                .add_step(CompositionStep(name="extract", tool_ref="regex_extract", ...))
            )
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            chain = fn(*args, **kwargs)
            if not isinstance(chain, CompositionChain):
                raise TypeError(f"@composite_tool {name} must return a CompositionChain, got {type(chain)}")
            chain.name = name
            chain.description = description
            return chain
        wrapper._is_composite_tool = True
        wrapper._composition_name = name
        return wrapper
    return decorator


def build_parameter_mapping(
    source_output: dict[str, Any],
    target_input_schema: dict[str, Any],
    explicit_mapping: dict[str, str] = None,
) -> dict[str, Any]:
    """
    Auto-wire outputs from one step to inputs of the next.

    Args:
        source_output: Output dict from prior step
        target_input_schema: Expected input schema for next step
        explicit_mapping: Optional {target_field: source_field} overrides

    Returns:
        Input dict for next step with matched/mapped fields
    """
    explicit_mapping = explicit_mapping or {}
    result = {}

    # Apply explicit mappings first
    for target_field, source_field in explicit_mapping.items():
        if source_field in source_output:
            result[target_field] = source_output[source_field]

    # Passthrough: auto-map fields with same name if not already set
    for field_name in target_input_schema.keys():
        if field_name not in result and field_name in source_output:
            result[field_name] = source_output[field_name]

    return result
