"""
Prometheus Metrics Exporter for ToolWeaver.

Traditional pull-based Prometheus metrics exposition via HTTP /metrics endpoint.
This is the classic Prometheus model where Prometheus scrapes your application.

Usage:
    from orchestrator._internal.execution.analytics import PrometheusMetrics

    # Start metrics server
    metrics = PrometheusMetrics(port=8000)

    # Record metrics
    metrics.record_skill_execution("skill_123", success=True, latency_ms=150)

    # Prometheus scrapes http://localhost:8000/metrics

Environment Variables:
    PROMETHEUS_ENABLED: Enable Prometheus metrics (true/false)
    PROMETHEUS_PORT: Port for metrics endpoint (default: 8000)
    PROMETHEUS_HOST: Host to bind to (default: 0.0.0.0)
"""

import logging
import os
from dataclasses import dataclass

try:
    from prometheus_client import REGISTRY, Counter, Gauge, Histogram, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("Prometheus client not installed. Install with: pip install prometheus-client")


logger = logging.getLogger(__name__)


@dataclass
class PrometheusConfig:
    """Configuration for Prometheus metrics"""
    port: int = 8000
    host: str = "0.0.0.0"
    enabled: bool = True


class PrometheusMetrics:
    """
    Prometheus metrics exporter for ToolWeaver.

    Exposes metrics via HTTP endpoint for Prometheus scraping.
    """

    def __init__(self, config: PrometheusConfig | None = None):
        """
        Initialize Prometheus metrics exporter.

        Args:
            config: PrometheusConfig object, or None to load from environment
        """
        if not PROMETHEUS_AVAILABLE:
            raise RuntimeError("Prometheus client not installed. Run: pip install prometheus-client")

        self.config = config or self._load_config_from_env()
        self._create_metrics()

        if self.config.enabled:
            self._start_server()

    def _load_config_from_env(self) -> PrometheusConfig:
        """Load Prometheus configuration from environment variables"""
        return PrometheusConfig(
            port=int(os.getenv("PROMETHEUS_PORT", "8000")),
            host=os.getenv("PROMETHEUS_HOST", "0.0.0.0"),
            enabled=os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
        )

    def _start_server(self) -> None:
        """Start HTTP server for metrics endpoint"""
        try:
            start_http_server(self.config.port, addr=self.config.host, registry=REGISTRY)
            logger.info(f"Prometheus metrics server started: http://{self.config.host}:{self.config.port}/metrics")
        except OSError as e:
            if "already in use" in str(e).lower():
                logger.warning(f"Port {self.config.port} already in use, metrics server not started")
            else:
                raise

    def _create_metrics(self) -> None:
        """Create Prometheus metric instruments"""
        # Check if metrics already registered (avoid duplicates in tests)
        try:
            # Try to get existing metrics
            self.skill_executions = REGISTRY._names_to_collectors.get('toolweaver_skill_executions_total')
            if self.skill_executions:
                logger.debug("Reusing existing Prometheus metrics")
                self.skill_success = REGISTRY._names_to_collectors['toolweaver_skill_success_total']
                self.skill_failures = REGISTRY._names_to_collectors['toolweaver_skill_failures_total']
                self.skill_latency = REGISTRY._names_to_collectors['toolweaver_skill_latency_milliseconds']
                self.skill_rating = REGISTRY._names_to_collectors['toolweaver_skill_rating']
                self.skill_health_score = REGISTRY._names_to_collectors['toolweaver_skill_health_score']
                return
        except Exception:
            pass

        # Counters (monotonically increasing)
        self.skill_executions = Counter(
            'toolweaver_skill_executions_total',
            'Total number of skill executions',
            ['skill_id', 'user_id', 'org_id']
        )

        self.skill_success = Counter(
            'toolweaver_skill_success_total',
            'Total number of successful skill executions',
            ['skill_id', 'user_id', 'org_id']
        )

        self.skill_failures = Counter(
            'toolweaver_skill_failures_total',
            'Total number of failed skill executions',
            ['skill_id', 'user_id', 'org_id']
        )

        # Histograms (value distributions)
        self.skill_latency = Histogram(
            'toolweaver_skill_latency_milliseconds',
            'Skill execution latency in milliseconds',
            ['skill_id', 'user_id', 'org_id'],
            buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000]
        )

        self.skill_rating = Histogram(
            'toolweaver_skill_rating',
            'Skill rating (1-5 stars)',
            ['skill_id', 'user_id'],
            buckets=[1, 2, 3, 4, 5]
        )

        # Gauges (current values)
        self.skill_health_score = Gauge(
            'toolweaver_skill_health_score',
            'Skill health score (0-100)',
            ['skill_id']
        )

        logger.info("Prometheus metric instruments created")

    def record_skill_execution(
        self,
        skill_id: str,
        success: bool,
        latency_ms: float,
        user_id: str | None = None,
        org_id: str | None = None
    ) -> None:
        """
        Record a skill execution event.

        Args:
            skill_id: Unique skill identifier
            success: Whether execution succeeded
            latency_ms: Execution time in milliseconds
            user_id: Optional user identifier
            org_id: Optional organization identifier
        """
        labels = {
            'skill_id': skill_id,
            'user_id': user_id or 'unknown',
            'org_id': org_id or 'default'
        }

        # Increment counters
        self.skill_executions.labels(**labels).inc()

        if success:
            self.skill_success.labels(**labels).inc()
        else:
            self.skill_failures.labels(**labels).inc()

        # Record latency
        self.skill_latency.labels(**labels).observe(latency_ms)

        logger.debug(f"Recorded execution: {skill_id} ({'success' if success else 'failure'}, {latency_ms}ms)")

    def record_skill_rating(
        self,
        skill_id: str,
        rating: int,
        user_id: str | None = None
    ) -> None:
        """
        Record a skill rating (1-5 stars).

        Args:
            skill_id: Unique skill identifier
            rating: Rating value (1-5)
            user_id: Optional user identifier
        """
        if not 1 <= rating <= 5:
            raise ValueError(f"Rating must be 1-5, got {rating}")

        labels = {
            'skill_id': skill_id,
            'user_id': user_id or 'unknown'
        }

        self.skill_rating.labels(**labels).observe(rating)

        logger.debug(f"Recorded rating: {skill_id} = {rating} stars")

    def update_health_score(self, skill_id: str, score: float) -> None:
        """
        Update health score for a skill (0-100).

        Args:
            skill_id: Unique skill identifier
            score: Health score (0-100)
        """
        if not 0 <= score <= 100:
            raise ValueError(f"Health score must be 0-100, got {score}")

        self.skill_health_score.labels(skill_id=skill_id).set(score)
        logger.debug(f"Updated health score: {skill_id} = {score}/100")

    def health_check(self) -> bool:
        """
        Check if Prometheus metrics are healthy.

        Returns:
            True if metrics are working
        """
        try:
            return True
        except Exception as e:
            logger.error(f"Prometheus health check failed: {e}")
            return False

    def get_config_summary(self) -> dict:
        """
        Get configuration summary (for debugging).

        Returns:
            Dictionary with config info
        """
        return {
            "backend": "prometheus",
            "endpoint": f"http://{self.config.host}:{self.config.port}/metrics",
            "port": self.config.port,
            "host": self.config.host,
            "enabled": self.config.enabled,
            "healthy": self.health_check()
        }


# Convenience function for one-line initialization
def create_prometheus_exporter(
    port: int | None = None,
    host: str | None = None
) -> PrometheusMetrics:
    """
    Create Prometheus metrics exporter with explicit config or from environment.

    Args:
        port: Optional port (uses PROMETHEUS_PORT env if None)
        host: Optional host (uses PROMETHEUS_HOST env if None)

    Returns:
        PrometheusMetrics instance
    """
    if port or host:
        config = PrometheusConfig(
            port=port or 8000,
            host=host or "0.0.0.0"
        )
        return PrometheusMetrics(config=config)
    else:
        return PrometheusMetrics()  # Load from environment


if __name__ == "__main__":
    # Test Prometheus metrics
    logging.basicConfig(level=logging.INFO)

    try:
        metrics = PrometheusMetrics()

        print("\n=== Prometheus Metrics Test ===")
        print(f"Config: {metrics.get_config_summary()}")

        # Record some test metrics
        print("\nRecording test metrics...")
        metrics.record_skill_execution("test_skill", success=True, latency_ms=150, user_id="test_user")
        metrics.record_skill_execution("test_skill", success=True, latency_ms=200, user_id="test_user")
        metrics.record_skill_execution("test_skill", success=False, latency_ms=50, user_id="test_user")
        metrics.record_skill_rating("test_skill", rating=5, user_id="test_user")
        metrics.update_health_score("test_skill", score=85.5)

        print("✓ Metrics recorded successfully")
        print(f"\n✓ Metrics exposed at: http://localhost:{metrics.config.port}/metrics")
        print("\nTest with:")
        print(f"  curl http://localhost:{metrics.config.port}/metrics")
        print("\nOr configure Prometheus to scrape this endpoint.")
        print("\nPress Ctrl+C to stop...")

        # Keep running
        import time
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n✓ Stopped")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
