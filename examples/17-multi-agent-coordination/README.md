# Example 17: Multi-Agent Coordination

This example demonstrates coordinating multiple agents to complete a complex task:
1. Agent A fetches and prepares data
2. Agent B analyzes the data
3. Agent C generates a report

## Architecture

```
Data Fetcher Agent
        ↓ (raw_data)
Data Analyst Agent
        ↓ (insights)
Report Generator Agent
        ↓ (report)
Final Output
```

## Key Patterns

1. **Sequential Coordination**: Pass outputs from one agent to the next
2. **Error Handling**: Implement fallbacks if an agent fails
3. **Cost Tracking**: Monitor total cost across all delegations
4. **Monitoring**: Track latency and success rates

## Files

- `coordinate_agents.py` - Sequential agent coordination
- `agents.yaml` - Agent configuration

## Running

```bash
python coordinate_agents.py
```

## Expected Output

```
Step 1: Fetching data...
  ✓ Data fetched (10.5s)
Step 2: Analyzing data...
  ✓ Analysis complete (25.3s)
Step 3: Generating report...
  ✓ Report generated (15.2s)
Total cost: $0.50
```
