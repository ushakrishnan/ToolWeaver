"""
Tests for Workflow System (Phase 8)

Tests cover:
1. Workflow template creation and validation
2. Workflow context and variable substitution
3. Dependency resolution and parallel execution
4. Error handling and retries
5. Conditional execution
"""

import pytest
import asyncio
from orchestrator._internal.workflows.workflow import (
    WorkflowTemplate,
    WorkflowStep,
    WorkflowContext,
    WorkflowExecutor,
    StepStatus
)


class TestWorkflowStep:
    """Test WorkflowStep creation and validation"""
    
    def test_create_simple_step(self):
        """Test creating a simple workflow step"""
        step = WorkflowStep(
            step_id="test_step",
            tool_name="test_tool",
            parameters={"param1": "value1"}
        )
        
        assert step.step_id == "test_step"
        assert step.tool_name == "test_tool"
        assert step.parameters == {"param1": "value1"}
        assert step.depends_on == []
        assert step.condition is None
        assert step.retry_count == 0
    
    def test_create_step_with_dependencies(self):
        """Test creating a step with dependencies"""
        step = WorkflowStep(
            step_id="step2",
            tool_name="tool2",
            parameters={},
            depends_on=["step1"]
        )
        
        assert step.depends_on == ["step1"]
    
    def test_step_requires_id(self):
        """Test that step_id is required"""
        with pytest.raises(ValueError, match="step_id is required"):
            WorkflowStep(
                step_id="",
                tool_name="tool",
                parameters={}
            )
    
    def test_step_requires_tool_name(self):
        """Test that tool_name is required"""
        with pytest.raises(ValueError, match="tool_name is required"):
            WorkflowStep(
                step_id="step1",
                tool_name="",
                parameters={}
            )


class TestWorkflowTemplate:
    """Test WorkflowTemplate creation and validation"""
    
    def test_create_simple_workflow(self):
        """Test creating a simple workflow"""
        workflow = WorkflowTemplate(
            name="test_workflow",
            description="Test workflow",
            steps=[
                WorkflowStep(step_id="step1", tool_name="tool1", parameters={})
            ]
        )
        
        assert workflow.name == "test_workflow"
        assert workflow.description == "Test workflow"
        assert len(workflow.steps) == 1
    
    def test_create_workflow_with_dependencies(self):
        """Test creating a workflow with dependent steps"""
        workflow = WorkflowTemplate(
            name="dep_workflow",
            description="Workflow with dependencies",
            steps=[
                WorkflowStep(step_id="step1", tool_name="tool1", parameters={}),
                WorkflowStep(
                    step_id="step2",
                    tool_name="tool2",
                    parameters={},
                    depends_on=["step1"]
                )
            ]
        )
        
        assert len(workflow.steps) == 2
        assert workflow.steps[1].depends_on == ["step1"]
    
    def test_workflow_requires_name(self):
        """Test that workflow name is required"""
        with pytest.raises(ValueError, match="name is required"):
            WorkflowTemplate(
                name="",
                description="Test",
                steps=[WorkflowStep(step_id="s1", tool_name="t1", parameters={})]
            )
    
    def test_workflow_requires_steps(self):
        """Test that workflow must have steps"""
        with pytest.raises(ValueError, match="must have at least one step"):
            WorkflowTemplate(
                name="empty",
                description="Empty workflow",
                steps=[]
            )
    
    def test_workflow_validates_unique_step_ids(self):
        """Test that step IDs must be unique"""
        with pytest.raises(ValueError, match="step_ids must be unique"):
            WorkflowTemplate(
                name="duplicate",
                description="Duplicate step IDs",
                steps=[
                    WorkflowStep(step_id="step1", tool_name="tool1", parameters={}),
                    WorkflowStep(step_id="step1", tool_name="tool2", parameters={})
                ]
            )
    
    def test_workflow_validates_dependencies_exist(self):
        """Test that dependencies must reference existing steps"""
        with pytest.raises(ValueError, match="depends on non-existent step"):
            WorkflowTemplate(
                name="invalid_dep",
                description="Invalid dependency",
                steps=[
                    WorkflowStep(
                        step_id="step1",
                        tool_name="tool1",
                        parameters={},
                        depends_on=["nonexistent"]
                    )
                ]
            )
    
    def test_get_step_by_id(self):
        """Test retrieving a step by ID"""
        workflow = WorkflowTemplate(
            name="test",
            description="Test",
            steps=[
                WorkflowStep(step_id="step1", tool_name="tool1", parameters={}),
                WorkflowStep(step_id="step2", tool_name="tool2", parameters={})
            ]
        )
        
        step = workflow.get_step("step1")
        assert step is not None
        assert step.step_id == "step1"
        
        nonexistent = workflow.get_step("step99")
        assert nonexistent is None


class TestWorkflowContext:
    """Test WorkflowContext functionality"""
    
    def test_create_empty_context(self):
        """Test creating an empty context"""
        context = WorkflowContext()
        
        assert context.step_results == {}
        assert context.step_status == {}
        assert context.variables == {}
        assert context.errors == {}
    
    def test_create_context_with_variables(self):
        """Test creating a context with initial variables"""
        context = WorkflowContext({"var1": "value1", "var2": 42})
        
        assert context.variables == {"var1": "value1", "var2": 42}
    
    def test_set_and_get_result(self):
        """Test storing and retrieving step results"""
        context = WorkflowContext()
        
        context.set_result("step1", {"output": "result1"})
        
        result = context.get_result("step1")
        assert result == {"output": "result1"}
        assert context.is_success("step1")
    
    def test_set_error(self):
        """Test storing step errors"""
        context = WorkflowContext()
        
        error = ValueError("Test error")
        context.set_error("step1", error)
        
        assert "step1" in context.errors
        assert context.get_status("step1") == StepStatus.FAILED
        assert not context.is_success("step1")
    
    def test_substitute_simple_variable(self):
        """Test substituting a simple variable"""
        context = WorkflowContext({"repo": "myrepo"})
        
        result = context.substitute("Repository: {{repo}}")
        
        assert result == "Repository: myrepo"
    
    def test_substitute_step_result(self):
        """Test substituting a step result field"""
        context = WorkflowContext()
        context.set_result("step1", {"url": "https://example.com"})
        
        result = context.substitute("URL: {{step1.url}}")
        
        assert result == "URL: https://example.com"
    
    def test_substitute_nested_field(self):
        """Test substituting a nested result field"""
        context = WorkflowContext()
        context.set_result("step1", {"user": {"name": "John", "email": "john@example.com"}})
        
        result = context.substitute("Name: {{step1.user.name}}")
        
        assert result == "Name: John"
    
    def test_substitute_dict(self):
        """Test substituting variables in a dictionary"""
        context = WorkflowContext({"repo": "myrepo", "branch": "main"})
        
        template = {
            "repository": "{{repo}}",
            "branch": "{{branch}}",
            "static": "value"
        }
        
        result = context.substitute(template)
        
        assert result == {
            "repository": "myrepo",
            "branch": "main",
            "static": "value"
        }
    
    def test_substitute_list(self):
        """Test substituting variables in a list"""
        context = WorkflowContext({"value": "test"})
        
        template = ["item1", "{{value}}", "item3"]
        
        result = context.substitute(template)
        
        assert result == ["item1", "test", "item3"]
    
    def test_substitute_missing_variable(self):
        """Test substituting a missing variable returns empty string"""
        context = WorkflowContext()
        
        result = context.substitute("Value: {{missing}}")
        
        # Should return empty string for missing variable
        assert result == "Value: "
    
    def test_context_to_dict(self):
        """Test exporting context as dictionary"""
        context = WorkflowContext({"var1": "value1"})
        context.set_result("step1", {"output": "result1"})
        context.set_error("step2", ValueError("error"))
        
        result = context.to_dict()
        
        assert "step_results" in result
        assert "step_status" in result
        assert "variables" in result
        assert "errors" in result
        assert result["variables"] == {"var1": "value1"}


class TestDependencyResolution:
    """Test dependency resolution and execution ordering"""
    
    @pytest.mark.asyncio
    async def test_simple_linear_workflow(self):
        """Test workflow with linear dependencies"""
        workflow = WorkflowTemplate(
            name="linear",
            description="Linear workflow",
            steps=[
                WorkflowStep(step_id="step1", tool_name="tool1", parameters={}),
                WorkflowStep(
                    step_id="step2",
                    tool_name="tool2",
                    parameters={},
                    depends_on=["step1"]
                ),
                WorkflowStep(
                    step_id="step3",
                    tool_name="tool3",
                    parameters={},
                    depends_on=["step2"]
                )
            ]
        )
        
        executor = WorkflowExecutor()
        levels = executor._resolve_dependencies(workflow.steps)
        
        # Should have 3 levels (no parallel execution)
        assert len(levels) == 3
        assert len(levels[0]) == 1
        assert levels[0][0].step_id == "step1"
        assert len(levels[1]) == 1
        assert levels[1][0].step_id == "step2"
        assert len(levels[2]) == 1
        assert levels[2][0].step_id == "step3"
    
    @pytest.mark.asyncio
    async def test_parallel_workflow(self):
        """Test workflow with parallel steps"""
        workflow = WorkflowTemplate(
            name="parallel",
            description="Parallel workflow",
            steps=[
                WorkflowStep(step_id="step1", tool_name="tool1", parameters={}),
                WorkflowStep(
                    step_id="step2",
                    tool_name="tool2",
                    parameters={},
                    depends_on=["step1"]
                ),
                WorkflowStep(
                    step_id="step3",
                    tool_name="tool3",
                    parameters={},
                    depends_on=["step1"]
                ),
                WorkflowStep(
                    step_id="step4",
                    tool_name="tool4",
                    parameters={},
                    depends_on=["step2", "step3"]
                )
            ]
        )
        
        executor = WorkflowExecutor()
        levels = executor._resolve_dependencies(workflow.steps)
        
        # Should have 3 levels
        assert len(levels) == 3
        
        # Level 0: step1
        assert len(levels[0]) == 1
        assert levels[0][0].step_id == "step1"
        
        # Level 1: step2 and step3 (parallel)
        assert len(levels[1]) == 2
        step_ids = {step.step_id for step in levels[1]}
        assert step_ids == {"step2", "step3"}
        
        # Level 2: step4
        assert len(levels[2]) == 1
        assert levels[2][0].step_id == "step4"
    
    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected"""
        workflow = WorkflowTemplate(
            name="circular",
            description="Circular dependency",
            steps=[
                WorkflowStep(
                    step_id="step1",
                    tool_name="tool1",
                    parameters={},
                    depends_on=["step2"]
                ),
                WorkflowStep(
                    step_id="step2",
                    tool_name="tool2",
                    parameters={},
                    depends_on=["step1"]
                )
            ]
        )
        
        executor = WorkflowExecutor()
        
        with pytest.raises(ValueError, match="Circular dependency"):
            executor._resolve_dependencies(workflow.steps)


class TestWorkflowExecution:
    """Test end-to-end workflow execution"""
    
    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self):
        """Test executing a simple 2-step workflow"""
        workflow = WorkflowTemplate(
            name="simple",
            description="Simple workflow",
            steps=[
                WorkflowStep(
                    step_id="step1",
                    tool_name="tool1",
                    parameters={"input": "{{start_value}}"}
                ),
                WorkflowStep(
                    step_id="step2",
                    tool_name="tool2",
                    parameters={"data": "{{step1}}"},
                    depends_on=["step1"]
                )
            ]
        )
        
        executor = WorkflowExecutor()
        context = await executor.execute(workflow, {"start_value": "test"})
        
        # Check that both steps completed
        assert context.is_success("step1")
        assert context.is_success("step2")
        
        # Check results were stored
        assert context.get_result("step1") is not None
        assert context.get_result("step2") is not None
    
    @pytest.mark.asyncio
    async def test_execute_workflow_with_variable_substitution(self):
        """Test workflow with variable substitution in parameters"""
        workflow = WorkflowTemplate(
            name="substitution",
            description="Workflow with substitution",
            steps=[
                WorkflowStep(
                    step_id="step1",
                    tool_name="tool1",
                    parameters={"repo": "{{repo_name}}", "branch": "{{branch_name}}"}
                )
            ]
        )
        
        executor = WorkflowExecutor()
        context = await executor.execute(
            workflow,
            {"repo_name": "myrepo", "branch_name": "main"}
        )
        
        assert context.is_success("step1")
        result = context.get_result("step1")
        
        # Parameters should have been substituted
        assert result["parameters"]["repo"] == "myrepo"
        assert result["parameters"]["branch"] == "main"
    
    @pytest.mark.asyncio
    async def test_conditional_step_execution(self):
        """Test conditional step execution"""
        workflow = WorkflowTemplate(
            name="conditional",
            description="Conditional workflow",
            steps=[
                WorkflowStep(
                    step_id="step1",
                    tool_name="tool1",
                    parameters={}
                ),
                WorkflowStep(
                    step_id="step2",
                    tool_name="tool2",
                    parameters={},
                    depends_on=["step1"],
                    condition="false"  # This step should be skipped
                )
            ]
        )
        
        executor = WorkflowExecutor()
        context = await executor.execute(workflow)
        
        # Step1 should succeed
        assert context.is_success("step1")
        
        # Step2 should be skipped
        assert context.get_status("step2") == StepStatus.SKIPPED
    
    @pytest.mark.asyncio
    async def test_parallel_execution_faster_than_sequential(self):
        """Test that parallel execution is faster than sequential"""
        import time
        
        # Mock tool executor with delays
        class MockToolExecutor:
            async def execute(self, tool_name, parameters):
                await asyncio.sleep(0.1)  # 100ms delay per tool
                return {"tool": tool_name, "result": "success"}
        
        workflow = WorkflowTemplate(
            name="parallel_test",
            description="Test parallel performance",
            steps=[
                WorkflowStep(step_id="step1", tool_name="tool1", parameters={}),
                WorkflowStep(
                    step_id="step2",
                    tool_name="tool2",
                    parameters={},
                    depends_on=["step1"]
                ),
                WorkflowStep(
                    step_id="step3",
                    tool_name="tool3",
                    parameters={},
                    depends_on=["step1"]
                ),
                WorkflowStep(
                    step_id="step4",
                    tool_name="tool4",
                    parameters={},
                    depends_on=["step2", "step3"]
                )
            ]
        )
        
        executor = WorkflowExecutor(tool_executor=MockToolExecutor())
        
        start = time.time()
        context = await executor.execute(workflow)
        duration = time.time() - start
        
        # Sequential would take 400ms (4 steps × 100ms)
        # Parallel should take ~300ms (step1: 100ms, step2+step3 parallel: 100ms, step4: 100ms)
        assert duration < 0.4, f"Parallel execution took {duration:.3f}s, expected < 0.4s"
        
        # All steps should succeed
        assert all(context.is_success(f"step{i}") for i in range(1, 5))


class TestErrorHandling:
    """Test error handling and retry logic"""
    
    @pytest.mark.asyncio
    async def test_step_failure_stops_dependent_steps(self):
        """Test that failed step prevents dependent steps from running"""
        class FailingExecutor:
            async def execute(self, tool_name, parameters):
                if tool_name == "failing_tool":
                    raise ValueError("Tool failed")
                return {"success": True}
        
        workflow = WorkflowTemplate(
            name="failing",
            description="Workflow with failing step",
            steps=[
                WorkflowStep(step_id="step1", tool_name="failing_tool", parameters={}),
                WorkflowStep(
                    step_id="step2",
                    tool_name="tool2",
                    parameters={},
                    depends_on=["step1"]
                )
            ]
        )
        
        executor = WorkflowExecutor(tool_executor=FailingExecutor())
        context = await executor.execute(workflow)
        
        # Step1 should fail
        assert context.get_status("step1") == StepStatus.FAILED
        
        # Step2 should be skipped (dependency failed)
        assert context.get_status("step2") == StepStatus.SKIPPED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
