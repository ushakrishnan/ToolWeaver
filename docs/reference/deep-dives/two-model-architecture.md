# Two-Model Architecture

## Simple Explanation
Use the big model to decide, and the small models/tools to do. One smart plan, many cheap steps.

## Technical Explanation
Planner (GPT-4o/Claude) generates a DAG once. Executors (Phi-3/Llama, MCP/tools/sandboxed code) run steps with retries/fallbacks and caching. Hybrid search narrows tools; guardrails keep cost, time, and failures controlled.

ToolWeaver separates planning (large models) from execution (small models) to cut cost and latency.

- Planner: GPT-4o/Claude turn user intent into structured plans (1 call/request).
- Executors: Phi-3/Llama or deterministic tools perform parsing, routing, and enrichment (many cheap calls).
- Cost impact: Up to 80–90% savings possible vs all-large-model by pushing repetitive work to small models + caching (varies by task complexity mix).
- Safety: planners see only necessary context; executors run in sandbox/process isolation.

Execution flow
1) Plan: large model generates DAG with tool calls.
2) Search: registry search narrows tools (BM25 + embeddings).
3) Execute: small models/tools run steps; retries/fallbacks applied.
4) Aggregate: results merged; planner re-engaged only if needed.

When to use
- Workloads with many atomic steps (extraction, classification, routing).
- Cost-sensitive pipelines needing predictable spend.

Pitfalls / tips
- Keep tool schemas tight to reduce planner token use.
- Use caching (prompt/query/embedding) to avoid re-planning on similar inputs.
- Prefer deterministic tools where possible; use small models for light reasoning, not heavy synthesis.
