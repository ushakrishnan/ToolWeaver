# Sample 05: Workflow Library and Composition

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`


**Complexity:** ⭐⭐ Intermediate | **Time:** 15 minutes  
**Feature Demonstrated:** Reusable workflow patterns and automatic tool chaining

## Overview

### What This Example Does
Defines reusable workflow templates with automatic dependency resolution and parallel execution.

### Key Features Showcased
- **Workflow Definition**: Create multi-step workflows with dependencies
- **Automatic Parallelization**: Execute independent steps concurrently (25-40% speedup)
- **Workflow Library**: Save, version, and reuse workflow patterns
- **Composition**: Chain workflows together for complex processes

### Why This Matters

This example demonstrates ToolWeaver's workflow capabilities:
- Define reusable workflow templates
- Automatic dependency resolution between steps
- Parallel execution of independent tasks
- Save and load workflows from library
- Compose complex workflows from simple patterns

## Real-World Use Case

Common business processes often follow patterns:
- **Document Processing**: Upload → Extract → Validate → Store
- **Data Pipeline**: Fetch → Transform → Validate → Load
- **Notification Flow**: Detect Event → Filter → Format → Send

Instead of recoding these patterns, save them as workflows and reuse across projects.

## How It Works

1. **Define Workflow**: Specify steps and dependencies
2. **Register**: Save to workflow library
3. **Reuse**: Load and execute with different inputs
4. **Compose**: Chain workflows together for complex processes

## Architecture

```
Workflow Definition
    ↓
Step 1 ──→ Step 2 ──→ Step 4
    ↓         ↓
  Step 3 ─────┘
(parallel)  (sequential)

Execution Engine:
- Detects dependencies (DAG)
- Runs parallel steps concurrently
- Passes outputs between steps
- Handles errors and retries
```

## Workflow Patterns

### 1. Sequential (Pipeline)
```
Step A → Step B → Step C
```
Each step depends on previous step's output.

### 2. Parallel (Fan-out)
```
       ┌─→ Step B
Step A ├─→ Step C
       └─→ Step D
```
Independent steps run concurrently.

### 3. Conditional (Branch)
```
         ┌─→ Step B (if X)
Step A ──┤
         └─→ Step C (if Y)
```
Execute different paths based on conditions.

### 4. Map-Reduce
```
Step A → [Map over items] → Reduce → Step D
```
Process lists in parallel, then combine results.

## Files

- `workflow_demo.py` - Main example script
- `.env` - Your API keys (don't commit!)
- `.env.example` - Template for setup
- `README.md` - This file

## Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your API keys to `.env`

3. Install dependencies (from project root):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python workflow_demo.py
```

### Example Output

```
=== Workflow Library Example ===

Scenario 1: Receipt Processing Workflow
--------------------------------------
Workflow: receipt_processing_v1

Step 1: upload_image ✓ (125ms)
Step 2: extract_text ✓ (340ms)
Step 3: parse_items ✓ (180ms)
  ├─ Step 4a: categorize ✓ (95ms) [parallel]
  └─ Step 4b: validate ✓ (110ms) [parallel]
Step 5: generate_report ✓ (150ms)

Total: 1.0s (25% speedup via parallelization)

Scenario 2: Data Pipeline Workflow
----------------------------------
Workflow: etl_pipeline_v2

Step 1: fetch_data ✓ (450ms)
Step 2a: clean_data ✓ (220ms) [parallel]
Step 2b: validate_schema ✓ (180ms) [parallel]
Step 2c: enrich_data ✓ (310ms) [parallel]
Step 3: merge_results ✓ (90ms)
Step 4: load_database ✓ (280ms)

Total: 1.5s (33% speedup via parallelization)

Scenario 3: Compose Workflows
-----------------------------
Combining: receipt_processing + notification

Step 1: Execute receipt_processing workflow ✓
Step 2: Check if amount > $1000 ✓
Step 3: Send approval notification ✓

Total: 1.8s

Metrics:
- Workflows defined: 3
- Workflows executed: 3
- Total steps: 16
- Parallel steps: 5
- Time saved: 0.8s (30% reduction)
```

## Key Concepts

### 1. Workflow Definition

```python
from orchestrator.workflow import Workflow, WorkflowStep

workflow = Workflow(
    name="receipt_processing",
    description="Process receipt images end-to-end",
    steps=[
        WorkflowStep(id="1", tool="upload_image", depends_on=[]),
        WorkflowStep(id="2", tool="extract_text", depends_on=["1"]),
        WorkflowStep(id="3", tool="parse_items", depends_on=["2"]),
        WorkflowStep(id="4a", tool="categorize", depends_on=["3"]),
        WorkflowStep(id="4b", tool="validate", depends_on=["3"]),
        WorkflowStep(id="5", tool="report", depends_on=["4a", "4b"])
    ]
)
```

### 2. Dependency Resolution

The engine automatically:
- Builds DAG (Directed Acyclic Graph)
- Identifies parallel steps (4a, 4b)
- Determines execution order
- Handles errors (retry, fallback)

### 3. Workflow Library

```python
from orchestrator.workflow_library import WorkflowLibrary

library = WorkflowLibrary()

# Save workflow

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

library.save(workflow, version="v1")

# Load workflow

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

loaded = library.load("receipt_processing", version="v1")

# List available workflows

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

workflows = library.list()
```

### 4. Workflow Composition

```python
# Compose two workflows

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

combined = workflow1.then(workflow2)

# Conditional composition

> **Note:** This sample uses ToolWeaver from PyPI. Install with: `pip install -r requirements.txt`

workflow.if_condition(
    condition=lambda result: result['amount'] > 1000,
    then_workflow=approval_workflow,
    else_workflow=auto_process_workflow
)
```

## Benefits

**Reusability**
- Define once, use many times
- Version control workflows
- Share across team

**Maintainability**
- Update workflow in one place
- Test workflows independently
- Clear documentation

**Performance**
- Automatic parallelization (25-40% speedup)
- Dependency optimization
- Resource scheduling

**Reliability**
- Error handling built-in
- Retry logic
- Rollback capability

## Configuration Options

```python
WorkflowEngine(
    max_parallel=4,              # Max concurrent steps
    retry_failed_steps=True,     # Auto-retry on failure
    max_retries=3,               # Retry limit
    timeout_per_step=30,         # Step timeout (seconds)
    save_intermediate=True,      # Save step outputs
    enable_rollback=True         # Rollback on error
)
```

## Advanced Features

The example demonstrates:
- Parallel execution optimization
- Error handling and recovery
- Conditional branching
- Map-reduce patterns
- Workflow composition
- Version management
- Performance monitoring

## Related Examples

- **Sample 02**: Uses simple workflows internally
- **Sample 10**: Multi-step planning generates workflows
- **Sample 11**: Programmatic executor for complex flows

## Learn More

- [Workflow Documentation](../../docs/WORKFLOW_USAGE_GUIDE.md)
- [Workflow Architecture](../../docs/WORKFLOW_ARCHITECTURE.md)
- [Features Guide](../../docs/FEATURES_GUIDE.md)
