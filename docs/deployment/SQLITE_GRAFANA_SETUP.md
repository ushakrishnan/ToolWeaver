# Analytics Backend Setup Guide

This guide covers setting up analytics for ToolWeaver with **three backend options**:
- **SQLite**: Local database storage (zero config, development)
- **Prometheus**: Self-hosted metrics (real-time, production)
- **OTLP**: Grafana Cloud push (managed, cloud-native)

See [ANALYTICS_STRATEGY.md](../reference/ANALYTICS_STRATEGY.md) for detailed comparison.

---

## Quick Start: Choose Your Backend

**For local development:**
→ Use **SQLite Backend** (zero config, no dependencies)

**For production with self-hosted infrastructure:**
→ Use **Prometheus Backend** (real-time monitoring + alerting)

**For production with managed cloud:**
→ Use **OTLP Backend** (Grafana Cloud, zero maintenance)

Set in `.env`:
```bash
ANALYTICS_BACKEND=sqlite      # Local development
# OR
ANALYTICS_BACKEND=prometheus  # Self-hosted production
# OR
ANALYTICS_BACKEND=otlp        # Grafana Cloud
```

---

## OTLP Backend (Grafana Cloud Prometheus) ⭐ RECOMMENDED

### Why OTLP?

- ✅ **Simpler setup** - No local database files
- ✅ **Cloud-native** - Push metrics directly to Grafana Cloud
- ✅ **Auto-retention** - Grafana manages storage (14 days free tier)
- ✅ **Industry standard** - OpenTelemetry protocol
- ✅ **Free tier** - 10,000 metric series included
- ✅ **No maintenance** - No backups, no cleanup needed

### Architecture:
```
ToolWeaver (Python)
  ↓ pushes metrics via OTLP
  ↓
Grafana Cloud Prometheus
  ↓ queries
  ↓
Grafana Dashboards
  ↓ visualizes
  ↓
Beautiful charts/leaderboards/trends
```

### Setup Steps

1. **Go to Grafana Cloud** (https://grafana.com/auth/sign-up)
   - Sign up for free account
   - Verify email

2. **Navigate to Prometheus Setup**
   - Click "Connections" → "Add new connection"
   - Search for "Prometheus"
   - Click "Prometheus onboarding"

3. **Select Options**
   - Step 1: "Collect and send metrics to a fully-managed Prometheus Stack"
   - Step 2: "Custom Setup Options"
   - Step 3: "Send Metrics over HTTP" → "OpenTelemetry (OTEL)"

4. **Copy Configuration**
   You'll get three values:
   ```
   Endpoint: https://otlp-gateway-prod-{region}.grafana.net/otlp
   Instance ID: 1234567 (numeric)
   Token: glc_... (starts with glc_)
   ```

5. **Configure ToolWeaver**
   Add to `.env`:
   ```bash
   # Backend selection
   ANALYTICS_BACKEND=otlp
   
   # OTLP configuration
   OTLP_ENDPOINT=https://otlp-gateway-prod-us-east-2.grafana.net/otlp
   OTLP_INSTANCE_ID=1234567
   OTLP_TOKEN=glc_your_token_here
   OTLP_PUSH_INTERVAL=60  # seconds
   ```

6. **Install Dependencies**
   ```bash
   pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
   ```

7. **Test It**
   ```python
   from orchestrator.execution.analytics import OTLPMetrics
   
   metrics = OTLPMetrics()
   metrics.record_skill_execution("test_skill", success=True, latency_ms=150)
   # Metrics automatically pushed every 60 seconds
   ```

8. **View in Grafana**
   - Go to your Grafana Cloud instance
   - Navigate to: Explore → PromQL
   - Query: `rate(toolweaver_skill_executions_total[5m])`

### Available Metrics

OTLP pushes these metrics automatically:
- `toolweaver_skill_executions_total` - Counter of executions
- `toolweaver_skill_success_total` - Successful executions
- `toolweaver_skill_failures_total` - Failed executions
- `toolweaver_skill_latency_milliseconds` - Execution time histogram
- `toolweaver_skill_rating` - User ratings (1-5 stars)
- `toolweaver_skill_health_score` - Health score (0-100)

---

## Prometheus Backend (Self-Hosted Production)

### Why Prometheus?

- ✅ **Real-time monitoring** - HTTP /metrics endpoint for scraping
- ✅ **Production-grade** - Industry standard for operations monitoring
- ✅ **Alerting** - Built-in alert manager
- ✅ **Self-hosted** - Full control, no external dependencies
- ✅ **Cost-effective** - Open source, runs on your infrastructure

### Architecture:
```
ToolWeaver (Python)
  ↓ exposes HTTP /metrics endpoint
  ↓
Prometheus Server (scrapes endpoint)
  ↓ stores time-series data
  ↓
Grafana Dashboards
  ↓ queries and visualizes
  ↓
Real-time charts + alerts
```

### Setup Steps

1. **Install prometheus-client**:
```bash
pip install prometheus-client
```

2. **Configure in `.env`**:
```bash
ANALYTICS_BACKEND=prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=8000
PROMETHEUS_HOST=0.0.0.0
```

3. **Run your application** - metrics automatically exposed at `http://localhost:8000/metrics`

4. **Configure Prometheus to scrape**:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'toolweaver'
    static_configs:
      - targets: ['localhost:8000']
```

5. **Start Prometheus**:
```bash
docker run -d -p 9090:9090 -v ./prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
```

6. **Add to Grafana** as data source and create dashboards

See [ANALYTICS_BACKENDS.md](../reference/ANALYTICS_BACKENDS.md) for detailed configuration.

---

## SQLite Backend (Local Database)

### Why SQLite?

- ✅ **Zero installation** - Built into Python
- ✅ **No server needed** - File-based database
- ✅ **Offline-friendly** - No internet required
- ✅ **Good for dev** - Local testing and debugging
- ✅ **Advanced queries** - Full SQL support

### Architecture:
```
ToolWeaver (Python)
  ↓ stores metrics
  ↓
SQLite Database (.sqlite3 file)
  ↓ queries
  ↓
Grafana Dashboards
  ↓ visualizes
  ↓
Beautiful charts/leaderboards/trends
```

---

## SQLite Setup (Local Database)

### Why SQLite?

- ✅ **Zero installation** - Built into Python
- ✅ **No server needed** - File-based database
- ✅ **Perfect for analytics** - Excellent time-series support
- ✅ **Sufficient scale** - Handles millions of records
- ✅ **Free** - No licensing costs

### Option 1: Automatic Setup (Recommended)

SQLite database and tables are **automatically created** on first run:

```python
# When you first run Phase 5 analytics:
from orchestrator.execution.analytics import SkillAnalytics

analytics = SkillAnalytics()
# Automatically creates: ~/.toolweaver/analytics.db
# Automatically creates all tables
```

That's it! No configuration needed beyond setting the env var.

### Option 2: Manual Setup

If you want to pre-create the database:

```bash
cd ~/.toolweaver
# Database and tables auto-create on first write
# OR manually with:
sqlite3 analytics.db < schema.sql
```

### Verify SQLite is Working

```bash
# Check database exists
ls -la ~/.toolweaver/analytics.db

# Query database manually (optional)
sqlite3 ~/.toolweaver/analytics.db

# Inside sqlite3:
> .tables
> SELECT COUNT(*) FROM skill_usage;
> .quit
```

---

## Grafana Setup (Free Tier)

### Prerequisites

- Free Grafana account (https://grafana.com/auth/sign-up)
- OR Docker for self-hosted (optional)

### Option 1: Grafana Cloud Free (Easiest)

1. **Sign up for free**:
   - Go to https://grafana.com/auth/sign-up
   - Create account (free tier included)
   - Verify email

2. **Create API Key or Service Account**:
   - Login to https://grafana.cloud
   - Navigate to **Organization Settings → API Keys** (top navigation → Org Settings)
   - Or use **Service Accounts** (Organization → Service Accounts) - newer recommended approach
   - Create new API key or service account with Editor role
   - Copy the key/token (save it safely)

3. **Get Grafana URL**:
   - From dashboard, note your stack URL
   - Format: `https://YOUR-INSTANCE.grafana.net`

4. **Configure ToolWeaver**:
   ```bash
   # .env file
   GRAFANA_ENABLED=true
   GRAFANA_URL=https://YOUR-INSTANCE.grafana.net
   GRAFANA_API_KEY=your-api-key-here
   GRAFANA_DATASOURCE_NAME=ToolWeaver SQLite
   ```

5. **Done!** Start ToolWeaver Phase 5, which will:
   - Create data source in Grafana
   - Auto-create dashboards
   - Start pushing metrics

### Option 2: Self-Hosted Grafana with Docker

1. **Start Grafana container**:
   ```bash
   docker run -d \
     --name grafana \
     -p 3000:3000 \
     -e GF_SECURITY_ADMIN_PASSWORD=admin \
     grafana/grafana:latest
   ```

2. **Access Grafana**:
   - Go to http://localhost:3000
   - Login with: admin / admin
   - Change password when prompted

3. **Create API Key or Service Account**:
   - Click gear icon (Settings) → API Keys (or Service Accounts)
   - New API Key → Editor role (or create Service Account with Editor role)
   - Copy the key/token

4. **Configure ToolWeaver**:
   ```bash
   # .env file
   GRAFANA_ENABLED=true
   GRAFANA_URL=http://localhost:3000
   GRAFANA_API_KEY=your-api-key-here
   GRAFANA_DATASOURCE_NAME=ToolWeaver SQLite
   GRAFANA_DATASOURCE_TYPE=sqlite  # or postgresql
   ```

5. **Done!** ToolWeaver will auto-configure

### Verify Grafana Connection

```bash
# Test API connection
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://YOUR-INSTANCE.grafana.net/api/health

# Should return: {"database":"ok","version":"..."}
```

---

## Environment Variables Configuration

### SQLite Variables

```bash
# Enable/disable SQLite analytics
ANALYTICS_DB_ENABLED=true

# Database file location (default: ~/.toolweaver/analytics.db)
ANALYTICS_DB_PATH=~/.toolweaver/analytics.db

# Optional: Database connection string
ANALYTICS_DB_URL=sqlite:////home/user/.toolweaver/analytics.db

# Optional: Auto-cleanup old data (days)
ANALYTICS_DB_RETENTION_DAYS=365
```

### Grafana Variables

```bash
# Enable/disable Grafana integration
GRAFANA_ENABLED=true

# Grafana URL (Cloud or self-hosted)
GRAFANA_URL=https://YOUR-INSTANCE.grafana.net
# OR for local:
# GRAFANA_URL=http://localhost:3000

# Grafana API Key (from settings)
GRAFANA_API_KEY=your-api-key-here

# Data source configuration
GRAFANA_DATASOURCE_NAME=ToolWeaver SQLite
GRAFANA_DATASOURCE_TYPE=sqlite

# Organization ID (default: 1)
GRAFANA_ORG_ID=1

# Auto-create dashboards (true/false)
GRAFANA_AUTO_CREATE_DASHBOARDS=true

# Dashboard refresh interval (optional)
GRAFANA_DASHBOARD_REFRESH=30s
```

### Full Example .env

```bash
# ============================================================
# PHASE 5: ANALYTICS WITH SQLite + GRAFANA
# ============================================================

# SQLite Configuration
ANALYTICS_DB_ENABLED=true
ANALYTICS_DB_PATH=~/.toolweaver/analytics.db
ANALYTICS_DB_RETENTION_DAYS=365

# Grafana Cloud (Option 1)
GRAFANA_ENABLED=true
GRAFANA_URL=https://myteam-grafana.grafana.net
GRAFANA_API_KEY=glc_xxxxxYYYYYzzzzz
GRAFANA_DATASOURCE_NAME=ToolWeaver Analytics
GRAFANA_DATASOURCE_TYPE=sqlite
GRAFANA_AUTO_CREATE_DASHBOARDS=true
GRAFANA_DASHBOARD_REFRESH=1m

# OR Grafana Self-Hosted (Option 2)
# GRAFANA_URL=http://localhost:3000
# GRAFANA_API_KEY=eyJrIjoiWHhxxxxx...
```

---

## What Data Gets Stored

ToolWeaver analytics creates these tables automatically:

```
SQLite Database (analytics.db)
├── skill_usage
│   ├── skill_id
│   ├── user_id
│   ├── timestamp
│   ├── execution_count
│   ├── success_count
│   ├── failure_count
│   └── avg_latency_ms
├── skill_metrics
│   ├── skill_id
│   ├── rating_1_5_stars
│   ├── rating_count
│   ├── install_count
│   └── last_updated
├── leaderboard_cache
│   ├── skill_id
│   ├── rank
│   ├── score
│   └── metric_type
└── recommendation_log
    ├── user_id
    ├── recommended_skill_id
    ├── score
    └── timestamp
```

All tables are **auto-created** on first use.

---

## Grafana Dashboards

When Phase 5 starts, ToolWeaver automatically creates these dashboards:

### 1. Usage Trends
- Skill usage over time (line chart)
- Success rates by day
- Adoption curves
- Trending skills

### 2. Leaderboards
- Top 10 skills by usage
- Top skills by rating
- Most improved skills
- Trending new skills

### 3. Performance Metrics
- Execution time by skill
- Success rate percentages
- Error rates
- Latency percentiles

### 4. Adoption Tracking
- Skills per user
- Org adoption rates
- Usage growth metrics
- User engagement

### 5. Health Dashboard
- Skill health scores (0-100)
- Dependency health
- Deprecated skills
- Recommendations effectiveness

---

## Troubleshooting

### SQLite Issues

**"Database locked" error**:
```bash
# Multiple processes writing simultaneously
# Solution: Enable WAL mode (auto-enabled in Phase 5)
sqlite3 ~/.toolweaver/analytics.db "PRAGMA journal_mode=WAL;"
```

**"Disk space full"**:
```bash
# Clean up old data
sqlite3 ~/.toolweaver/analytics.db \
  "DELETE FROM skill_usage WHERE timestamp < date('now', '-365 days');"
```

**Check database integrity**:
```bash
sqlite3 ~/.toolweaver/analytics.db "PRAGMA integrity_check;"
```

### Grafana Issues

**"Connection refused" to Grafana**:
- Check `GRAFANA_URL` is correct
- Verify API key is valid
- For Cloud: https://YOUR-INSTANCE.grafana.net
- For Docker: http://localhost:3000

**"API Key invalid"**:
- Go to Grafana → Settings → API Keys
- Check key hasn't expired
- Create new key if needed

**"Data source not connecting"**:
- Verify SQLite file exists: `ls ~/.toolweaver/analytics.db`
- Check file permissions: `chmod 644 ~/.toolweaver/analytics.db`
- Restart ToolWeaver Phase 5

### Database Queries

**Manually query SQLite**:
```bash
sqlite3 ~/.toolweaver/analytics.db

# List tables
.tables

# Check skill usage
SELECT skill_id, COUNT(*) as uses FROM skill_usage GROUP BY skill_id;

# Recent activity
SELECT * FROM skill_usage ORDER BY timestamp DESC LIMIT 10;

# Export to CSV
.mode csv
.output usage.csv
SELECT * FROM skill_usage;
.quit
```

---

## Performance Tuning

### For Large Datasets (millions of records)

```bash
# Enable indexes for faster queries (auto-enabled)
sqlite3 ~/.toolweaver/analytics.db << EOF
CREATE INDEX idx_skill_usage_timestamp ON skill_usage(timestamp);
CREATE INDEX idx_skill_usage_skill_id ON skill_usage(skill_id);
ANALYZE;
EOF
```

### Optimize Grafana Queries

In Phase 5, analytics queries are optimized to:
- Use indexed columns
- Aggregate at database level
- Cache results in Redis (if available)
- Batch updates to reduce writes

### Monitor Database Size

```bash
# Check database file size
du -h ~/.toolweaver/analytics.db

# If growing too large, enable retention
ANALYTICS_DB_RETENTION_DAYS=180  # Keep 6 months instead of 1 year
```

---

## Backup & Recovery

### Backup Your Analytics Data

```bash
# Manual backup
cp ~/.toolweaver/analytics.db ~/.toolweaver/analytics.db.backup

# Automated backup (add to cron or Windows Task Scheduler)
sqlite3 ~/.toolweaver/analytics.db ".backup analytics_backup.db"
```

### Restore from Backup

```bash
cp ~/.toolweaver/analytics.db.backup ~/.toolweaver/analytics.db
```

### Export All Data

```bash
# Export to JSON
sqlite3 ~/.toolweaver/analytics.db -json > analytics_export.json

# Export specific table to CSV
sqlite3 ~/.toolweaver/analytics.db \
  -header -csv "SELECT * FROM skill_usage;" > usage.csv
```

---

## Security Considerations

### SQLite Security

- **File permissions**: Database stored with 644 (read-only to others)
  ```bash
  chmod 600 ~/.toolweaver/analytics.db  # Owner only
  ```
- **No network exposure**: SQLite is local-only by default
- **Sensitive data**: Metrics don't contain code, only usage stats

### Grafana Security

- **API Key / Service Account Token**: Treated like password, store securely
  - Not in version control
  - Not in logs
  - Rotate periodically (Grafana recommends monthly)
  - **Service Accounts** are the newer recommended approach for programmatic API access
  - API Keys still work fine for this integration
- **Data source**: Connections use authentication
- **Access control**: Grafana has user/org permissions
- **SSL/TLS**: Grafana Cloud uses HTTPS by default

### Best Practices

```bash
# Never commit API keys to git
echo "GRAFANA_API_KEY=*" >> .gitignore

# Use separate API keys for dev/prod
GRAFANA_API_KEY_DEV=glc_dev_xxxxx
GRAFANA_API_KEY_PROD=glc_prod_xxxxx

# Rotate API keys monthly
# Settings → API Keys → Delete old, Create new
```

---

## Next Steps

1. **Set env variables** (see above)
2. **Start Phase 5**: `python -m orchestrator.execution.analytics`
3. **Access Grafana**: https://YOUR-INSTANCE.grafana.net
4. **View dashboards**: Automatically created and populated
5. **Share dashboards**: Team members can view (Grafana users)

---

## Support & Debugging

Enable debug logging for Phase 5:

```bash
# Set log level
ANALYTICS_LOG_LEVEL=DEBUG

# Run with verbose output
python -m orchestrator.execution.analytics --verbose
```

View logs:
```bash
tail -f ~/.toolweaver/analytics.log
```

---

## What's Included in Phase 5

✅ SQLite database schema (auto-created)  
✅ Grafana data source integration  
✅ Auto-dashboard creation  
✅ Metrics aggregation  
✅ Leaderboard computation  
✅ Trend analysis  
✅ Recommendations engine  
✅ Health scoring  
✅ Backup/export tools  

Ready to start Phase 5? 🚀

---

**Last Updated**: December 18, 2025  
**Phase**: 5 (Advanced Analytics)
