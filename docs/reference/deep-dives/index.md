# Deep Dives

Architecture and operational deep dives for planners, search, caching, analytics, and migration.

- [Two-Model Architecture](two-model-architecture.md) — Large-planner + small-executor split and cost model.
- [Workflow Architecture](workflow-architecture.md) — DAG execution, dispatch, retries, and safety rails.
- [Registry Discovery](registry-discovery.md) — Tool registry shape, discovery paths, and search integration.
- [Search Tuning](search-tuning.md) — BM25 + embeddings hybrid, thresholds, and ranking knobs.
- [Prompt Caching](prompt-caching.md) — Layered caching and provider behaviors (Anthropic/OpenAI).
- [Analytics Guide](analytics-guide.md) — Metrics backends, schema, and when to pick Prometheus/OTLP/SQLite.
- [Skill Library](skill-library.md) — Managing reusable skills and catalog hygiene.
- [Small Model Improvements](small-model-improvements.md) — Using lightweight models for execution and cost savings.
 - [Hybrid Model Routing](hybrid-model-routing.md) — Route tasks across small and large models with thresholds and fallbacks.
 - [Control Flow Patterns](control-flow-patterns.md) — Sequence/branch/map-reduce, retries, and circuit breakers.
 - [Agent Delegation](agent-delegation.md) — Hand off tasks across specialized agents with A2A.
 - [Multi-Agent Coordination](multi-agent-coordination.md) — Fan-out/fan-in with quotas, idempotency, and aggregation.
 - [Error Recovery](error-recovery.md) — Classify failures, backoff retries, and compensating actions.
 - [Skills Packaging & Reuse](skills-packaging.md) — Versioned tool reuse via the skill library.
 - [Plugin Extension](plugin-extension.md) — Extend ToolWeaver at runtime with plugins.
 - [Idempotency & Retry](idempotency-retry.md) — Guardrails for parallel dispatch and safe retries.
 - [REST API Usage](rest-api-usage.md) — Call tools over HTTP from external clients.
