# Installation

## Requirements
- Python 3.10+
- Optional: Redis for distributed cache (fallback file cache included)

## Install from PyPI
```bash
pip install toolweaver
```

## Optional extras (choose what you need)
Use extras to pull in integrations without bloating installs.

| Extra | Includes | When to use | Why |
|-------|----------|-------------|-----|
| `toolweaver[redis]` | redis client deps | You have Redis for distributed cache | Faster shared caching vs file cache |
| `toolweaver[vector]` | Qdrant/client deps | You use semantic search/vector DB | Better tool retrieval at scale |
| `toolweaver[monitoring]` | prometheus/otlp/grafana deps | You need metrics/export | Observability for prod |
| `toolweaver[all]` | All above | You want everything preinstalled | One-shot setup |

Env hints
- Redis: `REDIS_URL=redis://...` (or `rediss://` for TLS)
- Vector/Qdrant: `QDRANT_URL=...`, `QDRANT_API_KEY=...`
- Metrics: `ANALYTICS_BACKEND=prometheus|otlp|sqlite`, plus backend-specific envs

## Verify
```bash
python - <<"PY"
from orchestrator import get_available_tools
print("Tools loaded:", len(get_available_tools()))
PY
```
