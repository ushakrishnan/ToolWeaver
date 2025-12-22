"""
ToolWeaver Phase 5: Advanced Analytics Backend.

Provides metrics collection, aggregation, and visualization for skills.

Components:
- sqlite_schema: Database schema management (local storage)
- skill_analytics: Core analytics engine (SQLite backend)
- otlp_metrics: OpenTelemetry metrics (Grafana Cloud backend)
- grafana_client: Grafana integration

Backends:
- SQLite: Local database storage (good for dev, single-server)
- OTLP: Push to Grafana Cloud Prometheus (cloud-native, auto-retention)

Usage (SQLite):
    from orchestrator._internal.execution.analytics import SkillAnalytics, setup_grafana
    
    # Initialize analytics with SQLite
    analytics = SkillAnalytics(db_path="~/.toolweaver/analytics.db")
    
    # Record skill usage
    analytics.record_skill_usage(
        skill_id="my-skill",
        user_id="user-123",
        success=True,
        latency_ms=245.5
    )
    
    # Setup Grafana dashboards
    setup_grafana(
        url="https://grafana.example.com",
        api_key="your-api-key",
        db_path="~/.toolweaver/analytics.db"
    )

Usage (OTLP/Grafana Cloud):
    from orchestrator._internal.execution.analytics import OTLPMetrics
    
    # Initialize OTLP client (reads from env: OTLP_ENDPOINT, OTLP_INSTANCE_ID, OTLP_TOKEN)
    metrics = OTLPMetrics()
    
    # Record metrics (pushed to Grafana Cloud automatically)
    metrics.record_skill_execution("my-skill", success=True, latency_ms=245.5)
    metrics.record_skill_rating("my-skill", rating=5)
"""

import os
import logging

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

# Try to import OTLP metrics (optional dependency)
try:
    from .otlp_metrics import OTLPMetrics, MetricConfig, create_otlp_client
    OTLP_AVAILABLE = True
except ImportError:
    OTLPMetrics = None
    MetricConfig = None
    create_otlp_client = None
    OTLP_AVAILABLE = False
    logging.warning("OTLP metrics not available. Install: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http")

# Try to import Prometheus metrics (optional dependency)
try:
    from .prometheus_metrics import PrometheusMetrics, PrometheusConfig, create_prometheus_exporter
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PrometheusMetrics = None
    PrometheusConfig = None
    create_prometheus_exporter = None
    PROMETHEUS_AVAILABLE = False
    logging.warning("Prometheus client not available. Install: pip install prometheus-client")

__all__ = [
    # Schema management (SQLite backend)
    "SQLiteSchema",
    "initialize_analytics_db",
    # Core analytics (SQLite backend)
    "SkillAnalytics",
    "SkillUsage",
    "SkillMetrics",
    "SkillRecommendation",
    "MetricType",
    "RecommendationType",
    # OTLP metrics (Grafana Cloud backend)
    "OTLPMetrics",
    "MetricConfig",
    "create_otlp_client",
    "OTLP_AVAILABLE",
    # Prometheus metrics (scraping backend)
    "PrometheusMetrics",
    "PrometheusConfig",
    "create_prometheus_exporter",
    "PROMETHEUS_AVAILABLE",
    # Grafana integration (works with all backends)
    "GrafanaClient",
    "GrafanaConfig",
    "setup_grafana",
    # Factory function
    "create_analytics_client",
]

__version__ = "1.0.0"
__phase__ = "5"


def create_analytics_client(backend: str = None):
    """
    Factory function to create analytics client based on backend selection.
    
    Args:
        backend: 'sqlite', 'otlp', or 'prometheus'. If None, reads from ANALYTICS_BACKEND env var.
    
    Returns:
        SkillAnalytics (SQLite), OTLPMetrics (OTLP), or PrometheusMetrics (Prometheus) instance
    
    Examples:
        # Auto-detect from environment
        analytics = create_analytics_client()
        
        # Explicit backend
        analytics = create_analytics_client(backend='prometheus')
    """
    if backend is None:
        backend = os.getenv("ANALYTICS_BACKEND", "sqlite").lower()
    
    if backend == "otlp":
        if not OTLP_AVAILABLE:
            raise RuntimeError(
                "OTLP backend requested but dependencies not installed. "
                "Run: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http"
            )
        logging.info("Creating OTLP metrics client (Grafana Cloud)")
        return OTLPMetrics()
    
    elif backend == "prometheus":
        if not PROMETHEUS_AVAILABLE:
            raise RuntimeError(
                "Prometheus backend requested but dependencies not installed. "
                "Run: pip install prometheus-client"
            )
        logging.info("Creating Prometheus metrics exporter (HTTP scraping)")
        return PrometheusMetrics()
    
    elif backend == "sqlite":
        logging.info("Creating SQLite analytics client (local database)")
        return SkillAnalytics()
    
    else:
        raise ValueError(f"Unknown analytics backend: {backend}. Use 'sqlite', 'otlp', or 'prometheus'.")
