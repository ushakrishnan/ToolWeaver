# Analytics Backend Setup

Configure analytics via SQLite (dev), Prometheus (self-hosted), or OTLP (Grafana Cloud).

## Quick start
Set one backend in `.env`:
```
ANALYTICS_BACKEND=sqlite      # local dev (default)
# or
ANALYTICS_BACKEND=prometheus  # self-hosted scrape
# or
ANALYTICS_BACKEND=otlp        # Grafana Cloud push
```
Install extras as needed (`prometheus-client`, or `opentelemetry-...` for OTLP).

## OTLP (Grafana Cloud) — recommended for managed prod
1) Sign up at grafana.com (free tier includes Prometheus/OTLP).
2) In Connections → Prometheus onboarding → choose OTLP over HTTP.
3) Capture Endpoint, Instance ID, Token.
4) Configure env:
```
ANALYTICS_BACKEND=otlp
OTLP_ENDPOINT=https://otlp-gateway-prod-<region>.grafana.net/otlp
OTLP_INSTANCE_ID=<id>
OTLP_TOKEN=<token>
OTLP_PUSH_INTERVAL=60
```
5) Send metrics:
```python
from orchestrator.execution.analytics import OTLPMetrics
metrics = OTLPMetrics()
metrics.record_skill_execution("test_skill", success=True, latency_ms=150)
```
6) View in Grafana Explore (PromQL), e.g., `rate(toolweaver_skill_executions_total[5m])`.

Metrics pushed: executions, successes/failures, latency histogram, rating, health score.

## Prometheus (self-hosted)
1) `pip install prometheus-client`
2) Env:
```
ANALYTICS_BACKEND=prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=8000
PROMETHEUS_HOST=0.0.0.0
```
3) Prometheus scrape config:
```yaml
scrape_configs:
  - job_name: 'toolweaver'
    static_configs:
      - targets: ['localhost:8000']
```
4) Run Prometheus (docker) and add Grafana dashboards.

## SQLite (local dev)
- Zero setup; DB auto-creates at `~/.toolweaver/analytics.db` when analytics run.
- Optional envs:
```
ANALYTICS_DB_PATH=~/.toolweaver/analytics.db
ANALYTICS_DB_RETENTION_DAYS=365
```

## Grafana (Cloud or self-hosted)
- For Cloud: create API key/service account; set `GRAFANA_URL`, `GRAFANA_API_KEY`, `GRAFANA_DATASOURCE_NAME` (e.g., ToolWeaver SQLite).
- For self-hosted: run `docker run -d -p 3000:3000 grafana/grafana:latest`, create API key, set same envs; datasource type `sqlite` or your DB type.

## Verification
- OTLP: metrics visible in Grafana Explore.
- Prometheus: GET `/metrics` and check Prometheus target is up.
- SQLite: `ls ~/.toolweaver/analytics.db` and `sqlite3` to inspect tables if needed.
