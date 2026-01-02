# Samples Index

Run these curated samples to see core features in action.

## Prerequisites
- Users: `pip install toolweaver`
- If a sample has its own requirements file (e.g., REST client): `pip install -r samples/<sample>/requirements.txt`
- Contributors (optional): `pip install -e .` to test against local source

**Setup Help:**
- **All Platforms:** [CROSS_PLATFORM_SETUP.md](../../samples/CROSS_PLATFORM_SETUP.md) — Windows, macOS, Linux setup guides
- **Environment Config:** [ENV_CONFIGURATION.md](../../samples/ENV_CONFIGURATION.md) — Complete reference for API keys and settings
- **Verification:** Run `python samples/verify_cross_platform.py` to test your setup

Note: `samples/` are the maintained, runnable demos. `examples/` contains older/extended scenarios—start with `samples/` unless you need legacy material.

- Parallel Agents: [samples/25-parallel-agents/parallel_deep_dive.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/25-parallel-agents/parallel_deep_dive.py)
- Caching Deep Dive: [samples/07-caching-optimization/caching_deep_dive.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/07-caching-optimization/caching_deep_dive.py)
- Sandbox Execution: [samples/09-code-execution/code_execution_demo.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/09-code-execution/code_execution_demo.py)
- Adding Tools (3 ways): [samples/23-adding-new-tools/three_ways.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/23-adding-new-tools/three_ways.py)
- GitHub Operations: [samples/03-github-operations/github_ops.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/03-github-operations/github_ops.py)
- Testing all samples: [Testing guide](testing.md)

Additional deep dives:
- Skills Packaging & Reuse: [samples/30-skills-packaging/skills_demo.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/30-skills-packaging/skills_demo.py)
- Plugin Extension: [samples/31-plugin-extension/plugin_demo.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/31-plugin-extension/plugin_demo.py)
- Idempotency & Retry (Dispatch): [samples/32-idempotency-retry/idempotency_retry_demo.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/32-idempotency-retry/idempotency_retry_demo.py)
- REST API Usage (client): [samples/29-rest-api-usage/rest_client_demo.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/29-rest-api-usage/rest_client_demo.py)
