# Cost Optimization & Error Recovery

This example demonstrates cost-aware tool selection and error recovery strategies.

## Key concepts

1. **Cost Optimizer** - Select tools based on cost/latency/reliability tradeoffs
2. **Error Recovery Policies** - Strategies for handling tool failures
3. **Tool Registry** - Centralized tool management with metadata
4. **Fallback chains** - Try alternative tools when primary fails

## Run it

```bash
python main.py
```

## What you'll see

- **Scenario 1**: Budget-constrained selection (pick cheapest within $0.02)
- **Scenario 2**: Latency-constrained selection (pick fastest within 1s)
- **Scenario 3**: Ranked comparison of all tools
- **Scenario 4**: Async execution with fallback to backup tool
- **Scenario 5**: Automatic retry with exponential backoff

## Key learning

When you have multiple tools that can solve a problem:
- Use `SelectionConfig` to define your constraints
- Use `CostOptimizer` to rank and pick the best fit
- Use `ErrorRecoveryPolicy` for automatic retry/fallback
- Let the tool registry handle the orchestration
