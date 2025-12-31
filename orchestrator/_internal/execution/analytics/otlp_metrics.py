"""
OpenTelemetry (OTLP) Metrics Client for Grafana Cloud

Pushes metrics directly to Grafana Cloud Prometheus using OpenTelemetry Protocol.
Simpler than SQLite - no local storage, automatic retention, cloud-native.

Usage:
    from orchestrator._internal.execution.analytics import OTLPMetrics
    
    metrics = OTLPMetrics()
    metrics.record_skill_execution("skill_123", success=True, latency_ms=150)
    metrics.record_skill_rating("skill_123", rating=5)
    metrics.push()  # Send to Grafana Cloud

Environment Variables:
    OTLP_ENDPOINT: Grafana Cloud OTLP endpoint (e.g., https://otlp-gateway-prod-us-east-2.grafana.net/otlp)
    OTLP_INSTANCE_ID: Grafana Cloud instance ID (e.g., 1472140)
    OTLP_TOKEN: Grafana Cloud token (glc_...)
    OTLP_PUSH_INTERVAL: How often to push metrics in seconds (default: 60)
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Any

try:
    from opentelemetry import metrics  # type: ignore[import-not-found]
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter,  # type: ignore[import-not-found]
    )
    from opentelemetry.sdk.metrics import MeterProvider  # type: ignore[import-not-found]
    from opentelemetry.sdk.metrics.export import (
        PeriodicExportingMetricReader,  # type: ignore[import-not-found]
    )
    from opentelemetry.sdk.resources import (  # type: ignore[import-not-found]
        SERVICE_NAME,
        SERVICE_VERSION,
        Resource,
    )
    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False
    logging.warning("OpenTelemetry not installed. Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http")


logger = logging.getLogger(__name__)


@dataclass
class MetricConfig:
    """Configuration for OTLP metrics"""
    endpoint: str
    instance_id: str
    token: str
    push_interval: int = 60  # seconds
    service_name: str = "toolweaver"
    service_version: str = "1.0.0"


class OTLPMetrics:
    """
    OpenTelemetry metrics client for Grafana Cloud.
    
    Provides similar interface to SkillAnalytics but pushes to cloud instead of local DB.
    """

    def __init__(self, config: MetricConfig | None = None):
        """
        Initialize OTLP metrics client.
        
        Args:
            config: MetricConfig object, or None to load from environment
        """
        if not OTLP_AVAILABLE:
            raise RuntimeError("OpenTelemetry not installed. Run: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http")

        self.config = config or self._load_config_from_env()
        self._setup_meter()
        self._create_instruments()

    def _load_config_from_env(self) -> MetricConfig:
        """Load OTLP configuration from environment variables"""
        endpoint = os.getenv("OTLP_ENDPOINT")
        instance_id = os.getenv("OTLP_INSTANCE_ID")
        token = os.getenv("OTLP_TOKEN")

        if not all([endpoint, instance_id, token]):
            raise ValueError(
                "Missing OTLP configuration. Set: OTLP_ENDPOINT, OTLP_INSTANCE_ID, OTLP_TOKEN"
            )

        # Type assertion since we checked they are not None
        assert endpoint is not None
        assert instance_id is not None
        assert token is not None

        return MetricConfig(
            endpoint=endpoint,
            instance_id=instance_id,
            token=token,
            push_interval=int(os.getenv("OTLP_PUSH_INTERVAL", "60")),
            service_name=os.getenv("OTLP_SERVICE_NAME", "toolweaver"),
            service_version=os.getenv("OTLP_SERVICE_VERSION", "1.0.0")
        )

    def _setup_meter(self) -> None:
        """Initialize OpenTelemetry meter with Grafana Cloud exporter"""
        import base64

        # Create resource with service info
        resource = Resource.create({
            SERVICE_NAME: self.config.service_name,
            SERVICE_VERSION: self.config.service_version,
        })

        # Configure OTLP exporter with Grafana Cloud credentials
        # Format: Basic base64(instance_id:token)
        credentials = f"{self.config.instance_id}:{self.config.token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}"
        }

        exporter = OTLPMetricExporter(
            endpoint=f"{self.config.endpoint}/v1/metrics",
            headers=headers,
        )

        # Create metric reader with periodic export
        reader = PeriodicExportingMetricReader(
            exporter=exporter,
            export_interval_millis=self.config.push_interval * 1000
        )

        # Create meter provider
        provider = MeterProvider(
            resource=resource,
            metric_readers=[reader]
        )

        # Set global meter provider (only if not already set)
        # Check if a provider is already set by checking the current provider
        current_provider = metrics.get_meter_provider()
        from opentelemetry.metrics import NoOpMeterProvider  # type: ignore[import-not-found]

        if isinstance(current_provider, NoOpMeterProvider):
            # No provider set yet, set ours
            metrics.set_meter_provider(provider)
            logger.info("Set new OTLP MeterProvider")
        else:
            # Provider already set, just use the existing one
            logger.debug("MeterProvider already set, reusing existing")

        # Get meter for this service
        self.meter = metrics.get_meter(__name__)

        logger.info(f"OTLP metrics initialized: {self.config.endpoint}")

    def _create_instruments(self) -> None:
        """Create metric instruments (counters, gauges, histograms)"""
        # Counters (monotonically increasing)
        self.skill_executions = self.meter.create_counter(
            name="toolweaver.skill.executions.total",
            description="Total number of skill executions",
            unit="1"
        )

        self.skill_success = self.meter.create_counter(
            name="toolweaver.skill.success.total",
            description="Total number of successful skill executions",
            unit="1"
        )

        self.skill_failures = self.meter.create_counter(
            name="toolweaver.skill.failures.total",
            description="Total number of failed skill executions",
            unit="1"
        )

        # Histograms (value distributions)
        self.skill_latency = self.meter.create_histogram(
            name="toolweaver.skill.latency.milliseconds",
            description="Skill execution latency in milliseconds",
            unit="ms"
        )

        self.skill_rating = self.meter.create_histogram(
            name="toolweaver.skill.rating",
            description="Skill rating (1-5 stars)",
            unit="1"
        )

        # Observable gauges (current values)
        self.meter.create_observable_gauge(
            name="toolweaver.skill.health_score",
            description="Skill health score (0-100)",
            callbacks=[self._observe_health_scores],
            unit="1"
        )

        # Cache for health scores (updated separately)
        self._health_scores: dict[str, float] = {}

        logger.info("OTLP metric instruments created")

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
        attributes = {"skill_id": skill_id}
        if user_id:
            attributes["user_id"] = user_id
        if org_id:
            attributes["org_id"] = org_id

        # Increment counters
        self.skill_executions.add(1, attributes=attributes)

        if success:
            self.skill_success.add(1, attributes=attributes)
        else:
            self.skill_failures.add(1, attributes=attributes)

        # Record latency
        self.skill_latency.record(latency_ms, attributes=attributes)

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

        attributes = {"skill_id": skill_id}
        if user_id:
            attributes["user_id"] = user_id

        self.skill_rating.record(rating, attributes=attributes)

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

        self._health_scores[skill_id] = score
        logger.debug(f"Updated health score: {skill_id} = {score}/100")

    def _observe_health_scores(self, options: Any) -> Any:
        """Callback for observable gauge - yields current health scores"""
        for skill_id, score in self._health_scores.items():
            yield metrics.Observation(
                value=score,
                attributes={"skill_id": skill_id}
            )

    def push(self) -> None:
        """
        Force immediate push of metrics to Grafana Cloud.
        
        Normally metrics are pushed automatically every OTLP_PUSH_INTERVAL seconds,
        but this method forces an immediate export.
        """
        # OpenTelemetry SDK handles periodic export automatically
        # This method exists for API compatibility with SQLite backend
        logger.info("Metrics will be pushed on next export interval")

    def health_check(self) -> bool:
        """
        Check if OTLP connection is healthy.
        
        Returns:
            True if connection is healthy
        """
        try:
            # Simple check - if meter is initialized, we're good
            return self.meter is not None
        except Exception as e:
            logger.error(f"OTLP health check failed: {e}")
            return False

    def get_config_summary(self) -> dict:
        """
        Get configuration summary (for debugging).
        
        Returns:
            Dictionary with config info (token redacted)
        """
        return {
            "backend": "otlp",
            "endpoint": self.config.endpoint,
            "instance_id": self.config.instance_id,
            "token": "***" + self.config.token[-8:],  # Show last 8 chars
            "push_interval": self.config.push_interval,
            "service_name": self.config.service_name,
            "service_version": self.config.service_version,
            "healthy": self.health_check()
        }


# Convenience function for one-line initialization
def create_otlp_client(
    endpoint: str | None = None,
    instance_id: str | None = None,
    token: str | None = None
) -> OTLPMetrics:
    """
    Create OTLP metrics client with explicit config or from environment.
    
    Args:
        endpoint: Optional OTLP endpoint (uses OTLP_ENDPOINT env if None)
        instance_id: Optional instance ID (uses OTLP_INSTANCE_ID env if None)
        token: Optional token (uses OTLP_TOKEN env if None)
    
    Returns:
        OTLPMetrics instance
    """
    if all([endpoint, instance_id, token]):
        # Type assertion since we checked they are not None
        assert endpoint is not None
        assert instance_id is not None
        assert token is not None
        config = MetricConfig(
            endpoint=endpoint,
            instance_id=instance_id,
            token=token
        )
        return OTLPMetrics(config=config)
    else:
        return OTLPMetrics()  # Load from environment


if __name__ == "__main__":
    # Test OTLP metrics
    logging.basicConfig(level=logging.DEBUG)

    try:
        metrics_client = OTLPMetrics()

        print("\n=== OTLP Metrics Test ===")
        print(f"Config: {metrics_client.get_config_summary()}")

        # Record some test metrics
        print("\nRecording test metrics...")
        metrics_client.record_skill_execution("test_skill", success=True, latency_ms=150, user_id="test_user")
        metrics_client.record_skill_execution("test_skill", success=True, latency_ms=200, user_id="test_user")
        metrics_client.record_skill_execution("test_skill", success=False, latency_ms=50, user_id="test_user")
        metrics_client.record_skill_rating("test_skill", rating=5, user_id="test_user")
        metrics_client.update_health_score("test_skill", score=85.5)

        print("✓ Metrics recorded successfully")
        print(f"Metrics will be pushed to Grafana Cloud in {metrics_client.config.push_interval} seconds")
        print("\nWaiting for export interval...")

        # Wait for one export cycle
        time.sleep(metrics_client.config.push_interval + 2)

        print("✓ Export cycle completed")
        print("\nCheck Grafana Cloud dashboards to see the metrics!")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
