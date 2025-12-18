# Example 21 - Error Recovery Pipeline

**Goal:** Demonstrate self-healing workflows: on failure, delegate diagnosis to one agent, fix via another, then retry original tool/agent.

## Steps
1) Attempt main operation via tool/agent.
2) On failure, delegate to diagnostic agent to produce fix steps.
3) Apply fix via remediation tool/agent.
4) Retry original operation; log outcome.

## How to Run
```bash
cd examples/21-error-recovery
python ../../scripts/dev_agents.py  # start local agents
# set AGENTS_CONFIG=agents.yaml  # optional if not in CWD
python workflow.py
```

## Files
- `workflow.py` - Main flow with retry and remediation
- `agents.yaml` - Diagnostic/remediation agents
- `requirements.txt` - Extra deps (if any)
- `test_example.py` - Smoke test placeholder

## Concepts Shown
- Error handling with retries
- Agent-assisted diagnosis and remediation
- Idempotency-friendly retries
- Monitoring/logging hooks for failures

## Expected Output
- Initial failure log
- Diagnostic suggestions
- Remediation attempt
- Success on retry (or clear failure report)
