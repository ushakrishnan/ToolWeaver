"""
Agent Evaluation Framework

Provides tools to measure agent performance on standard tasks.
Key metrics: completion rate, context usage, execution time, steps taken.

Usage:
    evaluator = AgentEvaluator(orchestrator, context_tracker)
    results = await evaluator.run_benchmark("standard_tasks")
    evaluator.save_baseline(results, "v1.0")
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of a single task execution"""
    task_id: str
    success: bool
    duration: float
    context_tokens: int
    steps_taken: int
    error: str | None = None
    output: Any | None = None


@dataclass
class BenchmarkResults:
    """Aggregated results from a benchmark suite"""
    completion_rate: float
    avg_context_usage: float
    avg_duration: float
    avg_steps: float
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    results: list[TaskResult]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "completion_rate": self.completion_rate,
            "avg_context_usage": self.avg_context_usage,
            "avg_duration": self.avg_duration,
            "avg_steps": self.avg_steps,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "results": [asdict(r) for r in self.results]
        }


class AgentEvaluator:
    """
    Evaluate agent performance on standard tasks.

    Features:
    - Run benchmark suites
    - Measure completion rate, context usage, speed
    - Save baselines for regression testing
    - Compare against previous runs
    """

    def __init__(self, orchestrator: Any, context_tracker: Any) -> None:
        """
        Initialize evaluator.

        Args:
            orchestrator: Orchestrator instance to evaluate
            context_tracker: ContextTracker instance for metrics
        """
        self.orchestrator = orchestrator
        self.context_tracker = context_tracker
        self.results_dir = Path("benchmarks/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def run_benchmark(self, task_suite: str) -> BenchmarkResults:
        """
        Run benchmark suite and collect metrics.

        Args:
            task_suite: Name of task suite file (e.g., "standard_tasks")

        Returns:
            BenchmarkResults with aggregated metrics
        """
        logger.info(f"Running benchmark suite: {task_suite}")

        # Load tasks
        tasks = self._load_tasks(task_suite)
        if not tasks:
            raise ValueError(f"No tasks found in suite: {task_suite}")

        logger.info(f"Loaded {len(tasks)} tasks")

        # Execute each task
        results = []
        for i, task in enumerate(tasks, 1):
            logger.info(f"Executing task {i}/{len(tasks)}: {task['id']}")
            result = await self._evaluate_task(task)
            results.append(result)

            # Log progress
            status = "✓" if result.success else "✗"
            logger.info(
                f"  {status} {result.task_id}: "
                f"{result.duration:.2f}s, "
                f"{result.context_tokens} tokens, "
                f"{result.steps_taken} steps"
            )

        # Aggregate results
        return self._aggregate_results(results)

    async def _evaluate_task(self, task: dict) -> TaskResult:
        """
        Execute single task and measure performance.

        Args:
            task: Task definition with prompt, expected output, etc.

        Returns:
            TaskResult with metrics
        """
        start_time = time.time()
        self.context_tracker.reset()

        try:
            # Execute task
            result = await self.orchestrator.execute(
                task["prompt"],
                context=task.get("context", {})
            )

            # Validate result
            success = self._validate_result(result, task.get("expected", {}))
            error = None
            output = result

        except Exception as e:
            logger.error(f"Task {task['id']} failed: {e}")
            success = False
            error = str(e)
            output = None
            result = {}

        duration = time.time() - start_time

        return TaskResult(
            task_id=task["id"],
            success=success,
            duration=duration,
            context_tokens=self.context_tracker.total_tokens,
            steps_taken=len(result.get("steps", [])),
            error=error,
            output=output
        )

    def _load_tasks(self, task_suite: str) -> list[dict]:
        """
        Load task suite from JSON file.

        Args:
            task_suite: Name of task suite (with or without .json)

        Returns:
            List of task definitions
        """
        # Try with and without .json extension
        suite_paths = [
            Path(f"benchmarks/task_suites/{task_suite}.json"),
            Path(f"benchmarks/task_suites/{task_suite}"),
            Path(task_suite)
        ]

        for path in suite_paths:
            if path.exists():
                logger.debug(f"Loading tasks from {path}")
                with open(path) as f:
                    data = json.load(f)
                    tasks = data.get("tasks", [])
                    return list(tasks) if isinstance(tasks, list) else []

        logger.error(f"Task suite not found: {task_suite}")
        return []

    def _validate_result(self, result: Any, expected: dict) -> bool:
        """
        Validate task result against expected output.

        Args:
            result: Actual output from orchestrator
            expected: Expected output criteria

        Returns:
            True if result meets expectations
        """
        if not expected:
            # No validation criteria, consider success if no exception
            return True

        # Check result type
        if "type" in expected:
            expected_type = expected["type"]
            if expected_type == "function_call":
                # Verify a function was called
                if not isinstance(result, dict) or "function" not in result:
                    return False

                # Check specific function if specified
                if "function" in expected:
                    if result.get("function") != expected["function"]:
                        return False

                # Check result contains expected string
                if "result_contains" in expected:
                    result_str = str(result.get("result", ""))
                    if expected["result_contains"] not in result_str:
                        return False

        # Check minimum steps
        if "min_steps" in expected:
            steps = len(result.get("steps", []))
            if steps < expected["min_steps"]:
                return False

        # Check tools used
        if "tools_used" in expected:
            tools = {step.get("tool") for step in result.get("steps", [])}
            expected_tools = set(expected["tools_used"])
            if not expected_tools.issubset(tools):
                return False

        return True

    def _aggregate_results(self, results: list[TaskResult]) -> BenchmarkResults:
        """
        Aggregate individual task results into summary metrics.

        Args:
            results: List of TaskResult objects

        Returns:
            BenchmarkResults with aggregated metrics
        """
        if not results:
            return BenchmarkResults(
                completion_rate=0.0,
                avg_context_usage=0.0,
                avg_duration=0.0,
                avg_steps=0.0,
                total_tasks=0,
                successful_tasks=0,
                failed_tasks=0,
                results=[]
            )

        successful = [r for r in results if r.success]
        total = len(results)

        return BenchmarkResults(
            completion_rate=len(successful) / total,
            avg_context_usage=sum(r.context_tokens for r in results) / total,
            avg_duration=sum(r.duration for r in results) / total,
            avg_steps=sum(r.steps_taken for r in results) / total,
            total_tasks=total,
            successful_tasks=len(successful),
            failed_tasks=total - len(successful),
            results=results
        )

    def save_baseline(self, results: BenchmarkResults, name: str) -> None:
        """
        Save results as baseline for regression testing.

        Args:
            name: Name for this baseline (e.g., "v1.0", "before_code_exec")
        """
        baseline_path = self.results_dir / f"{name}_baseline.json"

        baseline_data = {
            "name": name,
            "timestamp": time.time(),
            "completion_rate": results.completion_rate,
            "avg_context": results.avg_context_usage,
            "avg_duration": results.avg_duration,
            "avg_steps": results.avg_steps,
            "total_tasks": results.total_tasks,
            "successful_tasks": results.successful_tasks,
            "failed_tasks": results.failed_tasks
        }

        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f, indent=2)

        logger.info(f"Saved baseline to {baseline_path}")

    def load_baseline(self, name: str) -> dict[str, Any] | None:
        """
        Load previously saved baseline.

        Args:
            name: Name of baseline to load

        Returns:
            Baseline data or None if not found
        """
        baseline_path = self.results_dir / f"{name}_baseline.json"

        if not baseline_path.exists():
            logger.warning(f"Baseline not found: {name}")
            return None

        with open(baseline_path) as f:
            data = json.load(f)
            return cast(dict[str, Any] | None, data if isinstance(data, dict) else None)

    def compare_to_baseline(
        self,
        current: BenchmarkResults,
        baseline_name: str
    ) -> dict[str, Any]:
        """
        Compare current results to saved baseline.

        Args:
            current: Current benchmark results
            baseline_name: Name of baseline to compare against

        Returns:
            Dictionary with comparison metrics
        """
        baseline = self.load_baseline(baseline_name)

        if not baseline:
            return {"error": f"Baseline {baseline_name} not found"}

        comparison = {
            "baseline_name": baseline_name,
            "completion_rate": {
                "current": current.completion_rate,
                "baseline": baseline["completion_rate"],
                "change": current.completion_rate - baseline["completion_rate"],
                "pct_change": (
                    (current.completion_rate - baseline["completion_rate"])
                    / baseline["completion_rate"] * 100
                    if baseline["completion_rate"] > 0 else 0
                )
            },
            "context_usage": {
                "current": current.avg_context_usage,
                "baseline": baseline["avg_context"],
                "change": current.avg_context_usage - baseline["avg_context"],
                "pct_change": (
                    (current.avg_context_usage - baseline["avg_context"])
                    / baseline["avg_context"] * 100
                    if baseline["avg_context"] > 0 else 0
                )
            },
            "duration": {
                "current": current.avg_duration,
                "baseline": baseline["avg_duration"],
                "change": current.avg_duration - baseline["avg_duration"],
                "pct_change": (
                    (current.avg_duration - baseline["avg_duration"])
                    / baseline["avg_duration"] * 100
                    if baseline["avg_duration"] > 0 else 0
                )
            }
        }

        return comparison

    def print_comparison(self, comparison: dict[str, Any]) -> None:
        """
        Pretty print comparison results.

        Args:
            comparison: Output from compare_to_baseline()
        """
        print("\n" + "="*60)
        print(f"Comparison to baseline: {comparison['baseline_name']}")
        print("="*60)

        for metric, data in comparison.items():
            if metric == "baseline_name":
                continue

            print(f"\n{metric.replace('_', ' ').title()}:")
            print(f"  Current:  {data['current']:.2f}")
            print(f"  Baseline: {data['baseline']:.2f}")
            print(f"  Change:   {data['change']:+.2f} ({data['pct_change']:+.1f}%)")

            # Determine if change is good or bad
            if metric == "context_usage":
                status = "✓ Better" if data['change'] < 0 else "✗ Worse"
            elif metric == "duration":
                status = "✓ Faster" if data['change'] < 0 else "✗ Slower"
            else:  # completion_rate
                status = "✓ Better" if data['change'] > 0 else "✗ Worse"

            print(f"  Status:   {status}")

        print("\n" + "="*60)
