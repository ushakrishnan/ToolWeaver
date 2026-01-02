# Legacy Demo Applications

**⚠️ DEPRECATION NOTICE:** These demos use old import patterns from before the Phase 0 (Package-First) restructure. Many imports are **broken** and won't work with the current package. 

**For current, maintained examples, see the main [samples folder](../)** (01-32).

## Migration to Current Samples

This folder contains original demo and test scripts from ToolWeaver's development. **New users should start with the structured samples in the parent directory** ([01-basic-receipt-processing](../01-basic-receipt-processing/) through [32-idempotency-retry](../32-idempotency-retry/)).

### What Changed?

The package was restructured with a clean public API. Old imports like `from orchestrator.orchestrator import execute_plan` no longer work. See [PACKAGE_COMPLIANCE_REVIEW.md](../PACKAGE_COMPLIANCE_REVIEW.md) for migration guide.

## Quick Reference

### Main Demos

| File | Purpose |
|------|---------|
| `run_demo.py` | Execute predefined execution plans |
| `run_planner_demo.py` | Natural language → plan → execution |
| `usage_examples.py` | Basic tool registration and usage |

### Testing Scripts

| File | Purpose |
|------|---------|
| `test_discovery.py` | Tool discovery validation |
| `test_search.py` | Semantic search demo |
| `test_azure_connection.py` | Azure Computer Vision test |
| `test_github_mcp.py` | GitHub MCP server test |
| `test_monitoring_integration.py` | Monitoring backends test |

### Feature Demos

| File | Purpose |
|------|---------|
| `demo_auto_discover.py` | Automatic tool discovery |
| `demo_integrated.py` | Integrated orchestrator |
| `demo_monitoring_backends.py` | Monitoring backends |
| `demo_tool_examples.py` | Tool registration examples |
| `demo_workflow.py` | Workflow execution |

### Data Files

| File | Purpose |
|------|---------|
| `example_plan.json` | Basic execution plan |
| `example_plan_hybrid.json` | Advanced execution plan with parallel steps |

## Usage

```bash
# From this directory
python run_demo.py
python run_planner_demo.py "Your task here"
python test_discovery.py

# Or from project root
python examples/legacy-demos/run_demo.py
```

## Why Legacy?

These files were created during development and testing. While they still work, the new structured examples ([01-12](../)) provide:
- Clearer documentation
- Consistent structure
- Step-by-step learning path
- Real-world use cases

**Recommendation:** Start with the structured examples unless you need these specific test cases.
