# Workflow Usage Guide

Complete guide to using ToolWeaver's workflow composition system.

## Table of Contents

1. [Overview](#overview)
2. [Basic Concepts](#basic-concepts)
3. [Creating Workflows](#creating-workflows)
4. [Executing Workflows](#executing-workflows)
5. [Pattern Detection](#pattern-detection)
6. [Workflow Library](#workflow-library)
7. [Advanced Features](#advanced-features)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)

---

## Overview

The workflow system allows you to:

- **Compose multi-step tool chains** with dependencies
- **Execute steps in parallel** when possible
- **Share data between steps** using variable substitution
- **Learn from usage patterns** to suggest common workflows
- **Reuse workflows** with a built-in library

## Basic Concepts

### Workflow Components

```
WorkflowTemplate
├── WorkflowStep (step1)
│   ├── tool_name: "github_list_issues"
│   ├── parameters: {...}
│   └── dependencies: []
├── WorkflowStep (step2)
│   ├── tool_name: "github_create_pr"
│   ├── parameters: {"issue_id": "{{step1.issue_id}}"}
│   └── dependencies: ["step1"]
└── WorkflowStep (step3)
    ├── tool_name: "slack_send_message"
    ├── parameters: {"pr_url": "{{step2.pr_url}}"}
    └── dependencies: ["step2"]
```

### Execution Flow

1. **Dependency Resolution**: Steps organized into execution levels
2. **Parallel Execution**: Independent steps run concurrently
3. **Variable Substitution**: Parameters filled from context
4. **Error Handling**: Failed steps stop dependent steps
5. **Result Storage**: Step outputs saved to context

---

## Creating Workflows

### Simple Linear Workflow

```python
from orchestrator.workflow import WorkflowTemplate, WorkflowStep

# Create workflow
workflow = WorkflowTemplate(
    name="deploy_to_staging",
    description="Deploy application to staging environment",
    steps=[
        WorkflowStep(
            id="build",
            tool_name="docker_build",
            parameters={"image": "myapp:latest"}
        ),
        WorkflowStep(
            id="push",
            tool_name="docker_push",
            parameters={"image": "myapp:latest"},
            depends_on=["build"]
        ),
        WorkflowStep(
            id="deploy",
            tool_name="kubectl_apply",
            parameters={"manifest": "staging.yaml"},
            depends_on=["push"]
        )
    ]
)
```

### Workflow with Parallel Steps

```python
workflow = WorkflowTemplate(
    name="deploy_multi_region",
    description="Deploy to multiple regions in parallel",
    steps=[
        WorkflowStep(
            id="build",
            tool_name="docker_build",
            parameters={"image": "myapp:latest"}
        ),
        # These run in parallel after build completes
        WorkflowStep(
            id="deploy_us",
            tool_name="kubectl_apply",
            parameters={"region": "us-east-1"},
            depends_on=["build"]
        ),
        WorkflowStep(
            id="deploy_eu",
            tool_name="kubectl_apply",
            parameters={"region": "eu-west-1"},
            depends_on=["build"]
        ),
        WorkflowStep(
            id="deploy_asia",
            tool_name="kubectl_apply",
            parameters={"region": "ap-southeast-1"},
            depends_on=["build"]
        )
    ]
)
```

### Variable Substitution

```python
workflow = WorkflowTemplate(
    name="github_pr_workflow",
    description="Create PR and notify team",
    steps=[
        WorkflowStep(
            id="list_issues",
            tool_name="github_list_issues",
            parameters={
                "repo": "{{repo}}",
                "state": "open"
            }
        ),
        WorkflowStep(
            id="create_pr",
            tool_name="github_create_pr",
            parameters={
                "repo": "{{repo}}",
                "title": "Fix issue {{list_issues.issue_id}}",
                "body": "{{list_issues.issue_description}}"
            },
            depends_on=["list_issues"]
        ),
        WorkflowStep(
            id="notify",
            tool_name="slack_send_message",
            parameters={
                "channel": "{{slack_channel}}",
                "message": "PR created: {{create_pr.pr_url}}"
            },
            depends_on=["create_pr"]
        )
    ]
)
```

### Conditional Execution

```python
WorkflowStep(
    id="notify_on_failure",
    tool_name="slack_send_message",
    parameters={
        "channel": "alerts",
        "message": "Build failed!"
    },
    depends_on=["build"],
    condition="{{build.success}} == False"
)
```

### Retry Logic

```python
WorkflowStep(
    id="unstable_api",
    tool_name="call_external_api",
    parameters={"endpoint": "https://api.example.com"},
    max_retries=3,
    retry_delay=2.0  # seconds
)
```

---

## Executing Workflows

### Basic Execution

```python
from orchestrator.workflow import WorkflowExecutor, WorkflowContext

# Create executor and context
executor = WorkflowExecutor()
context = WorkflowContext(
    variables={
        "repo": "myorg/myrepo",
        "slack_channel": "#deployments"
    }
)

# Execute workflow
result = await executor.execute(workflow, context)

# Check results
print(f"Status: {result['status']}")
print(f"Steps completed: {len(result['completed_steps'])}")
print(f"Duration: {result['duration']:.2f}s")

# Access step results
pr_url = context.get_result("create_pr", "pr_url")
print(f"Created PR: {pr_url}")
```

### Handling Errors

```python
result = await executor.execute(workflow, context)

if result['status'] == 'failed':
    print(f"Workflow failed: {result['error']}")
    
    # Check which steps failed
    for step in result['failed_steps']:
        error = context.get_error(step['id'])
        print(f"Step {step['id']} failed: {error}")
```

### Accessing Step Results

```python
# Get full result
build_result = context.get_result("build")
print(build_result)  # {'image_id': '...', 'size_mb': 125, ...}

# Get specific field
image_id = context.get_result("build", "image_id")

# Get nested field
config = context.get_result("deploy", "status.config.replicas")
```

---

## Pattern Detection

### Analyzing Usage Logs

```python
from orchestrator.workflow_library import PatternDetector
from orchestrator.monitoring import create_monitor

# Collect logs during normal operation
monitor = create_monitor()

# ... application runs, logs tool calls ...

# Detect patterns
detector = PatternDetector(
    min_frequency=3,      # Pattern must appear 3+ times
    min_success_rate=0.8  # Pattern must succeed 80%+ of the time
)

patterns = detector.analyze_logs(
    logs=monitor.tool_call_log,
    max_sequence_length=5
)

# Review patterns
for pattern in patterns:
    print(f"Pattern: {' → '.join(pattern.tools)}")
    print(f"  Frequency: {pattern.frequency}")
    print(f"  Success rate: {pattern.success_rate:.1%}")
    print(f"  Avg duration: {pattern.avg_duration_ms:.0f}ms")
    print()
```

### Converting Patterns to Workflows

```python
# Suggest workflow from detected pattern
workflow = detector.suggest_workflow(
    pattern=patterns[0],
    name="auto_deploy_workflow",
    description="Auto-detected deployment pattern"
)

print(f"Created workflow with {len(workflow.steps)} steps")
```

---

## Workflow Library

### Using Built-in Workflows

```python
from orchestrator.workflow_library import WorkflowLibrary

# Create library (loads built-in workflows)
library = WorkflowLibrary()

# List available workflows
workflows = library.list_all()
for wf in workflows:
    print(f"{wf.name}: {wf.description}")
    print(f"  Category: {wf.category}")
    print(f"  Steps: {len(wf.steps)}")

# Get specific workflow
pr_workflow = library.get("github_pr_workflow")
```

### Registering Custom Workflows

```python
# Register custom workflow
library.register(workflow, is_builtin=False)

# Save to disk for persistence
library.save_to_disk("custom_workflows.json")

# Load later
library2 = WorkflowLibrary()
library2.load_from_disk("custom_workflows.json")
```

### Searching Workflows

```python
# Search by query
results = library.search(query="deploy kubernetes")

# Search by category
results = library.search(category="deployment")

# Search by tool name
results = library.search(tool_name="docker_build")

# Combine filters
results = library.search(
    query="deployment",
    category="devops",
    tool_name="kubectl"
)
```

### Suggesting Workflows

```python
# Suggest workflows for given tools
suggestions = library.suggest_for_tools([
    "github_list_issues",
    "github_create_pr"
])

for workflow in suggestions:
    print(f"Suggested: {workflow.name}")
    print(f"  Matches {len(workflow.steps)} of your tools")
```

---

## Advanced Features

### Dynamic Parameters

```python
# Parameters can reference:
# - Variables: {{variable_name}}
# - Step results: {{step_id.field}}
# - Nested fields: {{step_id.data.nested.field}}
# - List items: {{step_id.items[0]}}

WorkflowStep(
    id="process",
    tool_name="data_processor",
    parameters={
        "input": "{{source_url}}",
        "output": "{{base_path}}/{{process_id}}.json",
        "config": {
            "batch_size": "{{config.batch_size}}",
            "timeout": "{{timeout_seconds}}"
        }
    }
)
```

### Workflow Composition

```python
# Embed workflow as a step
sub_workflow = library.get("database_backup")

WorkflowStep(
    id="backup",
    tool_name="execute_workflow",
    parameters={
        "workflow": sub_workflow,
        "context": {"db": "{{database_name}}"}
    }
)
```

### Error Recovery

```python
# Add error handling step
WorkflowStep(
    id="cleanup",
    tool_name="cleanup_resources",
    parameters={"resource_id": "{{deploy.resource_id}}"},
    depends_on=["deploy"],
    condition="{{deploy.success}} == False",  # Only run on failure
    description="Cleanup after failed deployment"
)
```

### Monitoring and Logging

```python
# Execution includes detailed logging
result = await executor.execute(workflow, context)

# Check execution details
print(f"Total duration: {result['duration']:.2f}s")
print(f"Steps executed: {len(result['completed_steps'])}")
print(f"Parallel speedup: {result.get('parallel_speedup', 1.0):.1f}x")

# Review step timeline
for step in result['completed_steps']:
    print(f"{step['id']}: {step['duration']:.2f}s")
```

---

## Best Practices

### 1. Design Workflows for Reusability

```python
# ✅ Good: Parameterized and reusable
workflow = WorkflowTemplate(
    name="deploy_service",
    description="Deploy any service to any environment",
    steps=[
        WorkflowStep(
            id="deploy",
            tool_name="kubectl_apply",
            parameters={
                "service": "{{service_name}}",
                "environment": "{{environment}}",
                "replicas": "{{replicas}}"
            }
        )
    ]
)

# ❌ Bad: Hard-coded values
workflow = WorkflowTemplate(
    name="deploy_api_prod",
    steps=[
        WorkflowStep(
            id="deploy",
            tool_name="kubectl_apply",
            parameters={
                "service": "api-server",
                "environment": "production",
                "replicas": 5
            }
        )
    ]
)
```

### 2. Use Descriptive Names

```python
# ✅ Good
WorkflowStep(
    id="fetch_open_issues",
    tool_name="github_list_issues",
    description="Fetch all open issues for review"
)

# ❌ Bad
WorkflowStep(
    id="step1",
    tool_name="github_list_issues"
)
```

### 3. Add Explicit Dependencies

```python
# ✅ Good: Clear dependencies
WorkflowStep(
    id="deploy",
    tool_name="kubectl_apply",
    depends_on=["build", "test", "security_scan"]
)

# ❌ Bad: Implicit dependencies via variable substitution
WorkflowStep(
    id="deploy",
    tool_name="kubectl_apply",
    parameters={"image": "{{build.image_id}}"}  # Hidden dependency!
)
```

### 4. Handle Errors Gracefully

```python
# Add cleanup steps
WorkflowStep(
    id="cleanup_on_failure",
    tool_name="cleanup",
    depends_on=["deploy"],
    condition="{{deploy.success}} == False",
    description="Cleanup resources if deployment fails"
)

# Use retries for flaky operations
WorkflowStep(
    id="external_api_call",
    tool_name="call_api",
    max_retries=3,
    retry_delay=2.0
)
```

### 5. Optimize for Parallelism

```python
# ✅ Good: Parallel execution
steps = [
    WorkflowStep(id="setup", ...),
    # These can run in parallel
    WorkflowStep(id="test_unit", depends_on=["setup"]),
    WorkflowStep(id="test_integration", depends_on=["setup"]),
    WorkflowStep(id="test_e2e", depends_on=["setup"]),
    # This waits for all tests
    WorkflowStep(id="report", depends_on=["test_unit", "test_integration", "test_e2e"])
]

# ❌ Bad: Unnecessary serialization
steps = [
    WorkflowStep(id="test_unit"),
    WorkflowStep(id="test_integration", depends_on=["test_unit"]),
    WorkflowStep(id="test_e2e", depends_on=["test_integration"])
]
```

### 6. Learn from Patterns

```python
# Regularly analyze patterns to discover workflows
patterns = detector.analyze_logs(monitor.tool_call_log)

# Convert common patterns to reusable workflows
for pattern in patterns[:5]:  # Top 5 patterns
    if pattern.frequency >= 10 and pattern.success_rate >= 0.9:
        workflow = detector.suggest_workflow(pattern)
        library.register(workflow, is_builtin=False)

# Save for future use
library.save_to_disk("learned_workflows.json")
```

---

## API Reference

### WorkflowStep

```python
@dataclass
class WorkflowStep:
    id: str                      # Unique step identifier
    tool_name: str               # Tool to execute
    parameters: Dict[str, Any]   # Tool parameters (supports {{variables}})
    depends_on: List[str] = []   # Step IDs this depends on
    condition: Optional[str] = None  # Conditional execution
    max_retries: int = 0         # Number of retries
    retry_delay: float = 1.0     # Delay between retries (seconds)
    description: str = ""        # Human-readable description
```

### WorkflowTemplate

```python
@dataclass
class WorkflowTemplate:
    name: str                    # Workflow name
    description: str             # Human-readable description
    steps: List[WorkflowStep]    # Workflow steps
    category: str = "general"    # Category for organization
    tags: List[str] = []         # Tags for search
    
    def validate(self) -> None:
        """Validate workflow structure"""
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get step by ID"""
```

### WorkflowContext

```python
class WorkflowContext:
    def __init__(self, variables: Optional[Dict[str, Any]] = None):
        """Initialize with variables"""
    
    def set_result(self, step_id: str, result: Any) -> None:
        """Store step result"""
    
    def get_result(self, step_id: str, field: Optional[str] = None) -> Any:
        """Get step result (optionally specific field)"""
    
    def set_error(self, step_id: str, error: str) -> None:
        """Record step error"""
    
    def substitute(self, template: Any) -> Any:
        """Substitute {{variables}} in template"""
```

### WorkflowExecutor

```python
class WorkflowExecutor:
    async def execute(
        self,
        workflow: WorkflowTemplate,
        context: WorkflowContext,
        tool_registry: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute workflow.
        
        Returns:
            {
                'status': 'completed' | 'failed',
                'duration': float,
                'completed_steps': List[Dict],
                'failed_steps': List[Dict],
                'error': Optional[str]
            }
        """
```

### PatternDetector

```python
class PatternDetector:
    def __init__(self, min_frequency: int = 3, min_success_rate: float = 0.7):
        """Initialize pattern detector"""
    
    def analyze_logs(
        self,
        logs: List[ToolCallMetric],
        max_sequence_length: int = 5
    ) -> List[ToolSequence]:
        """Detect common tool sequences"""
    
    def suggest_workflow(
        self,
        pattern: ToolSequence,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> WorkflowTemplate:
        """Generate workflow from pattern"""
```

### WorkflowLibrary

```python
class WorkflowLibrary:
    def __init__(self):
        """Initialize library with built-in workflows"""
    
    def register(self, workflow: WorkflowTemplate, is_builtin: bool = False):
        """Register workflow"""
    
    def get(self, name: str) -> Optional[WorkflowTemplate]:
        """Get workflow by name"""
    
    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tool_name: Optional[str] = None
    ) -> List[WorkflowTemplate]:
        """Search workflows"""
    
    def suggest_for_tools(self, tools: List[str]) -> List[WorkflowTemplate]:
        """Suggest workflows for given tools"""
    
    def save_to_disk(self, filepath: str):
        """Save custom workflows"""
    
    def load_from_disk(self, filepath: str):
        """Load custom workflows"""
```

---

## Examples

See [examples/demo_workflow.py](../examples/demo_workflow.py) for complete working examples.

## Next Steps

- Learn about [integration with the orchestrator](ARCHITECTURE.md)
- Explore [monitoring and observability](PRODUCTION_DEPLOYMENT.md#monitoring)
- See [performance optimization](PHASE7_PERFORMANCE_OPTIMIZATION.md)
