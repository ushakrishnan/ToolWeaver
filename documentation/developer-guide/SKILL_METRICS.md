# Skill Metrics and Analytics

Monitor the usage patterns, performance, and quality of your saved skills.

## Overview

The metrics system automatically tracks every skill execution:
- **Usage**: How many times a skill is executed
- **Success Rate**: Percentage of successful executions
- **Latency**: Average execution time (milliseconds)
- **Ratings**: User feedback (1-5 stars)

All data is persisted to `~/.toolweaver/skills/metrics.json` and survives restarts.

## Automatic Tracking

When you use `execute_skill()`, metrics are **automatically captured**:

```python
from orchestrator.runtime import Orchestrator

orch = Orchestrator(...)

# This automatically tracks:
# - Execution time
# - Success/failure
# - Last used timestamp
result = await orch.execute_skill("my_skill", inputs={"x": 5})
```

Or use the timer context manager directly:

```python
from orchestrator.execution import SkillExecutionTimer

with SkillExecutionTimer("my_skill"):
    # Your skill execution code here
    result = my_skill_function()
```

## Adding User Ratings

Let users provide feedback on skill quality:

```python
from orchestrator.execution import rate_skill

# User rates skill 5 stars (excellent)
rate_skill("validate_email", 5)

# User rates skill 3 stars (okay)
rate_skill("process_order", 3)
```

Ratings are accumulated; you can rate the same skill multiple times.

## Viewing Metrics

### All Skills Summary

```python
from orchestrator.execution import print_metrics_report

print_metrics_report()
```

Output:
```
================================================================================
Skill Library Metrics Summary (5 skills)
================================================================================

📊 Most Used Skills:
  1. validate_email                   245 uses
  2. process_order                    189 uses
  3. send_notification                 67 uses

⭐ Highest Rated Skills:
  1. validate_email                 4.92/5.0 (12 ratings)
  2. process_order                  4.30/5.0 (10 ratings)
  3. send_notification              3.80/5.0 (5 ratings)

⚡ Fastest Skills (avg latency):
  1. validate_email                     2.1 ms
  2. parse_config                       5.3 ms
  3. send_notification                 42.7 ms

✅ Most Reliable Skills (success rate):
  1. validate_email                  99.2%
  2. process_order                   98.9%
  3. send_notification               95.5%
```

### Single Skill Report

```python
from orchestrator.execution import print_metrics_report

print_metrics_report('validate_email')
```

Output:
```
============================================================
Metrics for: validate_email
============================================================
Usage Count:    245
Success Rate:   99.2%
Avg Latency:    2.1 ms
Avg Rating:     4.92/5.0 (12 ratings)
Last Used:      2025-01-15T14:23:45
Created:        2025-01-01T09:00:00
```

## Accessing Metrics Programmatically

### Get metrics for a single skill

```python
from orchestrator.execution import get_skill_metrics

metrics = get_skill_metrics("validate_email")
print(f"Used {metrics.usage_count} times")
print(f"Success rate: {metrics.success_rate:.1f}%")
print(f"Avg latency: {metrics.avg_latency_ms:.1f} ms")
print(f"Avg rating: {metrics.avg_rating:.2f}/5.0")
```

### Get all metrics

```python
from orchestrator.execution import get_all_metrics

all_metrics = get_all_metrics()
for name, metrics in all_metrics.items():
    print(f"{name}: {metrics.usage_count} uses, {metrics.success_rate:.1f}% success")
```

### Get top skills by metric

```python
from orchestrator.execution import get_top_skills

# Top 5 most used
top_used = get_top_skills(metric="usage", limit=5)

# Top 5 highest rated
top_rated = get_top_skills(metric="rating", limit=5)

# Top 5 fastest
top_fast = get_top_skills(metric="latency", limit=5)

# Top 5 most reliable
top_reliable = get_top_skills(metric="success_rate", limit=5)
```

## SkillMetrics Data Class

Each skill has aggregated metrics:

```python
@dataclass
class SkillMetrics:
    skill_name: str
    usage_count: int              # Total executions
    success_count: int            # Successful executions
    total_latency_ms: float       # Cumulative latency
    ratings: List[int]            # User ratings (1-5)
    last_used: str                # ISO timestamp
    created_at: str               # ISO timestamp
    
    @property
    def success_rate(self) -> float:
        """Returns 0-100"""
    
    @property
    def avg_latency_ms(self) -> float:
        """Average execution time"""
    
    @property
    def avg_rating(self) -> float:
        """Average of ratings, 1-5 scale"""
```

## Use Cases

### 1. Performance Monitoring

Identify slow skills:

```python
from orchestrator.execution import get_top_skills

slow = get_top_skills(metric="latency", limit=1)
if slow[0].avg_latency_ms > 100:
    print(f"WARNING: {slow[0].skill_name} is slow ({slow[0].avg_latency_ms:.1f} ms)")
    # Consider optimizing or adding caching
```

### 2. Quality Assurance

Track reliability:

```python
from orchestrator.execution import get_skill_metrics

metrics = get_skill_metrics("critical_skill")
if metrics.success_rate < 95:
    print(f"Alert: {metrics.skill_name} has {metrics.success_rate:.1f}% success rate")
    # Review failure logs, add error handling
```

### 3. Cost Optimization

Identify which skills are worth caching/optimizing:

```python
from orchestrator.execution import get_all_metrics

metrics = get_all_metrics()
hot_skills = [m for m in metrics.values() if m.usage_count > 100]
# These are good candidates for Redis caching or optimization
```

### 4. Usage Analytics

Understand which skills are valuable:

```python
from orchestrator.execution import get_top_skills

top = get_top_skills(metric="usage", limit=10)
print("Your most-used skills (candidates for production):")
for m in top:
    print(f"  {m.skill_name}: {m.usage_count} uses, {m.avg_rating:.1f}★")
```

## Integration with CI/CD

Track metrics across environments:

```yaml
# Example: GitHub Actions workflow
- name: Evaluate skill health
  run: |
    python -c "
    from orchestrator.execution import get_all_metrics
    metrics = get_all_metrics()
    
    # Fail if any skill has < 90% success rate
    for m in metrics.values():
        if m.usage_count > 10 and m.success_rate < 90:
            exit(1)
    "
```

## Best Practices

1. **Rate skills regularly**: After using a skill, rate it to build feedback history
2. **Review slow skills**: Skills > 100ms may benefit from caching or optimization
3. **Monitor reliability**: Track success rates for critical skills
4. **Deprecate low-value skills**: Archive skills with low usage/ratings
5. **Collect user feedback**: Encourage teams to rate skills they use

## Data Persistence

Metrics are stored in `~/.toolweaver/skills/metrics.json`:

```json
{
  "validate_email": {
    "skill_name": "validate_email",
    "usage_count": 245,
    "success_count": 243,
    "total_latency_ms": 514.5,
    "ratings": [5, 5, 4, 5, 5],
    "last_used": "2025-01-15T14:23:45",
    "created_at": "2025-01-01T09:00:00"
  }
}
```

## Troubleshooting

**"No metrics available"**
- Execute some skills first; metrics are created on first execution
- Check `~/.toolweaver/skills/metrics.json` exists

**Metrics not updating**
- Ensure skills are being executed with `execute_skill()` or `SkillExecutionTimer`
- Check file permissions on `~/.toolweaver/skills/` directory

**Large metrics file**
- Consider archiving old metrics periodically
- Implement retention policy (e.g., keep last 90 days)

## Future Enhancements

- Metrics export (CSV, Grafana dashboards)
- Anomaly detection (alert on unusual latency)
- Skill versioning with metrics per version
- Team/organization-level metrics aggregation
- Metrics cleanup/archival policies

## Related Documentation

- [Skill Library Reference](../reference/SKILL_LIBRARY.md)
- [Executing Skills Guide](EXECUTING_SKILLS.md)
- [Skill Composition Guide](SKILL_COMPOSITION.md)
