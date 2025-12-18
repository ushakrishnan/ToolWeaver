# Example 22 - End-to-End Showcase (Tools + Agents + Skills)

End-to-end flow combining tools, agents, and the skill library:
1) Fetch data via tool
2) Analyze via agent (streaming optional)
3) Solidify a helper as a reusable skill
4) Reuse the skill on a second input
5) Store results via tool

## How to Run
```bash
cd examples/22-end-to-end-showcase
python ../../scripts/dev_agents.py  # start local agents
# set AGENTS_CONFIG=agents.yaml  # optional if not in CWD
python workflow.py
```

## Files
- workflow.py - Main flow
- agents.yaml - Local dev agent endpoints
- test_example.py - Smoke test using monkeypatch

## What It Shows
- Unified discovery (tools + agents)
- `execute_tool` and `execute_agent_step`
- Saving and reusing a code skill (MVP)
- Deterministic tool steps wrapped around agent reasoning
