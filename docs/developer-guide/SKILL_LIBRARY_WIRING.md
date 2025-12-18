# Skill Library Wiring (Redis + Qdrant)

This guide shows how to wire the Skill Library MVP to Redis (cache) and Qdrant (semantic search) in a minimal, opt-in way.

## Prerequisites
- Python deps installed from repo (`pip install -e .`)
- Redis running locally (default: `localhost:6379`) - **Optional**
- Qdrant running locally (default: `localhost:6333`) - **Optional**

## Environment

Windows PowerShell:

```powershell
# Redis (optional, enables hot skill caching)
$env:REDIS_URL = "redis://localhost:6379/0"

# Qdrant (optional, enables semantic search - not yet implemented)
$env:QDRANT_URL = "http://localhost:6333"
$env:QDRANT_COLLECTION = "toolweaver-skills"
```

## Redis Cache (✅ Implemented)

**Status**: Automatic opt-in when `REDIS_URL` is set.

The skill library now automatically uses Redis for caching if available:
- **save_skill()**: Writes to disk + Redis cache (7-day TTL)
- **get_skill()**: Checks Redis first, falls back to disk
- **Graceful degradation**: Works without Redis (disk-only mode)

No code changes needed - just set `REDIS_URL` to enable caching.

## Minimal Wiring Pattern

```python
# wiring_example.py (conceptual pattern)
from orchestrator.execution import skill_library as sl
from orchestrator.vector_search import QdrantSkillIndex  # hypothetical thin wrapper
from orchestrator.redis_cache import RedisClient          # existing utility

# 1) Initialize caches/indexes (use env vars for config)
redis = RedisClient.from_env()            # if missing, returns None
skill_index = QdrantSkillIndex.from_env() # if missing, returns None

# 2) Wire into library (MVP uses disk; add these if present)
sl.set_cache(redis)           # cache lookups for hot skills
sl.set_vector_index(skill_index)  # power search_skills() with vectors

# 3) Save skill → caches + disk + vector index
ref = sl.save_skill(name="top_k", code="...", metadata={"tags": ["utility"]})

# 4) Search
for r in sl.search_skills("sorting top k integers"):
    print(r.name, r.score)
```

Notes:
- Keep this optional: if Redis/Qdrant are not set, the library still works with disk-only.
- Qdrant index schema: `id`, `name`, `tags`, embedding vector of the skill/code summary.
- Embedding: Use your existing model provider or a lightweight local embedder.

## Operational Tips
- Use short Redis TTLs to minimize stale entries during development
- Periodically compact Qdrant collection if you churn many skills
- For CI, skip Redis/Qdrant by unsetting env vars

## Next Steps
- Add `search_skills()` implementation using `set_vector_index()`
- Add `execute_skill()` entrypoint in Orchestrator to run saved tool/agent workflows
- Add Git integration for approved skills (promote from disk to repo)
