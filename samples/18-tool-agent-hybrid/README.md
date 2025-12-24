# Example 18: Tool + Agent Hybrid Workflow

This example demonstrates combining MCP tools with A2A agents in a single workflow:

1. **Tool Step**: Use MCP tool to fetch/transform data (deterministic, low-cost)
2. **Agent Step**: Delegate complex analysis to external agent (flexible, higher-cost)
3. **Tool Step**: Use tool to format results (deterministic)

## Why Hybrid?

| Scenario | Best Approach |
|----------|---------------|
| Simple transformations | MCP Tool (fast, cheap) |
| Complex analysis | A2A Agent (flexible, powerful) |
| Deterministic processing | MCP Tool |
| ML/AI inference | A2A Agent |
| Report formatting | MCP Tool |

## Workflow

```
Tool: Fetch Data
      ↓
Tool: Validate Data
      ↓
Agent: Analyze & Generate Insights
      ↓
Tool: Format Report
      ↓
Output
```

## Cost Optimization

- Use tools for simple, repeatable operations
- Use agents for complex, one-time analysis
- Cache tool results to avoid re-computation
- Consider agent cost vs. local computation

## Files

- `hybrid_workflow.py` - Tool + agent hybrid example
- `agents.yaml` - Agent configuration

## Running

```bash
python hybrid_workflow.py
```
