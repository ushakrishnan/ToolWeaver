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
- **get_skill()**: Checks Redis first (~1ms), falls back to disk (~5-10ms)
- **Graceful degradation**: Works without Redis (disk-only mode)

No code changes needed - just set `REDIS_URL` to enable caching.

## Qdrant Search (✅ Implemented)

**Status**: Automatic opt-in when `QDRANT_URL` is set.

The skill library now supports semantic search via Qdrant:
- **save_skill()**: Automatically indexes in Qdrant if available
- **search_skills(query, top_k)**: Vector search or keyword fallback
- **Auto-collection**: Creates `toolweaver_skills` collection if missing
- **Graceful degradation**: Falls back to keyword search if Qdrant unavailable

Example:
```python
from orchestrator.execution import search_skills

# Semantic search (uses Qdrant if available, keyword match otherwise)
results = search_skills("validate email format", top_k=5)
for skill, score in results:
    print(f"{skill.name}: {score:.2f}")
```

## Usage Pattern

```python
from orchestrator.execution import save_skill, search_skills, get_skill

# 1) Save skill → automatically uses Redis cache + Qdrant index if available
skill = save_skill(
    name="validate_email",
    code="def validate(email): ...",
    description="Validates email format",
    tags=["validation", "string"]
)

# 2) Search skills → vector search (Qdrant) or keyword fallback
results = search_skills("email validation", top_k=5)
for skill, score in results:
    print(f"{skill.name}: {score:.2f}")

# 3) Retrieve skill → checks Redis cache first, then disk
skill = get_skill("validate_email")
print(skill.code_path)
```

Notes:
- **Zero configuration**: Works disk-only without Redis/Qdrant
- **Automatic opt-in**: Set `REDIS_URL` and/or `QDRANT_URL` to enable features
- **Graceful degradation**: Each feature degrades independently if unavailable
- **Embedding model**: `all-MiniLM-L6-v2` (384-dim) downloaded on first use

## Operational Tips
- Use short Redis TTLs to minimize stale entries during development
- Periodically compact Qdrant collection if you churn many skills
- For CI, skip Redis/Qdrant by unsetting env vars

## Next Steps
- Add `search_skills()` implementation using `set_vector_index()`
- Add `execute_skill()` entrypoint in Orchestrator to run saved tool/agent workflows
- Add Git integration for approved skills (promote from disk to repo)
