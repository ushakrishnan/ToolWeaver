# Architecture (Overview)

Phase 0 isolates public API vs internal implementation:
- `orchestrator/` exports public surfaces only.
- `orchestrator/_internal/` holds implementation details (subject to change).
- Plugins extend via `orchestrator.plugins` without modifying core.

Later phases (1-3) add templates, decorators, YAML loader, and discovery APIs on top of this foundation.
