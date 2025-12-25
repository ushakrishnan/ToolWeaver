# Production Deployment Guide

Covers security hardening, performance, monitoring, scaling, and troubleshooting for production rollouts.

## Prerequisites
- Python: 3.11+
- RAM: 2 GB minimum (4 GB recommended if you run local embeddings)
- CPU: 2+ cores recommended for parallel tool execution
- Storage: ~1 GB for models and cache

### Dependencies (baseline)
```bash
pip install pydantic>=2.0
pip install aiohttp>=3.13
# Azure OpenAI (required)
pip install azure-identity>=1.12
pip install openai>=1.0
# Semantic search (optional but recommended)
pip install sentence-transformers>=5.0
pip install rank-bm25>=0.2
pip install torch>=2.0
pip install scikit-learn>=1.8
# Testing (dev only)
pip install pytest>=9.0
pip install pytest-asyncio>=1.3
pip install pytest-mock>=3.15
```

## Security Hardening
### Code execution sandbox
Already implemented via `ProgrammaticToolExecutor`; ensure timeouts and call limits are set.
```python
from orchestrator.programmatic_executor import ProgrammaticToolExecutor
executor = ProgrammaticToolExecutor(tool_catalog=catalog, mcp_client=mcp_client, timeout=30, max_tool_calls=100)
```
Blocked: file system, network, process spawn, eval/exec, dangerous builtins.

### Azure AD authentication
Prefer Managed Identity/Workload Identity over API keys.
```python
from azure.identity import DefaultAzureCredential
credential = DefaultAzureCredential()
```
Use RBAC and token auto-renewal; avoid embedding keys.

### Input validation
Use Pydantic models with length limits and pattern checks where needed.

### Resource limits
Set per-call timeouts, max concurrency, and rate limits (Redis or in-memory). Example: `TOOL_TIMEOUT=30`, `MAX_CONCURRENT_TOOLS=10`, `REQUESTS_PER_MINUTE=60`.

## Performance
### Lazy loading
Defer heavy inits (e.g., search engine) until first use.

### Caching
Use multi-level caching (discovery, embeddings, queries, prompt cache). Configure TTLs to balance freshness and cost.

### Connection pooling
Reuse `aiohttp` sessions with sensible connection limits when calling external services.

### Parallel execution
Use `asyncio.gather(..., return_exceptions=True)` for independent tool calls.

## Analytics & Monitoring
Choose one backend via env vars:
- Prometheus (self-hosted scraping)
- OTLP (Grafana Cloud push)
- SQLite (local dev)
```bash
ANALYTICS_BACKEND=prometheus   # or otlp or sqlite
```
Create the client via `create_analytics_client()`; metrics include success/failure/latency/ratings/health scores. Prefer Prometheus/OTLP over legacy execution logging.

Expose health/metrics endpoints for probes and scraping (FastAPI example):
```python
@app.get("/health")
async def health():
    return {"status": "healthy"}
```
Add `/metrics` when using Prometheus backend.

## Scaling
- Stateless app: keep request state out of process; share cache over NFS/Azure Files.
- Horizontal scale behind a load balancer; no sticky sessions required.
- Kubernetes resource requests: start around 1 CPU/2 GiB; allow headroom for caches.
- Shared cache PVC for embeddings/catalog if using file cache.

## Deployment patterns
- Containers + Kubernetes (preferred): add liveness/readiness probes; mount cache volume if needed; configure secrets via K8s secrets/Key Vault.
- Azure App Service/Container Apps: ensure Managed Identity enabled for Azure OpenAI; configure env vars for Redis/Qdrant.

## Troubleshooting quick checks
- Health: hit `/health`
- Metrics: `/metrics` when Prometheus enabled
- Cache status: Redis/Qdrant reachable? fall back behaviors enabled?
- Timeouts: confirm per-tool timeout and global request timeouts
- Credentials: prefer Managed Identity; if keys, verify env vars loaded
