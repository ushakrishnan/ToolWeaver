# Follow-up Issues (Tracking)

## Done ✅
- [x] Code validation module (syntax, exec, mypy) with docs
- [x] execute_skill() API in Orchestrator with guide

## Next (Phase 3 Enhancements)

1) Redis cache for Skill Library
- Wire optional Redis client into skill lookups/saves
- Env: `REDIS_URL`
- Estimated: 2-3 hours

2) Qdrant-backed `search_skills()`
- Add vector embedding for skill code/tags
- Integrate with discovery for progressive disclosure
- Env: `QDRANT_URL`, `QDRANT_COLLECTION`
- Estimated: 3-4 hours

3) Git approval flow for skills
- CLI to promote approved skills to Git repo
- Version control + audit trail
- Integrate with validation gates
- Estimated: 2-3 hours

4) Skill composition and dependency tracking
- Detect skills calling other skills
- Build dependency graphs
- Warn on circular dependencies
- Estimated: 2-3 hours

5) Skill metrics and ratings
- Track usage count, success rate, latency per skill
- Allow user ratings/feedback
- Surface hot/cold skills for cleanup
- Estimated: 2-3 hours
