# Production Deployment Guide

## Overview

This guide covers deploying ToolWeaver to production with focus on:
- Security hardening
- Performance optimization
- Monitoring and observability
- Scaling considerations
- Troubleshooting

## Prerequisites

### System Requirements

- **Python**: 3.11+ (tested on 3.13.11)
- **RAM**: Minimum 2GB (4GB recommended for embedding model)
- **Storage**: 1GB for models + cache
- **CPU**: 2+ cores recommended for parallel tool execution

### Dependencies

```bash
# Core dependencies
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

# Testing (development only)
pip install pytest>=9.0
pip install pytest-asyncio>=1.3
pip install pytest-mock>=3.15
```

## Security Hardening

### 1. Code Execution Sandbox

**AST-based validation** (already implemented in Phase 4):

```python
from orchestrator.programmatic_executor import ProgrammaticToolExecutor

executor = ProgrammaticToolExecutor(
    tool_catalog=catalog,
    mcp_client=mcp_client,
    timeout=30,  # Prevent infinite loops
    max_tool_calls=100  # Limit resource usage
)
```

**Blocked operations**:
- File system access (`open`, `os`, `pathlib`)
- Network access (`requests`, `urllib`, `socket`)
- Process spawning (`subprocess`, `os.system`)
- Code evaluation (`eval`, `exec`, `compile`)
- Dangerous builtins (`__import__`, `globals`, `locals`)

### 2. Azure AD Authentication

**Use Managed Identity** (no keys in code):

```python
from azure.identity import DefaultAzureCredential

# Managed Identity (recommended for Azure VM/App Service)
credential = DefaultAzureCredential()

# Or Workload Identity (for AKS)
credential = DefaultAzureCredential(
    exclude_managed_identity_credential=False,
    exclude_environment_credential=True
)
```

**Never use API keys** in production. Use Azure AD tokens with:
- Role-Based Access Control (RBAC)
- Managed Identity for secure credential management
- Token auto-renewal (handled by Azure SDK)

### 3. Input Validation

**Validate user inputs**:

```python
from pydantic import BaseModel, Field, validator

class UserRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    context: dict = Field(default_factory=dict)
    
    @validator('query')
    def validate_query(cls, v):
        # Block injection attempts
        dangerous_patterns = ['DROP TABLE', 'DELETE FROM', '<script>']
        for pattern in dangerous_patterns:
            if pattern.lower() in v.lower():
                raise ValueError(f"Dangerous pattern detected: {pattern}")
        return v
```

### 4. Resource Limits

**Set execution limits**:

```python
# Timeout per tool call
TOOL_TIMEOUT = 30  # seconds

# Max parallel executions
MAX_CONCURRENT_TOOLS = 10

# Rate limiting (using Redis or in-memory)
REQUESTS_PER_MINUTE = 60
REQUESTS_PER_HOUR = 1000
```

## Performance Optimization

### 1. Lazy Loading

**Load models on demand**:

```python
from orchestrator.tool_search import ToolSearchEngine

# Only initialize when needed
class LazySearchEngine:
    def __init__(self):
        self._engine = None
    
    def search(self, query, catalog, top_k=10):
        if self._engine is None:
            self._engine = ToolSearchEngine()  # ~11s load time
        return self._engine.search(query, catalog, top_k)
```

### 2. Caching Strategy

**Multi-level caching**:

```python
# Level 1: Discovery cache (24h TTL)
discovery_cache = "~/.toolweaver/discovered_tools.json"

# Level 2: Embedding cache (persistent)
embedding_cache = "~/.toolweaver/search_cache/emb_*.npy"

# Level 3: Query cache (1h TTL)
query_cache = "~/.toolweaver/search_cache/search_*.pkl"

# Level 4: LLM prompt cache (5min TTL, Anthropic)
# See docs/PROMPT_CACHING.md
```

### 3. Connection Pooling

**Reuse HTTP connections**:

```python
import aiohttp

# Global session (singleton)
_session = None

async def get_session():
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=100,  # Max connections
                limit_per_host=10
            )
        )
    return _session

# Use in planner
planner = LargePlanner(
    tool_catalog=catalog,
    session=await get_session()
)
```

### 4. Parallel Execution

**Use asyncio for tool calls**:

```python
import asyncio

async def execute_tools_parallel(tools):
    """Execute multiple tools concurrently."""
    tasks = [executor.execute(tool) for tool in tools]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

## Analytics & Monitoring Setup

### 1. Choose Your Analytics Backend

ToolWeaver supports **three analytics backends** for skill execution metrics (choose one):

```bash
# .env

# Production Recommended: Prometheus (real-time dashboards + alerting)
ANALYTICS_BACKEND=prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=8000
PROMETHEUS_HOST=0.0.0.0

# Alternative: Grafana Cloud OTLP (managed, zero infrastructure)
ANALYTICS_BACKEND=otlp
OTLP_ENDPOINT=https://otlp-gateway-prod-us-east-2.grafana.net/otlp
OTLP_INSTANCE_ID=1472140
OTLP_TOKEN=glc_...

# Development: SQLite (local storage, no external deps)
ANALYTICS_BACKEND=sqlite
ANALYTICS_DB_PATH=~/.toolweaver/analytics.db
```

**Automatic metric recording:**
```python
from orchestrator.execution.analytics import create_analytics_client

# Auto-selects backend from ANALYTICS_BACKEND env var
client = create_analytics_client()

# Metrics recorded automatically:
# - Skill execution (success/failure, latency)
# - Skill ratings (user feedback)
# - Health scores (aggregated performance)
```

See [ANALYTICS_STRATEGY.md](../reference/ANALYTICS_STRATEGY.md) for detailed comparison and when to use each.

### 2. Optional: Experiment Tracking with W&B

Separate from analytics backend. Use W&B for experiment comparison and reproducibility:

```bash
# .env
WANDB_API_KEY=your-wandb-api-key
WANDB_PROJECT=ToolWeaver
WANDB_ENTITY=your-username
WANDB_RUN_NAME=production-run-1
```

**Combine both systems:**
```python
from orchestrator.execution.analytics import create_analytics_client
import wandb

# Real-time monitoring
metrics = create_analytics_client()

# Experiment tracking
run = wandb.init(project="toolweaver")

# Log to both
metrics.record_skill_execution(skill_id="parse", success=True, latency_ms=145)
wandb.log({"skill_execution": True})
```

### 3. Legacy: Execution Logging (Deprecated)

For tool execution logging (separate from metrics, not recommended for new deployments):

```bash
# .env
MONITORING_BACKENDS=local,wandb  # Legacy option
TOOL_LOGS_DIR=.tool_logs
```

**Recommendation:** Use analytics backends for metrics instead of legacy logging.

### 2. Export Metrics

**Daily exports for analysis**:

```python
import schedule

def export_daily_metrics():
    """Export metrics at midnight."""
    timestamp = datetime.now().strftime("%Y-%m-%d")
    monitor.export_metrics(f"/metrics/toolweaver_{timestamp}.json")

# Schedule daily export
schedule.every().day.at("00:00").do(export_daily_metrics)
```

### 3. Health Checks

**Endpoint for Kubernetes/load balancer**:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "uptime": time.time() - start_time,
        "metrics": monitor.get_summary()["overview"]
    }

@app.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics."""
    summary = monitor.get_summary()
    return f"""
# HELP toolweaver_tool_calls_total Total tool calls
# TYPE toolweaver_tool_calls_total counter
toolweaver_tool_calls_total {summary['overview']['total_tool_calls']}

# HELP toolweaver_errors_total Total errors
# TYPE toolweaver_errors_total counter
toolweaver_errors_total {summary['overview']['total_errors']}

# HELP toolweaver_cache_hit_rate Cache hit rate
# TYPE toolweaver_cache_hit_rate gauge
toolweaver_cache_hit_rate {summary['overview']['cache_hit_rate']}
"""
```

## Scaling Considerations

### Horizontal Scaling

**Stateless design** (already implemented):
- No shared state between requests
- All state in Azure OpenAI (stateless LLM calls)
- Cache files on shared storage (NFS, Azure Files)

**Load balancer configuration**:
```yaml
# Example for Azure Load Balancer
apiVersion: v1
kind: Service
metadata:
  name: toolweaver
spec:
  type: LoadBalancer
  selector:
    app: toolweaver
  ports:
  - port: 80
    targetPort: 8000
  sessionAffinity: None  # No sticky sessions needed
```

### Vertical Scaling

**Resource allocation**:
```yaml
# Kubernetes pod spec
resources:
  requests:
    memory: "2Gi"  # Minimum for embedding model
    cpu: "1000m"   # 1 core
  limits:
    memory: "4Gi"  # Allow headroom for cache
    cpu: "2000m"   # 2 cores for parallel execution
```

### Cache Sharing

**Shared cache volume**:
```yaml
# Kubernetes PVC for cache sharing
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: toolweaver-cache
spec:
  accessModes:
  - ReadWriteMany  # Multiple pods can read/write
  resources:
    requests:
      storage: 5Gi
  storageClassName: azurefile  # Or NFS
```

## Deployment Patterns

### Pattern 1: Azure App Service

**Best for**: Small to medium scale (< 1000 req/min)

```bash
# Deploy to App Service
az webapp up \
  --resource-group toolweaver-rg \
  --name toolweaver-app \
  --runtime "PYTHON:3.11" \
  --sku B2  # 2 cores, 3.5GB RAM

# Enable managed identity
az webapp identity assign \
  --name toolweaver-app \
  --resource-group toolweaver-rg

# Grant Azure OpenAI access
az role assignment create \
  --assignee <managed-identity-principal-id> \
  --role "Cognitive Services OpenAI User" \
  --scope <openai-resource-id>
```

### Pattern 2: Azure Container Instances

**Best for**: Simple containerized deployment

```bash
# Build container
docker build -t toolweaver:latest .

# Push to ACR
az acr login --name myregistry
docker tag toolweaver:latest myregistry.azurecr.io/toolweaver:latest
docker push myregistry.azurecr.io/toolweaver:latest

# Deploy to ACI
az container create \
  --resource-group toolweaver-rg \
  --name toolweaver-instance \
  --image myregistry.azurecr.io/toolweaver:latest \
  --cpu 2 \
  --memory 4 \
  --assign-identity \
  --environment-variables \
    AZURE_OPENAI_ENDPOINT=https://myopenai.openai.azure.com
```

### Pattern 3: Azure Kubernetes Service (AKS)

**Best for**: High scale (> 1000 req/min), advanced orchestration

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: toolweaver
spec:
  replicas: 3
  selector:
    matchLabels:
      app: toolweaver
  template:
    metadata:
      labels:
        app: toolweaver
    spec:
      serviceAccountName: toolweaver-sa
      containers:
      - name: toolweaver
        image: myregistry.azurecr.io/toolweaver:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        env:
        - name: AZURE_OPENAI_ENDPOINT
          value: "https://myopenai.openai.azure.com"
        volumeMounts:
        - name: cache
          mountPath: /cache
      volumes:
      - name: cache
        persistentVolumeClaim:
          claimName: toolweaver-cache
```

## Troubleshooting

### Common Issues

#### 1. Embedding Model Load Timeout

**Symptom**: First request takes >60s, times out

**Solution**: Pre-warm model on startup
```python
# startup.py
from orchestrator.tool_search import ToolSearchEngine

# Load model during app startup
print("Loading embedding model...")
engine = ToolSearchEngine()
_ = engine._get_embedding_model()  # Force load
print("Model loaded successfully")
```

#### 2. Cache Permission Errors

**Symptom**: `PermissionError: [Errno 13] Permission denied: '~/.toolweaver'`

**Solution**: Set explicit cache directory with write permissions
```python
import os
os.environ['TOOLWEAVER_CACHE_DIR'] = '/tmp/toolweaver_cache'
```

#### 3. Azure AD Authentication Failures

**Symptom**: `AuthenticationError: Failed to get token`

**Solution**: Verify managed identity has correct roles
```bash
# Check identity
az webapp identity show \
  --name toolweaver-app \
  --resource-group toolweaver-rg

# Check role assignment
az role assignment list \
  --assignee <principal-id> \
  --scope <openai-resource-id>
```

#### 4. High Memory Usage

**Symptom**: Container OOMKilled, >4GB RAM used

**Solution**: Disable embedding model if not using search
```python
# Skip search for small catalogs (≤20 tools)
planner = LargePlanner(
    tool_catalog=catalog,
    use_tool_search=False  # Saves ~1.5GB RAM
)
```

### Debug Mode

**Enable verbose logging**:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Log all tool calls
logging.getLogger('orchestrator.programmatic_executor').setLevel(logging.DEBUG)
logging.getLogger('orchestrator.tool_search').setLevel(logging.DEBUG)
logging.getLogger('orchestrator.planner').setLevel(logging.DEBUG)
```

## Production Checklist

### Pre-Deployment
- [ ] All tests passing (103/103)
- [ ] Security scan completed (no vulnerabilities)
- [ ] Azure AD authentication configured
- [ ] Managed Identity assigned
- [ ] RBAC roles granted
- [ ] Resource limits set
- [ ] Health check endpoint tested
- [ ] Monitoring configured

### Post-Deployment
- [ ] Health check returns 200 OK
- [ ] Metrics endpoint accessible
- [ ] First request completes successfully
- [ ] Cache directory created
- [ ] Logs being written
- [ ] Monitoring dashboard shows data
- [ ] Error rate < 1%
- [ ] p95 latency < 2s (excluding model load)

### Ongoing
- [ ] Monitor error rates daily
- [ ] Review metrics weekly
- [ ] Update tools as needed
- [ ] Rotate logs monthly
- [ ] Update dependencies quarterly
- [ ] Review security quarterly

## Performance Targets

Based on Phase 5 implementation:

| Metric | Target | Notes |
|--------|--------|-------|
| p50 latency | < 500ms | Excluding first request |
| p95 latency | < 2s | Excluding model load |
| Error rate | < 1% | Including retries |
| Cache hit rate | > 70% | With prompt caching |
| Throughput | 100+ req/s | With 3 replicas |
| Memory per pod | < 4GB | With embedding model |

## Support

For issues or questions:
1. Check logs in `/var/log/toolweaver/` or container logs
2. Review [ARCHITECTURE.md](./ARCHITECTURE.md) for design decisions
3. Consult [PROMPT_CACHING.md](./PROMPT_CACHING.md) for optimization
4. Open issue on GitHub: https://github.com/ushakrishnan/ToolWeaver/issues

## Next Steps

1. **Deploy to staging**: Test with production-like data
2. **Load test**: Verify throughput targets
3. **Monitor for 1 week**: Collect baseline metrics
4. **Optimize**: Adjust based on real usage patterns
5. **Deploy to production**: With gradual rollout (10% → 50% → 100%)
