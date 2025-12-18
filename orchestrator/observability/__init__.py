"""
Observability subpackage.

Consolidates monitoring, metrics collection, and observability backends.
"""

from .monitoring import (
    ToolUsageMonitor,
    ToolCallMetric,
    SearchMetric,
    create_monitor,
    print_metrics_report,
)

# Optional: Monitoring backends (require wandb, prometheus_client for some)
try:
    from .monitoring_backends import (
        MonitoringBackend,
        LocalBackend,
        WandbBackend,
        PrometheusBackend,
    )
    _BACKENDS_AVAILABLE = True
except ImportError:
    _BACKENDS_AVAILABLE = False

__all__ = [
    "ToolUsageMonitor",
    "ToolCallMetric",
    "SearchMetric",
    "create_monitor",
    "print_metrics_report",
]

if _BACKENDS_AVAILABLE:
    __all__.extend([
        "MonitoringBackend",
        "LocalBackend",
        "WandbBackend",
        "PrometheusBackend",
    ])
