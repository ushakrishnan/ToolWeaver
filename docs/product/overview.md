# ToolWeaver: Secure Tool Orchestration for AI

## Simple Explanation
Imagine two teammates:
- Smart Planner (expensive): figures out the plan
- Fast Worker (efficient): executes the steps safely

ToolWeaver helps the Planner find the right tools, then runs many small, cheap steps in parallel with safety rails. You get smart planning with fast, low-cost execution.

## Technical Explanation
Two-model architecture: large models (GPT-4o/Claude) plan once; small models/tools (Phi-3/Llama, APIs) execute many cheap steps. ToolWeaver provides a registry, search, parallel dispatcher, caching, and sandboxing so complex workflows run safely and predictably.

## The Problem
Integrating many tools and models into real workflows is hard:
- Parallel fan-out without runaway cost or failures
- Consistent schemas and discovery across heterogeneous tools
- Safe execution (no secrets leakage, no dangerous code paths)
- Performance (caching, idempotency) and observability

## The Solution
ToolWeaver is a package-first library to register, discover, and run tools and agents with built-in guardrails:
- Secure fan-out: parallel dispatch with concurrency, cost, duration, and failure-rate limits
- Safe execution: template sanitization, PII redaction, secrets-safe logging, sandboxed code
- Performance: dual-layer caching (Redis + file) and idempotency for instant retries
- Useful outputs: aggregation (majority vote, rank by metric, best result)

## Why It Matters
- Ship faster: remove boilerplate for limits, logging, caching
- Scale safely: guardrails prevent cost bombs and unstable fan-outs
- Stay flexible: decorators, templates, or YAML—mix and match

## Quickstart
- Install and run a sample in minutes: [Get Started / Quickstart](../get-started/quickstart.md)
- See parallel dispatch: [Tutorial / Parallel Agents](../tutorials/parallel-agents.md)

## Package Extras (what/when/why)
- redis: distributed cache. Use when you need shared caching; faster than file cache.
- vector: Qdrant + client deps. Use for semantic tool search at scale.
- monitoring: Prometheus/OTLP/Grafana deps. Use for production observability.
- all: everything above. Use for one-shot setup.

See install matrix: [Get Started / Installation](../get-started/installation.md)

## Learn More
- Concepts overview: [Concepts / Overview](../concepts/overview.md)
- Public API: [Reference / Python API](../reference/api-python/overview.md)
- Samples: [Samples Index](../samples/index.md)
