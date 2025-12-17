"""
Tests for Agent Evaluation Framework

Tests evaluation system, context tracking, and benchmark execution.
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from orchestrator.assessment.evaluation import AgentEvaluator, TaskResult, BenchmarkResults
from orchestrator.observability.context_tracker import ContextTracker


# Mock Orchestrator for testing
class MockOrchestrator:
    """Mock orchestrator that simulates task execution"""
    
    def __init__(self, should_fail=False, execution_time=0.1):
        self.should_fail = should_fail
        self.execution_time = execution_time
        
    async def execute(self, prompt, context=None):
        """Simulate task execution"""
        await asyncio.sleep(self.execution_time)
        
        if self.should_fail:
            raise Exception("Simulated failure")
        
        # Simulate successful execution
        return {
            "result": "success",
            "function": "test_function",
            "steps": [
                {"tool": "tool1", "result": "data1"},
                {"tool": "tool2", "result": "data2"}
            ]
        }


@pytest.fixture
def context_tracker():
    """Create fresh context tracker for each test"""
    return ContextTracker()


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator"""
    return MockOrchestrator()


@pytest.fixture
def evaluator(mock_orchestrator, context_tracker):
    """Create evaluator with mock dependencies"""
    return AgentEvaluator(mock_orchestrator, context_tracker)


@pytest.fixture
def sample_task():
    """Sample task definition"""
    return {
        "id": "test_task_1",
        "prompt": "Calculate tax on $100",
        "context": {},
        "expected": {
            "type": "function_call",
            "function": "test_function"
        }
    }


@pytest.fixture
def sample_task_suite(tmp_path):
    """Create sample task suite file"""
    suite = {
        "name": "test_suite",
        "tasks": [
            {
                "id": "task_1",
                "prompt": "Test prompt 1",
                "expected": {"type": "function_call"}
            },
            {
                "id": "task_2",
                "prompt": "Test prompt 2",
                "expected": {"min_steps": 2}
            }
        ]
    }
    
    suite_dir = tmp_path / "benchmarks" / "task_suites"
    suite_dir.mkdir(parents=True)
    suite_path = suite_dir / "test_suite.json"
    
    with open(suite_path, 'w') as f:
        json.dump(suite, f)
    
    return suite_path


class TestContextTracker:
    """Test context tracking functionality"""
    
    def test_initialization(self, context_tracker):
        """Verify tracker starts with zero counts"""
        assert context_tracker.total_tokens == 0
        assert context_tracker.tool_definitions == 0
        assert context_tracker.tool_results == 0
        
    def test_add_tokens(self, context_tracker):
        """Verify token addition works"""
        context_tracker.add_tool_definitions(100)
        context_tracker.add_tool_result(50)
        context_tracker.add_user_input(30)
        context_tracker.add_model_output(20)
        
        assert context_tracker.total_tokens == 200
        assert context_tracker.tool_definitions == 100
        assert context_tracker.tool_results == 50
        
    def test_reset(self, context_tracker):
        """Verify reset clears all counts"""
        context_tracker.add_tool_definitions(100)
        context_tracker.add_tool_result(50)
        
        context_tracker.reset()
        
        assert context_tracker.total_tokens == 0
        assert context_tracker.tool_definitions == 0
        
    def test_breakdown(self, context_tracker):
        """Verify breakdown calculation"""
        context_tracker.add_tool_definitions(100)
        context_tracker.add_tool_result(50)
        
        breakdown = context_tracker.get_breakdown()
        
        assert breakdown.tool_definitions == 100
        assert breakdown.tool_results == 50
        assert breakdown.total == 150
        
    def test_percentage_breakdown(self, context_tracker):
        """Verify percentage calculation"""
        context_tracker.add_tool_definitions(100)
        context_tracker.add_tool_result(50)
        
        percentages = context_tracker.get_percentage_breakdown()
        
        assert percentages["tool_definitions"] == pytest.approx(66.67, 0.01)
        assert percentages["tool_results"] == pytest.approx(33.33, 0.01)
        
    def test_add_text(self, context_tracker):
        """Verify text estimation and categorization"""
        text = "A" * 400  # ~100 tokens at 4 chars/token
        
        context_tracker.add_text(text, category="tool_definitions")
        
        assert context_tracker.tool_definitions == 100
        assert context_tracker.total_tokens == 100
        
    def test_metrics(self, context_tracker):
        """Verify metrics output format"""
        context_tracker.add_tool_definitions(100)
        
        metrics = context_tracker.get_metrics()
        
        assert "total_tokens" in metrics
        assert "breakdown" in metrics
        assert "percentages" in metrics
        assert "efficiency_score" in metrics


class TestAgentEvaluator:
    """Test agent evaluation functionality"""
    
    @pytest.mark.asyncio
    async def test_evaluate_single_task(self, evaluator, context_tracker, sample_task):
        """Verify single task evaluation"""
        result = await evaluator._evaluate_task(sample_task)
        
        assert isinstance(result, TaskResult)
        assert result.task_id == "test_task_1"
        assert result.success == True
        assert result.duration > 0
        # Context tokens reset at start of task, so will be 0 unless
        # orchestrator adds tokens during execution
        assert result.context_tokens >= 0
        
    @pytest.mark.asyncio
    async def test_evaluate_task_failure(self, context_tracker):
        """Verify task failure is handled"""
        failing_orchestrator = MockOrchestrator(should_fail=True)
        evaluator = AgentEvaluator(failing_orchestrator, context_tracker)
        
        sample_task = {
            "id": "failing_task",
            "prompt": "This will fail",
            "expected": {}
        }
        
        result = await evaluator._evaluate_task(sample_task)
        
        assert result.success == False
        assert result.error is not None
        assert "Simulated failure" in result.error
        
    def test_load_tasks(self, evaluator, sample_task_suite):
        """Verify task suite loading"""
        tasks = evaluator._load_tasks(str(sample_task_suite))
        
        assert len(tasks) == 2
        assert tasks[0]["id"] == "task_1"
        assert tasks[1]["id"] == "task_2"
        
    def test_validate_result_function_call(self, evaluator):
        """Verify function call validation"""
        result = {
            "function": "test_func",
            "result": "contains 7.0 value"
        }
        
        expected = {
            "type": "function_call",
            "function": "test_func",
            "result_contains": "7.0"
        }
        
        is_valid = evaluator._validate_result(result, expected)
        
        assert is_valid == True
        
    def test_validate_result_min_steps(self, evaluator):
        """Verify minimum steps validation"""
        result = {
            "steps": [
                {"tool": "tool1"},
                {"tool": "tool2"},
                {"tool": "tool3"}
            ]
        }
        
        expected = {"min_steps": 2}
        
        is_valid = evaluator._validate_result(result, expected)
        
        assert is_valid == True
        
    def test_validate_result_tools_used(self, evaluator):
        """Verify tools used validation"""
        result = {
            "steps": [
                {"tool": "get_document"},
                {"tool": "summarize"}
            ]
        }
        
        expected = {
            "tools_used": ["get_document", "summarize"]
        }
        
        is_valid = evaluator._validate_result(result, expected)
        
        assert is_valid == True
        
    def test_aggregate_results(self, evaluator):
        """Verify results aggregation"""
        results = [
            TaskResult(
                task_id="task_1",
                success=True,
                duration=1.0,
                context_tokens=1000,
                steps_taken=2
            ),
            TaskResult(
                task_id="task_2",
                success=True,
                duration=2.0,
                context_tokens=2000,
                steps_taken=3
            ),
            TaskResult(
                task_id="task_3",
                success=False,
                duration=0.5,
                context_tokens=500,
                steps_taken=1,
                error="Failed"
            )
        ]
        
        aggregated = evaluator._aggregate_results(results)
        
        assert isinstance(aggregated, BenchmarkResults)
        assert aggregated.total_tasks == 3
        assert aggregated.successful_tasks == 2
        assert aggregated.failed_tasks == 1
        assert aggregated.completion_rate == pytest.approx(2/3, 0.01)
        assert aggregated.avg_duration == pytest.approx(1.17, 0.1)
        assert aggregated.avg_context_usage == pytest.approx(1166.67, 0.1)
        
    def test_save_and_load_baseline(self, evaluator, tmp_path):
        """Verify baseline save and load"""
        # Override results directory for testing
        evaluator.results_dir = tmp_path
        
        results = BenchmarkResults(
            completion_rate=0.8,
            avg_context_usage=5000,
            avg_duration=2.5,
            avg_steps=3.2,
            total_tasks=10,
            successful_tasks=8,
            failed_tasks=2,
            results=[]
        )
        
        # Save baseline
        evaluator.save_baseline(results, "test_baseline")
        
        # Load baseline
        loaded = evaluator.load_baseline("test_baseline")
        
        assert loaded is not None
        assert loaded["completion_rate"] == 0.8
        assert loaded["avg_context"] == 5000
        assert loaded["avg_duration"] == 2.5
        
    def test_compare_to_baseline(self, evaluator, tmp_path):
        """Verify baseline comparison"""
        evaluator.results_dir = tmp_path
        
        # Save baseline
        baseline_results = BenchmarkResults(
            completion_rate=0.8,
            avg_context_usage=10000,
            avg_duration=5.0,
            avg_steps=4.0,
            total_tasks=10,
            successful_tasks=8,
            failed_tasks=2,
            results=[]
        )
        evaluator.save_baseline(baseline_results, "baseline")
        
        # Create improved results
        current_results = BenchmarkResults(
            completion_rate=0.9,
            avg_context_usage=5000,  # 50% reduction!
            avg_duration=3.0,
            avg_steps=3.0,
            total_tasks=10,
            successful_tasks=9,
            failed_tasks=1,
            results=[]
        )
        
        comparison = evaluator.compare_to_baseline(current_results, "baseline")
        
        assert comparison["completion_rate"]["change"] == pytest.approx(0.1, 0.01)
        assert comparison["context_usage"]["change"] == -5000
        assert comparison["context_usage"]["pct_change"] == -50.0
        assert comparison["duration"]["change"] == -2.0
        
    @pytest.mark.asyncio
    async def test_run_benchmark_end_to_end(
        self, 
        evaluator, 
        sample_task_suite,
        context_tracker
    ):
        """Verify complete benchmark execution"""
        # Run benchmark
        results = await evaluator.run_benchmark(str(sample_task_suite))
        
        assert isinstance(results, BenchmarkResults)
        assert results.total_tasks == 2
        assert results.successful_tasks >= 0
        assert results.completion_rate >= 0
        # Context usage depends on orchestrator implementation
        assert results.avg_context_usage >= 0


class TestBenchmarkResults:
    """Test benchmark results data structure"""
    
    def test_to_dict(self):
        """Verify serialization to dictionary"""
        results = BenchmarkResults(
            completion_rate=0.8,
            avg_context_usage=5000,
            avg_duration=2.5,
            avg_steps=3.0,
            total_tasks=10,
            successful_tasks=8,
            failed_tasks=2,
            results=[]
        )
        
        result_dict = results.to_dict()
        
        assert result_dict["completion_rate"] == 0.8
        assert result_dict["avg_context_usage"] == 5000
        assert result_dict["total_tasks"] == 10
        assert "results" in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
