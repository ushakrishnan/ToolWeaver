# Troubleshooting

Quick fixes for common issues (local/dev friendly).

## Timeouts
- Increase per-call timeout via env (example): `TW_REQUEST_TIMEOUT=60`
- For long tools, use patterns with polling/backoff from the workflow library
- Validate network/dns; prefer localhost for dev agents/tools

## Streaming Tuning
- Disable streaming during tests to simplify assertions
- Enable streaming in examples by passing `stream=True` to `execute_agent_step`
- If terminals lag, reduce token rate/latency in model config

## Cost Controls
- Use small models by default; upgrade per-step where needed
- Enable prompt caching (see docs/reference/PROMPT_CACHING.md)
- Log token usage via monitoring backend and review hot paths

## Local Dev Agents
- Start the dev agent server: `python scripts/dev_agents.py`
- Point to local agents: `AGENTS_CONFIG=agents.yaml` under each example
- If requests fail, confirm port (default 8089) and endpoints

## Tool Discovery/Registry
- Keep `MCP_REGISTRY_URL` unset if you don’t need external tools
- When using registry, validate JSON schema and names don’t collide

## Redis/Qdrant Optionality
- Unset `REDIS_URL` and `QDRANT_URL` to run disk-only
- If enabled, verify services are reachable before running tests

## Windows Notes
- Use PowerShell env syntax: `$env:NAME = "value"`
- Avoid paths with spaces or quote them explicitly
