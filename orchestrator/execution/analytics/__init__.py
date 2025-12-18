"""
ToolWeaver Phase 5: Advanced Analytics Backend.

Provides metrics collection, aggregation, and visualization for skills.

Components:
- sqlite_schema: Database schema management
- skill_analytics: Core analytics engine
- grafana_client: Grafana integration

Usage:
    from orchestrator.execution.analytics import SkillAnalytics, setup_grafana
    
    # Initialize analytics
    analytics = SkillAnalytics(db_path="~/.toolweaver/analytics.db")
    
    # Record skill usage
    analytics.record_skill_usage(
        skill_id="my-skill",
        user_id="user-123",
        success=True,
        latency_ms=245.5
    )
    
    # Get metrics
    usage = analytics.get_skill_usage("my-skill")
    
    # Setup Grafana dashboards
    setup_grafana(
        url="https://grafana.example.com",
        api_key="your-api-key",
        db_path="~/.toolweaver/analytics.db"
    )
"""

from .sqlite_schema import SQLiteSchema, initialize_analytics_db
from .skill_analytics import (
    SkillAnalytics,
    SkillUsage,
    SkillMetrics,
    SkillRecommendation,
    MetricType,
    RecommendationType,
)
from .grafana_client import GrafanaClient, GrafanaConfig, setup_grafana

__all__ = [
    # Schema management
    "SQLiteSchema",
    "initialize_analytics_db",
    # Core analytics
    "SkillAnalytics",
    "SkillUsage",
    "SkillMetrics",
    "SkillRecommendation",
    "MetricType",
    "RecommendationType",
    # Grafana integration
    "GrafanaClient",
    "GrafanaConfig",
    "setup_grafana",
]

__version__ = "1.0.0"
__phase__ = "5"
