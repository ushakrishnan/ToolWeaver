"""
Tests for Workflow Library and Pattern Recognition (Phase 8)

Tests cover:
1. Pattern detection from usage logs
2. Workflow library management
3. Workflow search and suggestions
4. Serialization and persistence
"""

import pytest
import time
from pathlib import Path
from orchestrator.workflows.workflow_library import (
    PatternDetector,
    WorkflowLibrary,
    ToolSequence
)
from orchestrator.workflows.workflow import WorkflowTemplate, WorkflowStep
from orchestrator.observability.monitoring import ToolCallMetric


@pytest.fixture
def sample_logs():
    """Create sample tool usage logs"""
    from datetime import datetime, timezone, timedelta
    logs = []
    
    # Session 1: github_list_issues → github_create_pr → slack_send (successful)
    base_time = datetime.now(timezone.utc)
    logs.append(ToolCallMetric(
        timestamp=base_time.isoformat(),
        tool_name="github_list_issues",
        success=True,
        latency=0.1,  # 100ms
        execution_id="session1"
    ))
    logs.append(ToolCallMetric(
        timestamp=(base_time + timedelta(seconds=1)).isoformat(),
        tool_name="github_create_pr",
        success=True,
        latency=0.2,  # 200ms
        execution_id="session1"
    ))
    logs.append(ToolCallMetric(
        timestamp=(base_time + timedelta(seconds=2)).isoformat(),
        tool_name="slack_send_message",
        success=True,
        latency=0.05,  # 50ms
        execution_id="session1"
    ))
    
    # Session 2: Same pattern (successful)
    logs.append(ToolCallMetric(
        timestamp=(base_time + timedelta(seconds=10)).isoformat(),
        tool_name="github_list_issues",
        success=True,
        latency=0.095,  # 95ms
        execution_id="session2"
    ))
    logs.append(ToolCallMetric(
        timestamp=(base_time + timedelta(seconds=11)).isoformat(),
        tool_name="github_create_pr",
        success=True,
        latency=0.21,  # 210ms
        execution_id="session2"
    ))
    logs.append(ToolCallMetric(
        timestamp=(base_time + timedelta(seconds=12)).isoformat(),
        tool_name="slack_send_message",
        success=True,
        latency=0.045,  # 45ms
        execution_id="session2"
    ))
    
    # Session 3: Same pattern (successful)
    logs.append(ToolCallMetric(
        timestamp=(base_time + timedelta(seconds=20)).isoformat(),
        tool_name="github_list_issues",
        success=True,
        latency=0.105,  # 105ms
        execution_id="session3"
    ))
    logs.append(ToolCallMetric(
        timestamp=(base_time + timedelta(seconds=21)).isoformat(),
        tool_name="github_create_pr",
        success=True,
        latency=0.19,  # 190ms
        execution_id="session3"
    ))
    logs.append(ToolCallMetric(
        timestamp=(base_time + timedelta(seconds=22)).isoformat(),
        tool_name="slack_send_message",
        success=True,
        latency=0.055,  # 55ms
        execution_id="session3"
    ))
    
    return logs


class TestPatternDetector:
    """Test pattern detection from usage logs"""
    
    def test_create_detector(self):
        """Test creating a pattern detector"""
        detector = PatternDetector(min_frequency=3, min_success_rate=0.7)
        
        assert detector.min_frequency == 3
        assert detector.min_success_rate == 0.7
    
    def test_detect_simple_pattern(self, sample_logs):
        """Test detecting a simple 2-tool pattern"""
        detector = PatternDetector(min_frequency=3, min_success_rate=0.7)
        
        patterns = detector.analyze_logs(sample_logs, max_sequence_length=2)
        
        # Should find github_list_issues → github_create_pr pattern
        assert len(patterns) > 0
        
        # Check that the most common pattern is detected
        top_pattern = patterns[0]
        assert top_pattern.frequency >= 3
        assert top_pattern.success_rate >= 0.7
    
    def test_detect_three_tool_sequence(self, sample_logs):
        """Test detecting a 3-tool sequence"""
        detector = PatternDetector(min_frequency=3, min_success_rate=0.7)
        
        patterns = detector.analyze_logs(sample_logs, max_sequence_length=3)
        
        # Should find the full 3-tool sequence
        three_tool_patterns = [p for p in patterns if len(p.tools) == 3]
        assert len(three_tool_patterns) > 0
        
        # Check that it's the expected sequence
        top_pattern = three_tool_patterns[0]
        assert "github_list_issues" in top_pattern.tools
        assert "github_create_pr" in top_pattern.tools
        assert "slack_send_message" in top_pattern.tools
    
    def test_pattern_frequency_counting(self, sample_logs):
        """Test that pattern frequency is counted correctly"""
        detector = PatternDetector(min_frequency=1, min_success_rate=0.0)
        
        patterns = detector.analyze_logs(sample_logs, max_sequence_length=2)
        
        # github_list_issues → github_create_pr appears 3 times
        github_pattern = next(
            (p for p in patterns 
             if p.tools == ["github_list_issues", "github_create_pr"]),
            None
        )
        
        assert github_pattern is not None
        assert github_pattern.frequency == 3
    
    def test_pattern_success_rate(self, sample_logs):
        """Test that success rate is calculated correctly"""
        from datetime import datetime, timezone, timedelta
        # Add a failed 2-tool sequence
        base_time = datetime.now(timezone.utc)
        failed_logs = [
            ToolCallMetric(
                timestamp=(base_time + timedelta(seconds=30)).isoformat(),
                tool_name="github_list_issues",
                success=False,
                latency=0.1,
                execution_id="session4"
            ),
            ToolCallMetric(
                timestamp=(base_time + timedelta(seconds=31)).isoformat(),
                tool_name="github_create_pr",
                success=False,
                latency=0.2,
                execution_id="session4"
            )
        ]
        logs_with_failure = sample_logs + failed_logs
        
        detector = PatternDetector(min_frequency=1, min_success_rate=0.0)
        patterns = detector.analyze_logs(logs_with_failure, max_sequence_length=2)
        
        # Check 2-tool pattern for github_list_issues → github_create_pr
        github_pattern = next(
            (p for p in patterns if p.tools == ["github_list_issues", "github_create_pr"]),
            None
        )
        
        assert github_pattern is not None
        # 3 successful sequences + 1 failed = 75% success rate
        assert 0.7 <= github_pattern.success_rate <= 0.8
    
    def test_filter_by_min_frequency(self, sample_logs):
        """Test filtering patterns by minimum frequency"""
        # Require at least 5 occurrences (should filter out most patterns)
        detector = PatternDetector(min_frequency=5, min_success_rate=0.0)
        
        patterns = detector.analyze_logs(sample_logs, max_sequence_length=2)
        
        # All patterns should have frequency >= 5
        assert all(p.frequency >= 5 for p in patterns)
    
    def test_filter_by_success_rate(self, sample_logs):
        """Test filtering patterns by minimum success rate"""
        from datetime import datetime, timezone, timedelta
        # Add several failed sequences
        base_time = datetime.now(timezone.utc)
        failed_logs = [
            ToolCallMetric(
                timestamp=(base_time + timedelta(seconds=100+i)).isoformat(),
                tool_name="failing_tool",
                success=False,
                latency=0.05,
                execution_id=f"fail_{i}"
            )
            for i in range(5)
        ]
        
        all_logs = sample_logs + failed_logs
        
        detector = PatternDetector(min_frequency=1, min_success_rate=0.9)
        patterns = detector.analyze_logs(all_logs, max_sequence_length=1)
        
        # failing_tool should be filtered out (0% success rate)
        failing_pattern = next(
            (p for p in patterns if p.tools == ["failing_tool"]),
            None
        )
        assert failing_pattern is None
    
    def test_suggest_workflow_from_pattern(self, sample_logs):
        """Test suggesting a workflow based on detected pattern"""
        detector = PatternDetector(min_frequency=3, min_success_rate=0.7)
        patterns = detector.analyze_logs(sample_logs, max_sequence_length=3)
        
        # Suggest workflow for the detected 3-tool pattern
        tools = ["github_list_issues", "github_create_pr", "slack_send_message"]
        workflow = detector.suggest_workflow(tools, patterns)
        
        assert workflow is not None
        assert len(workflow.steps) == 3
        assert workflow.metadata.get('auto_generated') is True
    
    def test_suggest_workflow_no_match(self):
        """Test that no workflow is suggested when no pattern matches"""
        detector = PatternDetector()
        patterns = []  # No patterns
        
        workflow = detector.suggest_workflow(["unknown_tool"], patterns)
        
        assert workflow is None


class TestWorkflowLibrary:
    """Test workflow library management"""
    
    def test_create_library(self):
        """Test creating a workflow library"""
        library = WorkflowLibrary()
        
        # Should have built-in workflows
        assert len(library.list_all()) > 0
    
    def test_builtin_workflows_loaded(self):
        """Test that built-in workflows are loaded"""
        library = WorkflowLibrary()
        
        # Check for github_pr_workflow
        github_workflow = library.get("github_pr_workflow")
        assert github_workflow is not None
        assert github_workflow.name == "github_pr_workflow"
        assert len(github_workflow.steps) == 3
        
        # Check for slack_notification_chain
        slack_workflow = library.get("slack_notification_chain")
        assert slack_workflow is not None
        assert slack_workflow.name == "slack_notification_chain"
    
    def test_register_custom_workflow(self):
        """Test registering a custom workflow"""
        library = WorkflowLibrary()
        
        custom_workflow = WorkflowTemplate(
            name="custom_test",
            description="Custom test workflow",
            steps=[
                WorkflowStep(step_id="step1", tool_name="tool1", parameters={})
            ]
        )
        
        library.register(custom_workflow)
        
        retrieved = library.get("custom_test")
        assert retrieved is not None
        assert retrieved.name == "custom_test"
    
    def test_get_nonexistent_workflow(self):
        """Test getting a workflow that doesn't exist"""
        library = WorkflowLibrary()
        
        workflow = library.get("nonexistent_workflow")
        
        assert workflow is None
    
    def test_list_all_workflows(self):
        """Test listing all workflows"""
        library = WorkflowLibrary()
        
        workflows = library.list_all()
        
        assert len(workflows) >= 2  # At least 2 built-in workflows
        assert all(isinstance(w, WorkflowTemplate) for w in workflows)
    
    def test_search_by_query(self):
        """Test searching workflows by query"""
        library = WorkflowLibrary()
        
        results = library.search(query="github")
        
        assert len(results) > 0
        assert any("github" in w.name.lower() or "github" in w.description.lower() 
                  for w in results)
    
    def test_search_by_category(self):
        """Test searching workflows by category"""
        library = WorkflowLibrary()
        
        results = library.search(category="github")
        
        assert len(results) > 0
        assert all(w.metadata.get('category') == 'github' for w in results)
    
    def test_search_by_tool_name(self):
        """Test searching workflows by tool name"""
        library = WorkflowLibrary()
        
        results = library.search(tool_name="slack_send_message")
        
        assert len(results) > 0
        assert all(
            any(step.tool_name == "slack_send_message" for step in w.steps)
            for w in results
        )
    
    def test_suggest_workflows_for_tools(self):
        """Test suggesting workflows that use given tools"""
        library = WorkflowLibrary()
        
        suggestions = library.suggest_for_tools(["github_create_pr"])
        
        assert len(suggestions) > 0
        assert all(
            any(step.tool_name == "github_create_pr" for step in w.steps)
            for w in suggestions
        )
    
    def test_save_and_load_from_disk(self, tmp_path):
        """Test saving and loading workflows from disk"""
        storage_path = tmp_path / "workflows.json"
        
        # Create library and add custom workflow
        library1 = WorkflowLibrary(storage_path=storage_path)
        
        custom_workflow = WorkflowTemplate(
            name="custom_saved",
            description="Workflow to be saved",
            steps=[
                WorkflowStep(step_id="step1", tool_name="tool1", parameters={"key": "value"})
            ],
            metadata={'custom': True}
        )
        
        library1.register(custom_workflow)
        library1.save_to_disk()
        
        # Load in new library instance
        library2 = WorkflowLibrary(storage_path=storage_path)
        
        loaded_workflow = library2.get("custom_saved")
        assert loaded_workflow is not None
        assert loaded_workflow.name == "custom_saved"
        assert loaded_workflow.description == "Workflow to be saved"
        assert len(loaded_workflow.steps) == 1
        assert loaded_workflow.steps[0].parameters == {"key": "value"}
    
    def test_builtin_workflows_not_saved(self, tmp_path):
        """Test that built-in workflows are not saved to disk"""
        storage_path = tmp_path / "workflows.json"
        
        library = WorkflowLibrary(storage_path=storage_path)
        library.save_to_disk()
        
        # Check file contents
        import json
        with open(storage_path) as f:
            data = json.load(f)
        
        # Should not contain built-in workflows
        workflow_names = [w['name'] for w in data['workflows']]
        assert 'github_pr_workflow' not in workflow_names
        assert 'slack_notification_chain' not in workflow_names


class TestIntegration:
    """Test integration between pattern detection and workflow library"""
    
    def test_detect_pattern_and_register(self, sample_logs):
        """Test detecting a pattern and registering it in the library"""
        detector = PatternDetector(min_frequency=3, min_success_rate=0.7)
        patterns = detector.analyze_logs(sample_logs, max_sequence_length=3)
        
        library = WorkflowLibrary()
        
        # Suggest and register workflow from pattern
        tools = ["github_list_issues", "github_create_pr", "slack_send_message"]
        workflow = detector.suggest_workflow(tools, patterns)
        
        if workflow:
            library.register(workflow)
            
            # Verify workflow is in library
            retrieved = library.get(workflow.name)
            assert retrieved is not None
            assert retrieved.name == workflow.name
    
    def test_suggest_workflow_from_library_matches_pattern(self, sample_logs):
        """Test that library suggestions match detected patterns"""
        detector = PatternDetector(min_frequency=3, min_success_rate=0.7)
        patterns = detector.analyze_logs(sample_logs, max_sequence_length=3)
        
        library = WorkflowLibrary()
        
        # Get suggestions for github tools
        suggestions = library.suggest_for_tools(["github_create_pr"])
        
        # Should include the built-in github_pr_workflow
        assert any(w.name == "github_pr_workflow" for w in suggestions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
