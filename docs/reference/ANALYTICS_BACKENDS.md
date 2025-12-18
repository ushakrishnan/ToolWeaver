# Phase 5 Analytics: Quick Comparison

## SQLite vs OTLP Backend

| Feature | SQLite | OTLP (Grafana Cloud) |
|---------|--------|---------------------|
| **Setup Time** | 5 minutes | 10 minutes |
| **Storage** | Local file (~/.toolweaver/analytics.db) | Cloud (Grafana manages) |
| **Dependencies** | None (built-in) | opentelemetry-* packages |
| **Cost** | Free | Free (10k series) |
| **Retention** | Manual (RETENTION_DAYS) | Automatic (14 days) |
| **Backup** | Manual file copy | Managed by Grafana |
| **Multi-server** | No | Yes |
| **Internet** | Not required | Required |
| **Best for** | Dev, single-server | Production, cloud |

## Usage Examples

### SQLite Backend

```python
# .env
ANALYTICS_BACKEND=sqlite
ANALYTICS_DB_PATH=~/.toolweaver/analytics.db
ANALYTICS_DB_RETENTION_DAYS=365

# Code
from orchestrator.execution.analytics import SkillAnalytics

analytics = SkillAnalytics()
analytics.record_skill_usage("my-skill", user_id="user-123", success=True, latency_ms=150)
usage = analytics.get_skill_usage("my-skill")
print(f"Executions: {usage.execution_count}")
```

### OTLP Backend

```python
# .env
ANALYTICS_BACKEND=otlp
OTLP_ENDPOINT=https://otlp-gateway-prod-us-east-2.grafana.net/otlp
OTLP_INSTANCE_ID=1234567
OTLP_TOKEN=glc_your_token_here

# Code
from orchestrator.execution.analytics import OTLPMetrics

metrics = OTLPMetrics()
metrics.record_skill_execution("my-skill", success=True, latency_ms=150, user_id="user-123")
# Metrics pushed automatically every 60 seconds
```

### Factory Function (Backend-Agnostic)

```python
# .env
ANALYTICS_BACKEND=otlp  # or sqlite

# Code - works with both!
from orchestrator.execution.analytics import create_analytics_client

client = create_analytics_client()  # Auto-detects from ANALYTICS_BACKEND
client.record_skill_execution("my-skill", success=True, latency_ms=150)
```

## Grafana Queries

### SQLite Data Source
```sql
-- Top skills by usage
SELECT skill_id, SUM(execution_count) as total
FROM skill_usage
GROUP BY skill_id
ORDER BY total DESC
LIMIT 10;
```

### OTLP/Prometheus Data Source
```promql
# Top skills by usage rate
topk(10, rate(toolweaver_skill_executions_total[5m]))

# Average latency
avg(toolweaver_skill_latency_milliseconds)

# Success rate percentage
100 * (
  rate(toolweaver_skill_success_total[5m]) /
  rate(toolweaver_skill_executions_total[5m])
)
```

## Migration Between Backends

### From SQLite to OTLP
No data migration needed - just switch env var:
```bash
# Change in .env
ANALYTICS_BACKEND=otlp  # was: sqlite
```
Future metrics go to OTLP, historical data stays in SQLite.

### From OTLP to SQLite
```bash
# Change in .env
ANALYTICS_BACKEND=sqlite  # was: otlp
```
Start collecting locally. Grafana Cloud data retained for 14 days.

## Recommendations

**Use OTLP if:**
- Running in cloud (AWS, Azure, GCP)
- Multiple servers/instances
- Want zero maintenance
- Need industry-standard observability

**Use SQLite if:**
- Local development
- Single server deployment
- Need offline operation
- Want full SQL query capabilities
- Need long retention (>14 days free)

**Production Best Practice:**
Use OTLP for metrics, SQLite for detailed analytics/recommendations.
