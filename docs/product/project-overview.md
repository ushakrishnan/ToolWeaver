# Project Overview

## Simple Explanation
Two teammates:
- Smart Planner (expensive) figures out the plan
- Fast Worker (efficient) executes safe, small steps

ToolWeaver helps the Planner find the right tools and runs many cheap steps in parallel with guardrails. Result: smart planning with fast, low-cost execution.

## Technical Explanation
Large model plans once (GPT-4o/Claude). Small models and tools (Phi-3/Llama, APIs, sandboxed code) execute many steps. ToolWeaver provides:
- Registry & discovery (decorators/templates/YAML + hybrid search)
- Parallel dispatcher with limits (cost, time, failures, concurrency)
- Sandboxed execution (restricted builtins; timeouts)
- Multi-layer caching & idempotency
- Observability (metrics/logging)

## Architecture at a Glance
```
Natural Language → Large Model (Planning) → Tool Search → Workflow Execution
                   1 call           Narrow K tools      Parallel nodes
                            ↓
     MCP Workers   Function Calls   Sandboxed Code
            ↓            ↓                ↓
     Small Models (Phi-3/Llama) — many cheap calls
```

## Why It Matters
- Ship faster: remove boilerplate for limits, logging, caching
- Scale safely: guardrails prevent runaway cost/fan-out
- Stay flexible: decorators, templates, or YAML

## Quickstart
- Install: `pip install toolweaver`
- Define a tool and run a parallel demo: see [Get Started / Quickstart](../get-started/quickstart.md)

## Package Extras (what/when/why)
- `redis`: distributed cache — shared, faster than file cache
- `vector`: Qdrant + client — semantic tool search at scale
- `monitoring`: Prometheus/OTLP/Grafana — production observability
- `all`: everything above — one-shot setup

See details: [Get Started / Installation](../get-started/installation.md)
