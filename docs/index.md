# ToolWeaver

Secure tool orchestration for AI—parallel agents, caching, and sandboxed execution with built-in guardrails.

## Simple Explanation
Plan once with a large model, then execute many small, safe steps. ToolWeaver finds the right tools and runs them in parallel with limits and caching, so you get fast results without runaway cost.

## Technical Explanation
Planner outputs a DAG; the orchestrator discovers tools, narrows via hybrid search (BM25 + embeddings), dispatches steps concurrently with semaphores and guardrails, retries/fallbacks on errors, aggregates outputs, and records metrics. Code runs in a sandbox with restricted builtins and timeouts.

## The Product Pitch
- Problem: Orchestrating many tools/models safely is hard—costs, concurrency, safety, and consistency.
- Solution: ToolWeaver provides secure fan-out, discovery, safe execution, and performance primitives.
- Value: Ship faster, scale safely, stay flexible with decorators/templates/YAML.

## Get Started
- Quickstart: [Get Started / Quickstart](get-started/quickstart.md) — install, define your first tool, and run a parallel demo.
- Why ToolWeaver: [Product / Why ToolWeaver](product/why-toolweaver.md) — the problem, our approach, and value for production teams.
- Use Cases: [Product / Use Cases](product/use-cases.md) — batch processing, ensemble voting, discovery, safety, and cost control.

### 10-Minute Quickstart
!!! success "Your first tool and parallel run"
	1. Install: `pip install toolweaver` (add `[openai]`, `[azure]`, or `[anthropic]` for LLM providers)
	2. Define a tool:
	   ```python
	   from orchestrator import mcp_tool
	   @mcp_tool(domain="demo", description="Echo a message")
	   async def echo(message: str) -> dict:
	       """Echo back the provided message."""
	       return {"echo": message}
	   ```
	3. Run a parallel demo:
	   ```bash
	   python samples/25-parallel-agents/parallel_deep_dive.py
	   ```

## Learn
- Overview: [Concepts / Overview](concepts/overview.md) — core ideas: tools, discovery, sandbox, parallel dispatch, caching.
- How it works: [Product / How It Works](product/how-it-works.md) — end-to-end architecture with dispatch, aggregation, and caching.
- Security: [Product / Security & Safety](product/security.md) — redaction, sanitization, sandboxing, quotas, and idempotency.
- Performance: [Product / Performance & Cost](product/performance.md) — caching strategy, circuit breakers, and speedups.

## Build
- Python API: [Reference / Python API](reference/api-python/overview.md) — decorators, templates, loaders, discovery, plugins, config, logging, A2A.
- REST API: [Reference / API (REST) / Overview](reference/api-rest/overview.md) — list/get/execute endpoints for exposing tools over HTTP.
- Tutorials: [Sandbox Execution](tutorials/sandbox-execution.md) — safe code runs; [Caching Deep Dive](tutorials/caching-deep-dive.md) — TTL + fallback; [Parallel Agents](tutorials/parallel-agents.md) — fan-out with guardrails.
- Samples: [Samples Index](samples/index.md) — curated runnable demos to see real behavior quickly.

## Preview Locally
```bash
pip install mkdocs-material
mkdocs serve
```
