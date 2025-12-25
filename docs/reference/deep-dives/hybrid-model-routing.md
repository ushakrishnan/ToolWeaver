# Hybrid Model Routing

## Simple Explanation
Use multiple models together: fast, cheap models for easy tasks and bigger models for hard cases. Route requests based on confidence, cost, or explicit rules, and add fallbacks when the first choice fails.

## Technical Explanation
Implement a router that scores tasks by complexity/uncertainty (e.g., heuristics or LLM self-estimates) and selects a model backend accordingly. Combine thresholds, guardrails, and retries with fallback escalation. Log decisions and outcomes to tune thresholds over time.

**When to use**
- Large volume with mixed difficulty and tight latency/cost budgets
- Quality-sensitive paths needing escalation to stronger models

**Key Primitives**
- Scoring/thresholds: difficulty, confidence, domain tags
- Backends: small vs large model clients
- Fallbacks & retries: escalate on low confidence or errors
- Observability: decision logs and success metrics

**Try it**
- Run the sample: [samples/08-hybrid-model-routing/hybrid_routing_demo.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/08-hybrid-model-routing/hybrid_routing_demo.py)
- See the README: [samples/08-hybrid-model-routing/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/08-hybrid-model-routing/README.md)

**Gotchas**
- Avoid flapping by adding hysteresis and minimum confidence deltas
- Capture routing features so you can reproduce and debug decisions
- Guard against runaway retries; cap attempts and escalate deterministically
