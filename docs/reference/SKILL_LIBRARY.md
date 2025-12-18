# Skill Library (MVP)

A lightweight local library for saving and reusing generated code "skills" (snippets/modules) across runs and projects.

- Location: Windows → %USERPROFILE%\.toolweaver\skills
- Manifest: skills.json (tracks name, version, path, metadata)
- Code files: Stored under the same directory by unique identifier

## Why use it?
- Reuse high‑quality generated snippets without re‑prompting
- Create a growing local "toolbox" for common tasks
- Enable programmatic retrieval and composition in workflows

## Quick Start

1) Save a skill

```python
from orchestrator.execution import skill_library as sl

code = """
from typing import List

def top_k(items: List[int], k: int) -> List[int]:
    return sorted(items, reverse=True)[:k]
"""

ref = sl.save_skill(
    name="top_k",
    code=code,
    metadata={"language": "python", "tags": ["utility", "sorting"]},
)
print("Saved:", ref)
```

2) List skills

```python
from orchestrator.execution import skill_library as sl

for s in sl.list_skills():
    print(s.name, s.version, s.path)
```

3) Load skill code

```python
from orchestrator.execution import skill_library as sl

content = sl.get_skill_code("top_k")
exec(content, globals())
print(top_k([1,5,2,9], 2))  # -> [9, 5]
```

4) Search skills (placeholder)

```python
# Planned API; backed by Qdrant vector search when enabled
from orchestrator.execution import skill_library as sl

results = sl.search_skills("sorting top k integers")  # returns lightweight matches
for r in results:
    print(r.name, r.score)
```

## Conventions
- Names are unique; `save_skill()` auto-increments a semantic-ish version (0.0.x)
- `metadata` is free-form (e.g., tags, origin, eval metrics)
- The library validates basic syntax on save (AST parse for Python)

## Good Practices
- Keep skills small and single-purpose
- Add tags in `metadata` (e.g., domain, IO types)
- Store examples/tests in `metadata` for future validation

## Roadmap (future work)
- Version pinning, rollback, and diff
- Ratings, usage metrics, and pruning
- Composition graphs and dependency metadata
- Optional remote sync/backup
 - Qdrant-backed `search_skills()` with semantic embedding

## Source
Implementation: orchestrator/execution/skill_library.py

---

## Architecture Alignment

This MVP aligns with the approved storage decision described in [docs/architecture/skill-storage-decision.md](../architecture/skill-storage-decision.md):

- Storage layers: Memory → Redis (7‑day TTL) → Disk (permanent) → Qdrant (semantic search) → Git (optional version control)
- Write path: Save → Memory (instant), Redis (async), Disk (async), Qdrant (background)
- Read path: Memory → Redis → Disk fallback

Current implementation focuses on the Disk layer for simplicity. The following enhancements will bring the MVP to the full design:

- Redis cache for hot skills and fast lookups
- Qdrant vectors for `search_skills()` by semantic similarity
- Git integration for approved versioned skills

## Planned Integrations

- Orchestrator: `execute_skill()` to run saved tool/agent workflows
- Auto-capture: Optionally save successful generated code as skills
- Composition: Allow skills to call other skills with dependency metadata
- Governance: RBAC and approvals for promoting skills to Git
- Metrics: Success rate, latency, usage counts per skill

## Related Documents

- Architecture decision: [Skill Storage Architecture Decision](../architecture/skill-storage-decision.md)
- Internal: Phase plan and roadmap (docs/internal/NEXT_STEPS.md)
- Internal: Anthropic comparison and gaps (docs/internal/ANTHROPIC_MCP_COMPARISON.md)
- Internal: A2A integration plan (docs/internal/A2A_INTEGRATION_PLAN.md)
