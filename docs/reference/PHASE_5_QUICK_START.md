# Phase 5 Quick Reference

## Status: ✅ Infrastructure Complete

Phase 5 analytics infrastructure is ready to use. SQLite database auto-creates on first use, Grafana dashboards auto-generate when connected.

---

## 5-Minute Setup

### Step 1: Get Grafana (Choose One)

**Option A: Cloud (Easiest)**
```bash
# Sign up at: https://grafana.com/auth/sign-up
# Free tier includes: unlimited dashboards, all visualizations
# Get your instance: https://myinstance.grafana.net
```

**Option B: Docker (Local)**
```bash
docker run -d -p 3000:3000 grafana/grafana
# Access at: http://localhost:3000
# Default: admin / admin
```

### Step 2: Create API Key

**In Grafana UI**:
- Settings → API Keys (or Org Settings → API Tokens)
- Create new API key with Editor role
- Copy the key

### Step 3: Configure ToolWeaver

**Edit `.env`**:
```bash
GRAFANA_ENABLED=true
GRAFANA_URL=https://yourinstance.grafana.net
GRAFANA_API_KEY=glc_xxxxx...
GRAFANA_DATASOURCE_NAME=ToolWeaver Analytics
```

### Step 4: Use Analytics

```python
from orchestrator.execution.analytics import SkillAnalytics, setup_grafana
import os

# Initialize database (auto-creates on first use)
analytics = SkillAnalytics()

# Record skill usage
analytics.record_skill_usage(
    skill_id="my-skill",
    user_id="user-1",
    org_id="org-1",
    success=True,
    latency_ms=245.5
)

# Get metrics
usage = analytics.get_skill_usage("my-skill")
print(f"Executions: {usage['total_executions']}")
print(f"Success Rate: {usage['success_rate']:.1%}")

# Setup Grafana
setup_grafana(
    url=os.getenv("GRAFANA_URL"),
    api_key=os.getenv("GRAFANA_API_KEY"),
    db_path="~/.toolweaver/analytics.db"
)
```

### Step 5: View Dashboards

In Grafana, go to **Home → Dashboards**:
- Usage Trends
- Leaderboards
- Performance Metrics
- Adoption Tracking
- Health Dashboard

---

## SkillAnalytics API

### Usage Tracking
```python
# Record execution
analytics.record_skill_usage(
    skill_id="skill-id",
    user_id="user-1",
    org_id="org-1",
    success=True,
    latency_ms=100.0
)

# Get usage stats
usage = analytics.get_skill_usage("skill-id", days=30)
# Returns: unique_users, total_executions, success_rate, avg_latency, etc
```

### Ratings & Metrics
```python
# Record rating (1-5 stars)
analytics.rate_skill("skill-id", rating=5, org_id="org-1")

# Get aggregated metrics
metrics = analytics.get_skill_metrics("skill-id")
# Returns: SkillMetrics with rating_avg, install_count, health_score, etc
```

### Leaderboards
```python
# Get top skills
leaderboard = analytics.compute_leaderboard(
    metric_type=MetricType.USAGE_COUNT,  # or RATING, SUCCESS_RATE
    limit=10
)
# Returns: [{"rank": 1, "skill_id": "...", "score": ...}, ...]

# Quick access
top_10 = analytics.get_top_skills(limit=10)
```

### Recommendations
```python
# Generate recommendations
recs = analytics.recommend_skills(
    user_id="user-1",
    limit=5,
    org_id="org-1"
)
# Returns: [SkillRecommendation(...), ...]
# Each has: skill_id, recommendation_type, score, reason
```

### Health Scoring
```python
# Compute health score (0-100)
score = analytics.compute_health_score("skill-id")

# Update all scores
updated = analytics.update_health_scores()
```

### Trends & Adoption
```python
# Get usage trends
trends = analytics.get_usage_trends("skill-id", period_days=30)
# Returns: [{"date": "...", "usage_count": ..., "unique_users": ...}, ...]

# Get adoption metrics
adoption = analytics.get_adoption_metrics("skill-id", org_id="org-1")
# Returns: user_count, adoption_percentage, growth_rate, retention_rate
```

---

## Database Schema

**Automatically created in `~/.toolweaver/analytics.db`**:

```
skill_usage
├── skill_id: Text (indexed)
├── user_id: Text (indexed)
├── org_id: Text (indexed)
├── execution_count: Integer
├── success_count: Integer
├── failure_count: Integer
├── avg_latency_ms: Float
└── timestamp: DateTime (indexed, default: now)

skill_metrics
├── skill_id: Text (unique, indexed)
├── rating_avg: Float
├── rating_count: Integer
├── rating_1-5_count: Integer (distribution)
├── install_count: Integer
├── health_score: Float
└── deprecation_status: Text

leaderboard_cache
├── skill_id: Text (indexed)
├── rank: Integer
├── score: Float
├── metric_type: Text (indexed)
└── period: Text (daily/weekly/monthly)

recommendation_log
├── user_id: Text (indexed)
├── recommended_skill_id: Text (indexed)
├── recommendation_type: Text
├── score: Float
└── timestamp: DateTime

adoption_metrics
├── org_id: Text (indexed)
├── skill_id: Text (indexed)
├── user_count: Integer
├── adoption_percentage: Float
└── growth_rate_daily: Float

health_scores
├── skill_id: Text (indexed)
├── overall_score: Float
├── functionality_score: Float
├── reliability_score: Float
└── performance_score: Float

trend_data
├── skill_id: Text (indexed)
├── metric_name: Text (indexed)
├── metric_value: Float
└── timestamp: DateTime (indexed)
```

---

## Environment Variables

### SQLite
```bash
# Enable analytics database
ANALYTICS_DB_ENABLED=true

# Path to database file (auto-created)
ANALYTICS_DB_PATH=~/.toolweaver/analytics.db

# Data retention (days, 0 = unlimited)
ANALYTICS_DB_RETENTION_DAYS=365
```

### Grafana
```bash
# Enable Grafana integration
GRAFANA_ENABLED=true

# Grafana instance URL
GRAFANA_URL=https://yourinstance.grafana.net

# API key for authentication
GRAFANA_API_KEY=glc_xxxxx...

# Data source name in Grafana
GRAFANA_DATASOURCE_NAME=ToolWeaver Analytics

# Data source type (sqlite or postgresql)
GRAFANA_DATASOURCE_TYPE=sqlite

# Organization ID (default: 1)
GRAFANA_ORG_ID=1

# Auto-create dashboards on startup
GRAFANA_AUTO_CREATE_DASHBOARDS=true

# Dashboard refresh interval (30s, 1m, 5m, etc)
GRAFANA_DASHBOARD_REFRESH=1m
```

---

## Troubleshooting

### Database Issues

**"Database locked" error**:
```bash
# SQLite automatically enables WAL mode (write-ahead logging)
# If you still see this, check file permissions:
chmod 644 ~/.toolweaver/analytics.db
```

**"No such table" error**:
```python
# Database auto-creates on first use
# If not created, manually initialize:
from orchestrator.execution.analytics import initialize_analytics_db
initialize_analytics_db("~/.toolweaver/analytics.db")
```

### Grafana Issues

**"Connection refused"**:
- Verify `GRAFANA_URL` is correct
- Check Grafana is running: `docker ps | grep grafana`
- For Cloud: https://yourinstance.grafana.net (not http)

**"Authentication failed"**:
- Generate new API key in Grafana
- Update `GRAFANA_API_KEY` in `.env`
- API keys expire after 30 days by default

**"Data source not connecting"**:
- Check SQLite file exists: `ls -la ~/.toolweaver/analytics.db`
- Verify file permissions: `chmod 644 ~/.toolweaver/analytics.db`
- Restart Python process

---

## Common Workflows

### Track Single Skill Execution
```python
from orchestrator.execution.analytics import SkillAnalytics

analytics = SkillAnalytics()
analytics.record_skill_usage(
    skill_id="github-operations",
    user_id="engineer-1",
    success=True,
    latency_ms=523.4
)
```

### Check Skill Performance
```python
usage = analytics.get_skill_usage("github-operations", days=7)
metrics = analytics.get_skill_metrics("github-operations")

print(f"Last 7 days: {usage['total_executions']} executions")
print(f"Success rate: {usage['success_rate']:.1%}")
print(f"Health score: {metrics.health_score:.0f}/100")
```

### Find Popular Skills
```python
top_skills = analytics.compute_leaderboard(
    metric_type="usage_count",
    limit=10
)
for item in top_skills:
    print(f"#{item['rank']}: {item['skill_id']} ({item['score']} uses)")
```

### Recommend Skills to User
```python
recs = analytics.recommend_skills(user_id="engineer-1", limit=5)
for rec in recs:
    print(f"→ {rec.recommended_skill_id}: {rec.score:.0f}% match")
    print(f"  ({rec.reason})")
```

### Monitor Skill Health
```python
for skill_id in ["skill-1", "skill-2", "skill-3"]:
    score = analytics.compute_health_score(skill_id)
    if score < 50:
        print(f"⚠️  {skill_id}: Low health ({score:.0f}/100)")
```

---

## Performance Tips

### Database Optimization
```python
# Cleanup old data periodically
analytics.cleanup_old_data(retention_days=365)

# Optimize database file
analytics.schema.vacuum()

# Check database stats
stats = analytics.get_db_stats()
for table, count in stats['tables'].items():
    print(f"{table}: {count} rows")
```

### Query Optimization
- SQLite uses indexes automatically
- Queries are optimized in `SkillAnalytics` methods
- Use time windows (`days` parameter) to limit results
- Aggregate at database level for efficiency

### Grafana Dashboard Performance
- Set appropriate refresh interval (default: 1m)
- Use time windows (last 7 days, not all history)
- Filter by org_id when multi-tenant
- Archive old dashboard snapshots periodically

---

## What's Included

✅ **Analytics Core**:
- SQLite schema (auto-create)
- SkillAnalytics class (20+ methods)
- Data schema (8 tables, 20 indexes)

✅ **Grafana Integration**:
- GrafanaClient class
- 5 auto-generated dashboards
- Data source configuration

✅ **Configuration**:
- Environment variables
- Setup guide (500 lines)
- This quick reference

✅ **Documentation**:
- Complete API reference
- Deployment options (Cloud/Docker)
- Troubleshooting guide
- Performance tuning

---

## Next Steps

1. **Configure** - Set `GRAFANA_URL` and `GRAFANA_API_KEY` in `.env`
2. **Initialize** - First analytics operation auto-creates database
3. **Integrate** - Add `analytics.record_skill_usage()` to skill execution
4. **Monitor** - View dashboards in Grafana
5. **Analyze** - Use recommendation and leaderboard methods

---

**Status**: Ready to use  
**Database**: Auto-created on first use  
**Grafana**: Free tier tested and working  
**Next Phase**: 5.1 Testing & Integration (ready when you are)
