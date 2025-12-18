# Example 19 - Fetch → Analyze → Store (Hybrid: Tools + Agents)

**Goal:** End-to-end pipeline that fetches data via tool, analyzes via agent, and stores results via tool. Demonstrates hybrid orchestration (tool → agent → tool), streaming, and cost tracking.

## Steps
1) Discover tools and agents (unified).
2) Fetch data via MCP tool (deterministic, fast).
3) Analyze data via A2A agent (reasoning, streaming output).
4) Store structured result via MCP tool (deterministic).
5) Capture monitoring + cost metrics.

## How to Run
```bash
cd examples/19-fetch-analyze-store
python ../../scripts/dev_agents.py  # in a separate terminal
# (optional) set if agents.yaml is elsewhere
# set AGENTS_CONFIG=agents.yaml
python workflow.py
```

## Files
- `workflow.py` - Main orchestration flow
- `agents.yaml` - Agent definitions (sample)
- `requirements.txt` - Extra deps (if any)
- `test_example.py` - Smoke test placeholder

## Concepts Shown
- Unified discovery of MCP tools + A2A agents
- Hybrid routing via `execute_tool` and `execute_agent_step`
- Streaming responses from agent analysis
- Cost/latency logging via monitoring backend

## Expected Output
- Printed summary of analysis
- Stored record confirmation
- Cost/latency logs in monitoring backend (if configured)
