"""
Workflow System for Tool Composition (Phase 8)

Enables automatic tool chaining, dependency management, and context sharing
for complex multi-tool workflows.
"""

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status of a workflow step execution"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """
    A single step in a workflow.

    Features:
    - Tool name reference
    - Parameter templates with variable substitution
    - Dependency tracking
    - Conditional execution
    - Retry configuration
    """
    step_id: str
    tool_name: str
    parameters: dict[str, Any]
    depends_on: list[str] = field(default_factory=list)
    condition: str | None = None  # e.g., "{{step1.success}} == true"
    retry_count: int = 0
    timeout_seconds: int | None = None

    def __post_init__(self) -> None:
        """Validate step configuration"""
        if not self.step_id:
            raise ValueError("step_id is required")
        if not self.tool_name:
            raise ValueError("tool_name is required")
        if not isinstance(self.parameters, dict):
            raise ValueError("parameters must be a dictionary")


@dataclass
class WorkflowTemplate:
    """
    A reusable workflow template with multiple steps.

    Example:
        github_pr_workflow = WorkflowTemplate(
            name="github_pr_workflow",
            description="Create PR and notify team",
            steps=[
                WorkflowStep(
                    step_id="list_issues",
                    tool_name="github_list_issues",
                    parameters={"repo": "{{repo}}"}
                ),
                WorkflowStep(
                    step_id="create_pr",
                    tool_name="github_create_pr",
                    depends_on=["list_issues"],
                    parameters={
                        "repo": "{{repo}}",
                        "title": "{{pr_title}}"
                    }
                )
            ]
        )
    """
    name: str
    description: str
    steps: list[WorkflowStep]
    metadata: dict[str, Any] = field(default_factory=dict)
    parallel_groups: list[list[str]] | None = None

    def __post_init__(self) -> None:
        """Validate workflow configuration"""
        if not self.name:
            raise ValueError("name is required")
        if not self.steps:
            raise ValueError("workflow must have at least one step")

        # Validate unique step IDs
        step_ids = [step.step_id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("step_ids must be unique")

        # Validate dependencies exist
        valid_ids = set(step_ids)
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in valid_ids:
                    raise ValueError(f"Step '{step.step_id}' depends on non-existent step '{dep}'")

    def get_step(self, step_id: str) -> WorkflowStep | None:
        """Get step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None


class WorkflowContext:
    """
    Shared context for workflow execution.

    Features:
    - Store step results
    - Share data between steps
    - Variable substitution
    - Type-safe data access
    """

    def __init__(self, initial_variables: dict[str, Any] | None = None):
        self.step_results: dict[str, Any] = {}
        self.step_status: dict[str, StepStatus] = {}
        self.variables: dict[str, Any] = initial_variables or {}
        self.errors: dict[str, Exception] = {}

    def set_result(self, step_id: str, result: Any, status: StepStatus = StepStatus.SUCCESS) -> None:
        """Store result from a step execution"""
        self.step_results[step_id] = result
        self.step_status[step_id] = status

    def set_error(self, step_id: str, error: Exception) -> None:
        """Store error from a failed step"""
        self.errors[step_id] = error
        self.step_status[step_id] = StepStatus.FAILED

    def get_result(self, step_id: str) -> Any:
        """Retrieve result from a previous step"""
        return self.step_results.get(step_id)

    def get_status(self, step_id: str) -> StepStatus | None:
        """Get status of a step"""
        return self.step_status.get(step_id)

    def is_success(self, step_id: str) -> bool:
        """Check if a step completed successfully"""
        return self.step_status.get(step_id) == StepStatus.SUCCESS

    def substitute(self, template: Any) -> Any:
        """
        Substitute variables in template.

        Supports:
        - {{variable}} - Direct variable substitution
        - {{step_id.field}} - Access step result fields
        - {{step_id.field.nested}} - Nested field access

        Args:
            template: String template or dict with templates

        Returns:
            Substituted value (same type as input)
        """
        if isinstance(template, str):
            return self._substitute_string(template)
        elif isinstance(template, dict):
            return {k: self.substitute(v) for k, v in template.items()}
        elif isinstance(template, list):
            return [self.substitute(item) for item in template]
        else:
            return template

    def _substitute_string(self, template: str) -> str:
        """Substitute variables in a string template"""
        pattern = r"\{\{([^}]+)\}\}"

        def replacer(match: Any) -> str:
            expression = match.group(1).strip()
            try:
                value = self._evaluate_expression(expression)
                return str(value) if value is not None else ""
            except Exception as e:
                logger.warning(f"Failed to substitute '{expression}': {e}")
                return str(match.group(0))  # Return original if substitution fails

        return re.sub(pattern, replacer, template)

    def _evaluate_expression(self, expression: str) -> Any:
        """
        Evaluate a variable expression.

        Examples:
            "repo" -> self.variables["repo"]
            "step1.result" -> self.step_results["step1"]["result"]
            "step1.user.email" -> self.step_results["step1"]["user"]["email"]
        """
        # Check for direct variable first
        if expression in self.variables:
            return self.variables[expression]

        # Check for step result access (step_id.field.nested)
        if "." in expression:
            parts = expression.split(".")
            step_id = parts[0]

            if step_id in self.step_results:
                value = self.step_results[step_id]

                # Navigate nested fields
                for part in parts[1:]:
                    if isinstance(value, dict):
                        value = value.get(part)
                    elif hasattr(value, part):
                        value = getattr(value, part)
                    else:
                        return None

                return value

        return None

    def to_dict(self) -> dict[str, Any]:
        """Export context as dictionary"""
        return {
            "step_results": self.step_results,
            "step_status": {k: v.value for k, v in self.step_status.items()},
            "variables": self.variables,
            "errors": {k: str(v) for k, v in self.errors.items()}
        }


class WorkflowExecutor:
    """
    Execute workflows with dependency resolution and parallel execution.

    Features:
    - Topological sort for dependency resolution
    - Parallel execution of independent steps
    - Error handling with retries
    - Context management
    """

    def __init__(self, tool_executor: Any | None = None):
        """
        Initialize workflow executor.

        Args:
            tool_executor: Tool executor for running individual tools (optional)
        """
        self.tool_executor = tool_executor

    async def execute(
        self,
        workflow: WorkflowTemplate,
        initial_variables: dict[str, Any] | None = None
    ) -> WorkflowContext:
        """
        Execute a workflow with dependency-aware parallel execution.

        Args:
            workflow: Workflow template to execute
            initial_variables: Initial variables for context

        Returns:
            WorkflowContext with execution results
        """
        context = WorkflowContext(initial_variables)

        logger.info(f"Executing workflow: {workflow.name}")
        start_time = time.time()

        try:
            # Resolve dependencies into execution levels
            levels = self._resolve_dependencies(workflow.steps)

            logger.info(f"Workflow has {len(levels)} execution levels")

            # Execute each level in parallel
            for level_num, level_steps in enumerate(levels):
                logger.info(f"Executing level {level_num + 1} with {len(level_steps)} steps")

                # Check conditions and filter steps
                executable_steps = []
                for step in level_steps:
                    if self._should_execute(step, context):
                        executable_steps.append(step)
                    else:
                        context.set_result(step.step_id, None, StepStatus.SKIPPED)
                        logger.info(f"Skipping step '{step.step_id}' (condition not met)")

                if not executable_steps:
                    continue

                # Execute steps in parallel
                tasks = [self._execute_step(step, context) for step in executable_steps]
                await asyncio.gather(*tasks, return_exceptions=False)

            duration = time.time() - start_time
            logger.info(f"Workflow completed in {duration:.2f}s")

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise

        return context

    def _resolve_dependencies(self, steps: list[WorkflowStep]) -> list[list[WorkflowStep]]:
        """
        Resolve dependencies using topological sort.

        Returns list of lists, where each inner list contains steps that can
        be executed in parallel (same dependency level).

        Example:
            Steps: A, B(depends A), C(depends A), D(depends B,C)
            Result: [[A], [B, C], [D]]
        """
        # Build dependency graph
        step_map = {step.step_id: step for step in steps}
        in_degree = {step.step_id: len(step.depends_on) for step in steps}

        levels = []
        remaining = set(step_map.keys())

        while remaining:
            # Find steps with no unresolved dependencies
            current_level = [
                step_map[step_id]
                for step_id in remaining
                if in_degree[step_id] == 0
            ]

            if not current_level:
                # Circular dependency detected
                raise ValueError(f"Circular dependency detected in workflow. Remaining steps: {remaining}")

            levels.append(current_level)

            # Remove current level from remaining
            for step in current_level:
                remaining.remove(step.step_id)

            # Decrease in-degree for dependent steps
            for step_id in remaining:
                step = step_map[step_id]
                for dep in step.depends_on:
                    if dep not in remaining:  # Dependency resolved
                        in_degree[step_id] -= 1

        return levels

    def _should_execute(self, step: WorkflowStep, context: WorkflowContext) -> bool:
        """
        Check if a step should be executed based on its condition and dependencies.

        Args:
            step: Step to check
            context: Workflow context

        Returns:
            True if step should execute, False if should be skipped
        """
        # Check if all dependencies succeeded
        for dep in step.depends_on:
            if not context.is_success(dep):
                logger.warning(f"Step '{step.step_id}' skipped: dependency '{dep}' failed")
                return False

        # If no condition specified, execute
        if not step.condition:
            return True

        # Evaluate condition expression
        try:
            condition_str = context.substitute(step.condition)
            # Simple evaluation: check for "true" or non-empty result
            return bool(condition_str) and condition_str.lower() != "false"
        except Exception as e:
            logger.error(f"Failed to evaluate condition for '{step.step_id}': {e}")
            return False

    async def _execute_step(self, step: WorkflowStep, context: WorkflowContext) -> None:
        """
        Execute a single workflow step with retry logic.

        Args:
            step: Step to execute
            context: Workflow context
        """
        logger.info(f"Executing step: {step.step_id} (tool: {step.tool_name})")
        context.step_status[step.step_id] = StepStatus.RUNNING

        # Substitute variables in parameters
        try:
            parameters = context.substitute(step.parameters)
        except Exception as e:
            logger.error(f"Failed to substitute parameters for '{step.step_id}': {e}")
            context.set_error(step.step_id, e)
            return

        # Execute with retries
        last_error = None
        for attempt in range(step.retry_count + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retrying step '{step.step_id}' (attempt {attempt + 1}/{step.retry_count + 1})")

                # Execute tool (mock if no executor provided)
                if self.tool_executor:
                    result = await self._call_tool(step.tool_name, parameters, step.timeout_seconds)
                else:
                    # Mock execution for testing
                    result = {"step_id": step.step_id, "parameters": parameters, "mock": True}

                context.set_result(step.step_id, result, StepStatus.SUCCESS)
                logger.info(f"Step '{step.step_id}' completed successfully")
                return

            except Exception as e:
                last_error = e
                logger.warning(f"Step '{step.step_id}' failed (attempt {attempt + 1}): {e}")

                if attempt < step.retry_count:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)

        # All retries failed - ensure last_error is not None
        error = last_error if last_error is not None else Exception(f"Step '{step.step_id}' failed")
        context.set_error(step.step_id, error)
        logger.error(f"Step '{step.step_id}' failed after {step.retry_count + 1} attempts")

    async def _call_tool(self, tool_name: str, parameters: dict[str, Any], timeout: int | None) -> Any:
        """
        Call a tool with the given parameters.

        Args:
            tool_name: Name of tool to call
            parameters: Tool parameters
            timeout: Timeout in seconds

        Returns:
            Tool execution result
        """
        if not self.tool_executor:
            raise RuntimeError("No tool executor configured")

        # Call tool with optional timeout
        if timeout:
            return await asyncio.wait_for(
                self.tool_executor.execute(tool_name, parameters),
                timeout=timeout
            )
        else:
            return await self.tool_executor.execute(tool_name, parameters)


if __name__ == "__main__":
    # Example usage
    async def main() -> None:
        # Define a simple workflow
        workflow = WorkflowTemplate(
            name="example_workflow",
            description="Example multi-step workflow",
            steps=[
                WorkflowStep(
                    step_id="step1",
                    tool_name="tool_a",
                    parameters={"input": "{{start_value}}"}
                ),
                WorkflowStep(
                    step_id="step2",
                    tool_name="tool_b",
                    depends_on=["step1"],
                    parameters={"data": "{{step1.result}}"}
                ),
                WorkflowStep(
                    step_id="step3",
                    tool_name="tool_c",
                    depends_on=["step1"],
                    parameters={"value": "{{step1.output}}"}
                ),
                WorkflowStep(
                    step_id="step4",
                    tool_name="tool_d",
                    depends_on=["step2", "step3"],
                    parameters={"combined": "{{step2.result}} + {{step3.result}}"}
                )
            ]
        )

        # Execute workflow
        executor = WorkflowExecutor()
        context = await executor.execute(workflow, {"start_value": "hello"})

        print("Workflow completed:")
        print(context.to_dict())

    asyncio.run(main())
