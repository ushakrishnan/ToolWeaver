"""
Workflow System Demo

Demonstrates Phase 8 workflow composition features:
1. Creating and executing workflows
2. Pattern detection from usage logs
3. Workflow library management
4. Variable substitution and parallel execution
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from datetime import datetime, timezone

from orchestrator.monitoring import ToolCallMetric
from orchestrator.workflow import WorkflowContext, WorkflowExecutor, WorkflowStep, WorkflowTemplate
from orchestrator.workflow_library import PatternDetector, WorkflowLibrary

# =============================================================================
# Demo 1: Basic Workflow Execution
# =============================================================================

async def demo_basic_workflow():
    """Demonstrate basic workflow creation and execution"""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Workflow Execution")
    print("=" * 80)

    # Create a simple deployment workflow
    workflow = WorkflowTemplate(
        name="simple_deploy",
        description="Simple deployment workflow",
        steps=[
            WorkflowStep(
                step_id="build",
                tool_name="docker_build",
                parameters={
                    "image": "{{image_name}}",
                    "tag": "{{version}}"
                }
            ),
            WorkflowStep(
                step_id="test",
                tool_name="run_tests",
                parameters={
                    "image": "{{build.image_id}}"
                },
                depends_on=["build"]
            ),
            WorkflowStep(
                step_id="push",
                tool_name="docker_push",
                parameters={
                    "image": "{{build.image_id}}",
                    "registry": "{{registry}}"
                },
                depends_on=["test"]
            )
        ]
    )

    print(f"\n> Created workflow: {workflow.name}")
    print(f"  Steps: {len(workflow.steps)}")
    print("  Dependencies: build -> test -> push")

    # Create context with variables
    context = WorkflowContext(initial_variables={
        "image_name": "myapp",
        "version": "1.2.3",
        "registry": "docker.io/myorg"
    })

    print(f"\n> Created context with {len(context.variables)} variables")

    # Mock tool execution (in real use, these would be actual tool calls)
    async def mock_tool_executor(step: WorkflowStep, context: WorkflowContext):
        """Mock tool execution for demo"""
        await asyncio.sleep(0.1)  # Simulate work

        if step.tool_name == "docker_build":
            return {"image_id": "sha256:abc123", "size_mb": 125}
        elif step.tool_name == "run_tests":
            return {"passed": 42, "failed": 0, "duration": 15.3}
        elif step.tool_name == "docker_push":
            return {"pushed": True, "url": f"{context.variables['registry']}/myapp:1.2.3"}

        return {}

    # Execute workflow
    WorkflowExecutor()
    print("\n> Executing workflow...")

    # Note: In real usage, you'd pass tool_registry with actual tools
    # For demo, we'll manually execute steps
    for step in workflow.steps:
        print(f"  - Running: {step.step_id} ({step.tool_name})")
        result = await mock_tool_executor(step, context)
        context.set_result(step.step_id, result)

    print("\n> Workflow completed successfully!")

    # Show results
    build_result = context.get_result("build")
    test_result = context.get_result("test")
    push_result = context.get_result("push")

    print("\nResults:")
    print(f"  Build: {build_result['image_id'][:16]}... ({build_result['size_mb']} MB)")
    print(f"  Tests: {test_result['passed']} passed, {test_result['failed']} failed")
    print(f"  Push: {push_result['url']}")


# =============================================================================
# Demo 2: Parallel Execution
# =============================================================================

async def demo_parallel_execution():
    """Demonstrate parallel execution of independent steps"""
    print("\n" + "=" * 80)
    print("DEMO 2: Parallel Execution")
    print("=" * 80)

    workflow = WorkflowTemplate(
        name="multi_region_deploy",
        description="Deploy to multiple regions in parallel",
        steps=[
            WorkflowStep(
                step_id="build",
                tool_name="docker_build",
                parameters={"image": "myapp"}
            ),
            # These three steps can run in parallel
            WorkflowStep(
                step_id="deploy_us",
                tool_name="kubectl_deploy",
                parameters={
                    "region": "us-east-1",
                    "image": "{{build.image_id}}"
                },
                depends_on=["build"]
            ),
            WorkflowStep(
                step_id="deploy_eu",
                tool_name="kubectl_deploy",
                parameters={
                    "region": "eu-west-1",
                    "image": "{{build.image_id}}"
                },
                depends_on=["build"]
            ),
            WorkflowStep(
                step_id="deploy_asia",
                tool_name="kubectl_deploy",
                parameters={
                    "region": "ap-southeast-1",
                    "image": "{{build.image_id}}"
                },
                depends_on=["build"]
            ),
            # Final step waits for all deployments
            WorkflowStep(
                step_id="verify",
                tool_name="health_check",
                parameters={"regions": "all"},
                depends_on=["deploy_us", "deploy_eu", "deploy_asia"]
            )
        ]
    )

    print(f"\n> Created workflow: {workflow.name}")
    print(f"  Steps: {len(workflow.steps)}")
    print("\nExecution plan:")
    print("  Level 0: build")
    print("  Level 1: deploy_us, deploy_eu, deploy_asia (parallel)")
    print("  Level 2: verify")

    # In real execution, the 3 deploy steps would run concurrently
    print("\n> Parallel execution saves ~66% time vs sequential!")


# =============================================================================
# Demo 3: Pattern Detection
# =============================================================================

def demo_pattern_detection():
    """Demonstrate pattern detection from usage logs"""
    print("\n" + "=" * 80)
    print("DEMO 3: Pattern Detection")
    print("=" * 80)

    # Create sample logs (simulating real usage)
    base_time = datetime.now(timezone.utc)

    # Create logs for a common pattern (repeated 5 times)
    logs = []
    for i in range(5):
        session_id = f"session{i}"
        i * 60  # 1 minute apart

        # Pattern: list_issues → create_pr → notify_slack
        logs.extend([
            ToolCallMetric(
                timestamp=base_time.isoformat(),
                tool_name="github_list_issues",
                success=True,
                latency=0.15,
                execution_id=session_id
            ),
            ToolCallMetric(
                timestamp=base_time.isoformat(),
                tool_name="github_create_pr",
                success=True,
                latency=0.25,
                execution_id=session_id
            ),
            ToolCallMetric(
                timestamp=base_time.isoformat(),
                tool_name="slack_send_message",
                success=True,
                latency=0.05,
                execution_id=session_id
            )
        ])

    print(f"\n> Created {len(logs)} simulated tool call logs")
    print("  Sessions: 5")
    print("  Pattern: github_list_issues -> github_create_pr -> slack_send_message")

    # Detect patterns
    detector = PatternDetector(
        min_frequency=3,
        min_success_rate=0.8
    )

    patterns = detector.analyze_logs(logs, max_sequence_length=3)

    print(f"\n> Detected {len(patterns)} patterns")

    # Show top patterns
    for i, pattern in enumerate(patterns[:3], 1):
        print(f"\n  Pattern {i}:")
        print(f"    Tools: {' -> '.join(pattern.tools)}")
        print(f"    Frequency: {pattern.frequency}")
        print(f"    Success rate: {pattern.success_rate:.1%}")
        print(f"    Avg duration: {pattern.avg_duration_ms:.0f}ms")

    # Convert pattern to workflow
    if patterns:
        workflow = detector.suggest_workflow(
            tools=patterns[0].tools,
            patterns=patterns
        )

        if workflow:
            print("\n> Generated workflow from pattern:")
            print(f"  Name: {workflow.name}")
            print(f"  Steps: {len(workflow.steps)}")


# =============================================================================
# Demo 4: Workflow Library
# =============================================================================

def demo_workflow_library():
    """Demonstrate workflow library management"""
    print("\n" + "=" * 80)
    print("DEMO 4: Workflow Library")
    print("=" * 80)

    # Create library
    library = WorkflowLibrary()

    print("\n> Created workflow library")

    # List built-in workflows
    workflows = library.list_all()
    print("\nBuilt-in workflows:")
    for wf in workflows:
        print(f"  - {wf.name}")
        print(f"    {wf.description}")
        print(f"    Steps: {len(wf.steps)}")

    # Search workflows
    print("\nSearch for 'github' workflows:")
    results = library.search(query="github")
    for wf in results:
        print(f"  - {wf.name}")

    # Suggest workflows for tools
    print("\nSuggest workflows for tools: [github_list_issues, github_create_pr]")
    suggestions = library.suggest_for_tools([
        "github_list_issues",
        "github_create_pr"
    ])
    for wf in suggestions:
        print(f"  - {wf.name}")
        print(f"    Matches {len(wf.steps)} of your tools")

    # Register custom workflow
    custom_workflow = WorkflowTemplate(
        name="custom_deployment",
        description="My custom deployment workflow",
        steps=[
            WorkflowStep(
                step_id="build",
                tool_name="docker_build",
                parameters={"image": "myapp"}
            ),
            WorkflowStep(
                step_id="deploy",
                tool_name="kubectl_apply",
                parameters={"manifest": "deployment.yaml"},
                depends_on=["build"]
            )
        ]
    )

    library.register(custom_workflow)
    print(f"\n> Registered custom workflow: {custom_workflow.name}")

    # Show updated library
    all_workflows = library.list_all()
    custom_workflows = [wf for wf in all_workflows if not wf.name.startswith("github_") and not wf.name.startswith("slack_")]
    print(f"\nTotal workflows: {len(all_workflows)}")
    print(f"   Custom workflows: {len(custom_workflows)}")


# =============================================================================
# Demo 5: Variable Substitution
# =============================================================================

def demo_variable_substitution():
    """Demonstrate variable substitution in parameters"""
    print("\n" + "=" * 80)
    print("DEMO 5: Variable Substitution")
    print("=" * 80)

    # Create context with nested data
    context = WorkflowContext(initial_variables={
        "env": "production",
        "replicas": 5,
        "config": {
            "timeout": 30,
            "retries": 3
        }
    })

    # Add step results
    context.set_result("build", {
        "image_id": "sha256:abc123",
        "metadata": {
            "version": "1.2.3",
            "size": 125
        }
    })

    print("\n> Context variables:")
    print(f"  env: {context.variables['env']}")
    print(f"  replicas: {context.variables['replicas']}")
    print(f"  config: {context.variables['config']}")

    print("\n> Step results:")
    build_result = context.get_result('build')
    print(f"  build.image_id: {build_result['image_id']}")
    print(f"  build.metadata.version: {build_result['metadata']['version']}")

    # Test substitution
    template = {
        "environment": "{{env}}",
        "image": "{{build.image_id}}",
        "version": "{{build.metadata.version}}",
        "replicas": "{{replicas}}",
        "timeout": "{{config.timeout}}s"
    }

    print("\nTemplate:")
    for key, value in template.items():
        print(f"  {key}: {value}")

    result = context.substitute(template)

    print("\nAfter substitution:")
    for key, value in result.items():
        print(f"  {key}: {value}")


# =============================================================================
# Main Demo Runner
# =============================================================================

async def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("WORKFLOW SYSTEM DEMO")
    print("=" * 80)

    # Run demos
    await demo_basic_workflow()
    await demo_parallel_execution()
    demo_pattern_detection()
    demo_workflow_library()
    demo_variable_substitution()

    # Summary
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  1. Workflow creation and execution")
    print("  2. Parallel execution of independent steps")
    print("  3. Pattern detection from usage logs")
    print("  4. Workflow library management")
    print("  5. Variable substitution and data flow")

    print("\nNext Steps:")
    print("  - Read docs/WORKFLOW_USAGE_GUIDE.md for complete API")
    print("  - Check docs/PHASE8_WORKFLOW_ARCHITECTURE.md for details")
    print("  - Run tests: pytest tests/test_workflow*.py -v")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
