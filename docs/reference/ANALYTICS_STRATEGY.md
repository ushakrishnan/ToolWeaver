# Analytics Strategy: W&B vs Prometheus/Grafana

## Overview

ToolWeaver supports **three complementary analytics backends**, each serving different purposes in the observability stack:

1. **Weights & Biases (W&B)** - Experiment tracking & ML monitoring
2. **Prometheus/Grafana** - Real-time metrics & alerting
3. **SQLite** - Local development & self-hosted deployments

These are **ADDITIVE, NOT REPLACEMENTS** - they serve different use cases and can work together.

---

## Comparative Analysis

| Feature | W&B | Prometheus | SQLite |
|---------|-----|-----------|--------|
| **Purpose** | Experiment tracking, ML monitoring, logging | Real-time metrics, alerting, dashboards | Local storage, self-hosted |
| **Data Type** | Experiments, hyperparameters, artifacts, logs | Time-series metrics only | SQL queries |
| **Retention** | 1 year (free tier) | Configurable (default 15 days) | Unlimited |
| **Scale** | Managed cloud | Self-hosted/managed | Single machine |
| **Cost** | Free tier 100 projects | Free (self-hosted) or paid (SaaS) | Free |
| **Real-time** | Yes (dashboards) | Yes (scraping every 15-60s) | Not applicable |
| **Alerting** | ✓ | ✓ | ✗ |
| **Artifact Storage** | ✓ (Models, data, plots) | ✗ | ✗ |
| **Experiment Replay** | ✓ Full reproducibility | ✗ | ✗ |
| **Integration** | Runs, artifacts, config | Metrics only | Direct SQL |

---

## When to Use Each Backend

### **Weights & Biases (W&B)** - Use When:

✅ **Experiment Tracking**
- You want to compare different skill/model configurations
- You need full experiment reproducibility
- You want to version hyperparameters and artifacts

✅ **ML Model Monitoring**
- Tracking model performance over time
- A/B testing different models
- Version control for production models

✅ **Data & Artifacts**
- Logging training data samples
- Storing model checkpoints
- Tracking output artifacts

```python
# Example: W&B is great for this
import wandb

wandb.init(project="toolweaver", name="skill_v2")
wandb.config.update({
    "skill_version": "2.0",
    "model": "gpt-4",
    "strategy": "semantic_search"
})
wandb.log({"skill_rating": 4.8, "latency_ms": 145})
wandb.save("model_checkpoint.pkl")
```

### **Prometheus/Grafana** - Use When:

✅ **Real-time Monitoring**
- Skill success rates need real-time alerts
- Health scores drop below threshold
- Latency anomalies detected

✅ **Production Dashboards**
- Team-wide visibility of system health
- Historical trend analysis (30 days+)
- Cross-service metric correlation

✅ **Multi-environment Setup**
- Multiple deployments (dev/staging/prod)
- Centralized monitoring stack
- Cost-sensitive (open source)

```python
# Example: Prometheus is great for this
from orchestrator.execution.analytics import create_analytics_client

client = create_analytics_client(backend='prometheus')
# Auto-exposed at http://localhost:8000/metrics
# Scraped by Prometheus every 30s
# Visualized in Grafana dashboards
# Alerts triggered on anomalies
```

### **SQLite** - Use When:

✅ **Local Development**
- Building/testing new skills
- No external dependencies needed
- Quick iteration cycles

✅ **Self-Hosted Deployments**
- Air-gapped environments
- Single-machine deployments
- Long-term local analytics

```python
# Example: SQLite is great for this
from orchestrator.execution.analytics import create_analytics_client

client = create_analytics_client(backend='sqlite')
# All data stored locally
# Query directly via SQL
# Lightweight, no setup required
```

---

## Architecture Decision: Why Have All Three?

### Use Case Scenario

**Development Environment:**
```
Local Dev Machine
├── SQLite backend (local storage, fast iteration)
└── Skill test cycles
```

**Staging Environment:**
```
Staging Server
├── Prometheus backend (monitoring practice)
├── Grafana dashboards (team visibility)
└── Alert testing
```

**Production Environment:**
```
Production Cluster
├── Prometheus + Grafana (real-time ops monitoring)
├── W&B (experiment tracking, model versioning)
└── Historical analysis & reproducibility
```

### Key Insight: Different Concerns

| Concern | Best Tool |
|---------|-----------|
| "Is the system running well right now?" | **Prometheus** (real-time metrics) |
| "Which skill version performed best?" | **W&B** (experiment comparison) |
| "Why did latency spike yesterday?" | **Prometheus** (historical data) |
| "What was the exact config for production v3?" | **W&B** (config versioning) |
| "What's the local analytics without internet?" | **SQLite** (offline mode) |

---

## Recommended Deployments

### 1. **Startup / MVP** (Minimal)
```env
ANALYTICS_BACKEND=sqlite
# Cost: Free
# Setup: Zero
# Suitable for: Single developer
```

### 2. **Team Development** (Recommended)
```env
# Development environment
ANALYTICS_BACKEND=sqlite

# Production/Staging environment
ANALYTICS_BACKEND=prometheus
PROMETHEUS_PORT=8000

# Plus optional W&B for ML tracking
WANDB_API_KEY=your-key
```

### 3. **Enterprise Production** (Full Stack)
```env
ANALYTICS_BACKEND=prometheus          # Real-time ops monitoring
PROMETHEUS_PORT=8000
PROMETHEUS_HOST=0.0.0.0

# Plus separate services:
- Prometheus server (scrapes /metrics endpoint)
- Grafana instance (visualizes Prometheus metrics)
- W&B integration (experiment tracking)
```

---

## Combining W&B + Prometheus

You can use BOTH simultaneously for maximum observability:

```python
from orchestrator.execution.analytics import create_analytics_client

# Real-time monitoring
metrics = create_analytics_client(backend='prometheus')

# Experiment tracking (separate)
import wandb
run = wandb.init(project="toolweaver")

# Log to both systems
def record_skill_evaluation(skill_id, success, latency_ms):
    # Real-time metric
    metrics.record_skill_execution(
        skill_id=skill_id,
        success=success,
        latency_ms=latency_ms
    )
    
    # Experiment tracking
    wandb.log({
        "skill": skill_id,
        "success": success,
        "latency": latency_ms
    })

# Results:
# - Prometheus shows "Skill_X success rate: 94.2%" in real-time
# - W&B shows "Skill_X v2 vs v1 comparison" in experiment history
```

---

## Migration Path

### Start with SQLite:
```bash
pip install toolweaver
export ANALYTICS_BACKEND=sqlite
# Local development, no external dependencies
```

### Add Prometheus for team:
```bash
pip install toolweaver[prometheus]
export ANALYTICS_BACKEND=prometheus
# Team dashboards, real-time monitoring
```

### Add W&B for experiments:
```bash
pip install toolweaver[monitoring]
# Now have both Prometheus metrics AND W&B experiment tracking
export ANALYTICS_BACKEND=prometheus
export WANDB_API_KEY=your-key
```

---

## Configuration Files

### `.env.example` - All Options

```env
# ============================================================
# ANALYTICS BACKEND SELECTION
# ============================================================
# Choose: sqlite | prometheus | otlp
# (OTLP is Grafana Cloud alternative to Prometheus)
ANALYTICS_BACKEND=prometheus

# ============================================================
# SQLITE CONFIGURATION (Local Storage)
# ============================================================
ANALYTICS_DB_PATH=~/.toolweaver/analytics.db
ANALYTICS_DB_RETENTION_DAYS=90

# ============================================================
# PROMETHEUS CONFIGURATION (Real-time Metrics)
# ============================================================
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=8000
PROMETHEUS_HOST=0.0.0.0
# Access metrics at: http://localhost:8000/metrics

# ============================================================
# OTLP CONFIGURATION (Grafana Cloud Alternative)
# ============================================================
# Optional: Use instead of local Prometheus
OTLP_ENDPOINT=https://otlp-gateway-prod-us-east-2.grafana.net/otlp
OTLP_INSTANCE_ID=1472140
OTLP_TOKEN=glc_...
OTLP_PUSH_INTERVAL=60

# ============================================================
# WEIGHTS & BIASES CONFIGURATION (Experiment Tracking)
# ============================================================
# Optional: For ML experiment tracking (separate from analytics backend)
WANDB_API_KEY=your-wandb-api-key
WANDB_PROJECT=toolweaver
WANDB_ENTITY=your-username
```

---

## Cost Comparison

| Backend | Startup | Monthly | Year 1 |
|---------|---------|---------|--------|
| **SQLite** | $0 | $0 | $0 |
| **Prometheus (self-hosted)** | $10 | $15 | $190 |
| **Grafana (self-hosted)** | $0 | $0 | $0 |
| **W&B (free tier)** | $0 | $0 | $0 |
| **W&B (pro plan)** | $0 | $99 | $1,188 |
| **OTLP + Grafana Cloud** | $0 | $29 | $348 |

**Recommendation for cost-conscious teams:**
- Development: SQLite (free)
- Production: Prometheus (self-hosted) + Grafana (free)
- Optional: W&B free tier for experiment tracking

---

## FAQ

### Q: Do I have to use all three?
**A:** No. Pick what fits your use case:
- Solo dev? → SQLite
- Team with dashboards? → Prometheus + Grafana
- ML experiments? → Add W&B
- Cloud-only? → OTLP + Grafana Cloud

### Q: Can Prometheus replace W&B?
**A:** Partially. Prometheus is great for metrics/monitoring but lacks:
- Experiment comparison
- Artifact versioning
- Config reproducibility
- Full run history

### Q: Can W&B replace Prometheus?
**A:** Not for real-time ops monitoring. W&B is experiment-focused, not built for:
- Real-time alerting
- Multi-day trending
- Team dashboards
- Production monitoring

### Q: What about Datadog/New Relic?
**A:** Could replace Prometheus for production monitoring, but:
- Much more expensive ($30-500+/month)
- Overkill for tool orchestration
- Prometheus is battle-tested, open source

### Q: Can I switch backends without code changes?
**A:** Yes! Just change `ANALYTICS_BACKEND` env var and restart:
```bash
export ANALYTICS_BACKEND=sqlite    # Local
export ANALYTICS_BACKEND=prometheus # Production
export ANALYTICS_BACKEND=otlp      # Cloud
```

---

## Next Steps

1. **Choose your backend** based on use case
2. **Install dependencies**: `pip install toolweaver[prometheus]`
3. **Set env variable**: `export ANALYTICS_BACKEND=prometheus`
4. **For dashboards**: Deploy Prometheus + Grafana
5. **For experiments**: Optional `pip install wandb`

See **ANALYTICS_BACKENDS.md** for detailed backend configuration.

---

**Last Updated:** December 18, 2025  
**Status:** ✅ Complete - All three backends implemented and tested
