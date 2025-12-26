# Example 20 - Approval Workflow (Human-in-the-Loop)

**Goal:** Multi-agent pipeline with a human approval gate. Demonstrates agent delegation, branching, and orchestration with manual confirmation.

## Steps
1) Draft output via agent (analysis_agent).
2) Validate via second agent (validator_agent).
3) Pause for human approval (simulated prompt/input).
4) Finalize via MCP tool (apply_changes).

## How to Run
```bash
cd examples/20-approval-workflow
python ../../scripts/dev_agents.py  # start local agents
# set AGENTS_CONFIG=agents.yaml  # optional if not in CWD
python workflow.py
```

## Files
- `workflow.py` - Main orchestration flow with approval gate
- `agents.yaml` - Agent definitions
- `requirements.txt` - Extra deps (if any)
- `test_example.py` - Smoke test placeholder

## Concepts Shown
- Multi-agent coordination
- Human-in-the-loop approval (blocking prompt)
- Branching logic (approve vs reject)
- Finalization via deterministic tool

## Expected Output
- Draft created
- Validation notes
- Prompt for approval
- Final application of changes when approved
