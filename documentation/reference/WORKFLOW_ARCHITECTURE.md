# Workflow System Architecture

## Overview

The workflow system enables automatic tool chaining and workflow optimization by recognizing common patterns, managing dependencies, and sharing context between tool executions.

## Goals

1. **Tool Composition**: Automatically chain multiple tools into workflows
2. **Pattern Recognition**: Learn common tool sequences from usage logs
3. **Context Sharing**: Pass data between tools efficiently without LLM context overhead
4. **Dependency Management**: Handle tool dependencies with parallel execution where possible

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow System                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐      ┌────────────────────┐          │
│  │ WorkflowTemplate │──────│  WorkflowStep      │          │
│  │                  │      │                    │          │
│  │ - name           │      │ - step_id          │          │
│  │ - steps[]        │      │ - tool_name        │          │
│  │ - metadata       │      │ - depends_on[]     │          │
│  └──────────────────┘      │ - parameters       │          │
│          │                 └────────────────────┘          │
│          │                                                  │
│          ▼                                                  │
│  ┌──────────────────┐      ┌────────────────────┐          │
│  │ WorkflowExecutor │──────│  WorkflowContext   │          │
│  │                  │      │                    │          │
│  │ - execute()      │      │ - shared_data{}    │          │
│  │ - resolve_deps() │      │ - results{}        │          │
│  │ - parallel_exec()│      │ - get()/set()      │          │
│  └──────────────────┘      └────────────────────┘          │
│          │                                                  │
│          ▼                                                  │
│  ┌──────────────────┐      ┌────────────────────┐          │
│  │ PatternDetector  │──────│ WorkflowLibrary    │          │
│  │                  │      │                    │          │
│  │ - analyze_logs() │      │ - templates{}      │          │
│  │ - find_patterns()│      │ - suggest()        │          │
│  │ - suggest()      │      │ - cache_pattern()  │          │
│  └──────────────────┘      └────────────────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Data Models

### WorkflowTemplate

Defines a reusable workflow with multiple steps and dependencies.

```python
@dataclass
class WorkflowTemplate:
    """
    A reusable workflow template.
    
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
                        "title": "{{pr_title}}",
                        "body": "Fixes {{list_issues.issues[0].number}}"
                    }
                ),
                WorkflowStep(
                    step_id="notify_slack",
                    tool_name="slack_send_message",
                    depends_on=["create_pr"],
                    parameters={
                        "channel": "#dev",
                        "message": "PR created: {{create_pr.url}}"
                    }
                )
            ],
            metadata={
                "category": "github",
                "usage_count": 15,
                "success_rate": 0.93
            }
        )
    """
    name: str
    description: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = field(default_factory=dict)
    parallel_groups: Optional[List[List[str]]] = None  # step_ids that can run in parallel
```

### WorkflowStep

A single step in a workflow with dependencies and parameter templates.

```python
@dataclass
class WorkflowStep:
    """
    A single step in a workflow.
    
    Features:
    - Tool name reference
    - Parameter templates with variable substitution
    - Dependency tracking (depends_on)
    - Conditional execution (condition)
    - Retry configuration
    """
    step_id: str
    tool_name: str
    parameters: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    condition: Optional[str] = None  # e.g., "{{step1.success}} == true"
    retry_count: int = 0
    timeout_seconds: Optional[int] = None
```

### WorkflowContext

Shared context for passing data between workflow steps.

```python
class WorkflowContext:
    """
    Shared context for workflow execution.
    
    Features:
    - Store step results
    - Share data between steps
    - Variable substitution ({{step_id.field}})
    - Type-safe data access
    """
    
    def __init__(self):
        self.shared_data: Dict[str, Any] = {}
        self.step_results: Dict[str, Any] = {}
        self.variables: Dict[str, Any] = {}
    
    def set_result(self, step_id: str, result: Any):
        """Store result from a step execution"""
        self.step_results[step_id] = result
    
    def get_result(self, step_id: str) -> Any:
        """Retrieve result from a previous step"""
        return self.step_results.get(step_id)
    
    def substitute(self, template: str) -> str:
        """
        Substitute variables in template.
        
        Supports:
        - {{variable}} - Direct variable substitution
        - {{step_id.field}} - Access step result fields
        - {{step_id.field.nested}} - Nested field access
        """
        pass
```

## Workflow Execution

### Dependency Resolution

The WorkflowExecutor resolves dependencies using topological sort:

```
Steps: [A, B, C, D, E]
Dependencies:
  B depends on A
  C depends on A
  D depends on B, C
  E depends on D

Execution Order:
  Level 0: A           (no dependencies)
  Level 1: B, C        (parallel - both depend only on A)
  Level 2: D           (depends on B and C)
  Level 3: E           (depends on D)
```

### Parallel Execution

Steps at the same dependency level can execute in parallel:

```python
async def execute_workflow(self, workflow: WorkflowTemplate, context: WorkflowContext):
    """
    Execute workflow with dependency-aware parallel execution.
    
    1. Build dependency graph
    2. Topological sort to find execution levels
    3. Execute each level in parallel (asyncio.gather)
    4. Handle errors with retry logic
    5. Return final results
    """
    levels = self._resolve_dependencies(workflow.steps)
    
    for level in levels:
        # Execute all steps in this level in parallel
        tasks = [self._execute_step(step, context) for step in level]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle errors
        for step, result in zip(level, results):
            if isinstance(result, Exception):
                await self._handle_error(step, result, context)
```

## Pattern Recognition

### Usage Log Analysis

Detect common tool sequences from monitoring logs:

```python
class PatternDetector:
    """
    Analyze tool usage patterns and suggest workflows.
    
    Features:
    - Sequence mining (find common tool chains)
    - Frequency analysis (identify popular patterns)
    - Context similarity (group similar use cases)
    - Automatic workflow generation
    """
    
    def analyze_logs(self, logs: List[ToolUsageLog]) -> List[Pattern]:
        """
        Find common patterns in tool usage logs.
        
        Algorithm:
        1. Group logs by session/request_id
        2. Extract tool sequences (A → B → C)
        3. Count frequency of sequences
        4. Filter by minimum frequency (e.g., 5 occurrences)
        5. Calculate success rate
        6. Return patterns sorted by (frequency * success_rate)
        """
        pass
    
    def suggest_workflow(self, tools: List[str]) -> Optional[WorkflowTemplate]:
        """
        Suggest a workflow based on tool names.
        
        If tools match a known pattern (e.g., github_list_issues + github_create_pr),
        return a pre-built workflow template.
        """
        pass
```

### Common Patterns to Detect

1. **GitHub PR Workflow**: list issues → create PR → notify Slack
2. **Data Pipeline**: fetch data → transform → store → notify
3. **Approval Workflow**: create item → notify approver → wait → update
4. **Search & Report**: search multiple sources → aggregate → format → send

## Variable Substitution

### Template Syntax

Support flexible variable substitution in workflow parameters:

```python
# Direct variable
"{{variable_name}}"

# Step result field
"{{step_id.field}}"

# Nested field
"{{step_id.user.email}}"

# Array access
"{{step_id.items[0].name}}"

# Conditional
"{{step_id.success ? 'yes' : 'no'}}"

# Default value
"{{variable_name|default:'fallback'}}"
```

### Implementation

Use regex-based template engine with safe evaluation:

```python
def substitute_variables(template: str, context: WorkflowContext) -> str:
    """
    Replace {{variable}} placeholders with actual values.
    
    Example:
        template = "PR created: {{create_pr.url}}"
        context.step_results = {
            "create_pr": {"url": "https://github.com/repo/pulls/1"}
        }
        result = "PR created: https://github.com/repo/pulls/1"
    """
    pattern = r"\{\{([^}]+)\}\}"
    
    def replacer(match):
        expression = match.group(1).strip()
        return evaluate_expression(expression, context)
    
    return re.sub(pattern, replacer, template)
```

## Error Handling

### Retry Logic

Support automatic retries for transient failures:

```python
@dataclass
class RetryConfig:
    max_retries: int = 3
    backoff_seconds: int = 2
    backoff_multiplier: float = 2.0  # Exponential backoff
    retryable_errors: List[Type[Exception]] = field(default_factory=list)
```

### Fallback Strategies

1. **Skip and Continue**: Mark step as failed but continue workflow
2. **Fallback Step**: Execute alternative step on failure
3. **Abort Workflow**: Stop entire workflow on critical failure
4. **Compensating Action**: Undo previous steps (rollback)

## Workflow Library

### Pre-built Workflows

Ship with common workflow templates:

```python
BUILTIN_WORKFLOWS = {
    "github_pr_workflow": WorkflowTemplate(...),
    "slack_notification_chain": WorkflowTemplate(...),
    "data_pipeline": WorkflowTemplate(...),
    "approval_workflow": WorkflowTemplate(...),
}
```

### Custom Workflows

Users can define custom workflows:

```python
# workflows/custom_workflows.py
custom_workflow = WorkflowTemplate(
    name="my_custom_workflow",
    description="My specific use case",
    steps=[...]
)

# Register workflow
workflow_library.register(custom_workflow)
```

## Integration with Existing System

### Tool Search Integration

Use tool_search_tool (Phase 6) to find tools for workflow steps:

```python
async def build_workflow_from_description(self, description: str) -> WorkflowTemplate:
    """
    Use LLM + tool search to build workflow from natural language.
    
    Example:
        description = "Create a GitHub PR and notify the team on Slack"
        
        1. LLM breaks down into steps:
           - Search for issues
           - Create PR
           - Send Slack message
        
        2. Use tool_search_tool to find matching tools
        
        3. Generate WorkflowTemplate
    """
    pass
```

### Monitoring Integration

Log workflow executions for pattern detection:

```python
workflow_monitor.log_execution(
    workflow_name="github_pr_workflow",
    duration_ms=1250,
    success=True,
    steps_executed=3,
    context={"repo": "myrepo", "pr_number": 123}
)
```

## Performance Considerations

### Parallel Execution Benefits

For a 3-step workflow with independent steps:

```
Sequential: 100ms + 100ms + 100ms = 300ms
Parallel: max(100ms, 100ms, 100ms) = 100ms
Improvement: 3x faster
```

### Context Overhead

Minimize LLM context by keeping intermediate results in WorkflowContext:

```
Without workflows:
  LLM Request 1: "List GitHub issues" → 500 tokens
  LLM Request 2: "Here are the issues: [...]. Create PR" → 2000 tokens
  LLM Request 3: "PR created. Notify Slack" → 1500 tokens
  Total: 4000 tokens

With workflows:
  LLM Request 1: "Execute github_pr_workflow" → 500 tokens
  (Workflow executes internally, results passed via context)
  Total: 500 tokens
  
Savings: 87.5% token reduction
```

## Success Metrics

- **Workflow Adoption**: % of multi-tool tasks using workflows
- **Execution Time**: Average time savings from parallel execution
- **Token Reduction**: % reduction in LLM tokens from context sharing
- **Pattern Detection**: Number of patterns detected from logs
- **Success Rate**: % of workflow executions that complete successfully

## Next Steps (Implementation)

1. ✅ **Phase 8 Architecture** (this document)
2. Implement core workflow system (WorkflowTemplate, WorkflowStep, WorkflowContext)
3. Implement WorkflowExecutor with dependency resolution
4. Add pattern detection from usage logs
5. Create pre-built workflow library
6. Comprehensive testing
7. Documentation and examples

---

**Status**: 📋 Architecture Complete - Ready for Implementation  
**Estimated Effort**: 1 week  
**Dependencies**: Phase 6 (Tool Search Tool) recommended
