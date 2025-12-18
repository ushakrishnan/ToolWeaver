# Follow-up Issues (Tracking)

1) Redis cache for Skill Library
- Wire optional Redis client into skill lookups/saves
- Env: `REDIS_URL`

2) Qdrant-backed `search_skills()`
- Add vector index (name, tags, summary)
- Env: `QDRANT_URL`, `QDRANT_COLLECTION`

3) Git approval flow for skills
- Promote approved skills to Git (version control)
- Provide CLI to approve/revert

4) Orchestrator `execute_skill()` entrypoint
- Execute saved tool/agent workflows as a first-class call
- Telemetry hooks for success/latency per skill

5) Dev Docs
- Expand wiring guide with code samples
- Add end-to-end tutorial around Example 22
