"""
Tool Usage Monitoring and Observability

Tracks tool usage, errors, performance, and costs for production monitoring.
Provides metrics collection, logging, and performance analysis.

Supports pluggable backends:
- Local: File-based logging (default, no dependencies)
- W&B: Weights & Biases integration (optional)
- Prometheus: Metrics export (optional)
"""

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class ToolCallMetric:
    """Single tool call metric."""
    timestamp: str
    tool_name: str
    success: bool
    latency: float
    error: str | None = None
    execution_id: str | None = None


@dataclass
class SearchMetric:
    """Search query metric."""
    timestamp: str
    query: str
    num_results: int
    latency: float
    cache_hit: bool = False


class ToolUsageMonitor:
    """
    Track tool usage, errors, performance for production monitoring.

    Features:
    - Per-tool call counts, error rates, latency percentiles
    - Search query tracking
    - Cache hit/miss rates
    - Token usage tracking
    - Pluggable backends (local, W&B, Prometheus)
    - In-memory metrics aggregation

    Examples:
        # Local only (default)
        monitor = ToolUsageMonitor()

        # W&B integration
        monitor = ToolUsageMonitor(backends=["local", "wandb"])

        # Prometheus for production
        monitor = ToolUsageMonitor(backends=["prometheus"])

        # All backends
        monitor = ToolUsageMonitor(backends=["local", "wandb", "prometheus"])
    """

    def __init__(
        self,
        backends: str | list[str] | None = None,
        log_to_file: bool = True,
        log_dir: str = ".tool_logs",
        backend_config: dict[str, Any] | None = None
    ):
        """
        Initialize monitoring with pluggable backends.

        Args:
            backends: Backend(s) to use: "local", "wandb", "prometheus" or list
            log_to_file: Enable file logging (for local backend)
            log_dir: Directory for log files (for local backend)
            backend_config: Backend-specific configuration dict
        """
        # Normalize backends
        if backends is None:
            backends = ["local"]
        elif isinstance(backends, str):
            backends = [backends]

        self.backends: list[Any] = []
        backend_config = backend_config or {}

        # Initialize backends
        for backend_type in backends:
            try:
                if backend_type == "local":
                    from orchestrator._internal.observability.monitoring_backends import (
                        LocalBackend,
                    )
                    config = backend_config.get("local", {"log_dir": log_dir})
                    self.backends.append(LocalBackend(**config))

                elif backend_type == "wandb":
                    from orchestrator._internal.observability.monitoring_backends import (
                        WandbBackend,
                    )
                    config = backend_config.get("wandb", {})
                    self.backends.append(WandbBackend(**config))
                    print("✅ W&B monitoring enabled")

                elif backend_type == "prometheus":
                    from orchestrator._internal.observability.monitoring_backends import (
                        PrometheusBackend,
                    )
                    config = backend_config.get("prometheus", {})
                    self.backends.append(PrometheusBackend(**config))

                else:
                    print(f"⚠️  Unknown backend type: {backend_type}")

            except ImportError as e:
                print(f"⚠️  Could not load {backend_type} backend: {e}")

        # Backward compatibility
        self.log_to_file = log_to_file
        self.log_dir = log_dir

        # In-memory metrics (for get_summary, etc.)
        self.metrics: dict[str, Any] = {
            "tool_calls": defaultdict(int),
            "tool_errors": defaultdict(int),
            "tool_latency": defaultdict(list),
            "search_queries": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "token_usage": {"input": 0, "output": 0, "cached": 0}
        }

        # Detailed logs (last 1000 events)
        self.tool_call_log: list[ToolCallMetric] = []
        self.search_log: list[SearchMetric] = []

    def log_tool_call(
        self,
        tool_name: str,
        success: bool,
        latency: float,
        error: str | None = None,
        execution_id: str | None = None
    ) -> None:
        """
        Log individual tool call.

        Args:
            tool_name: Name of tool called
            success: Whether call succeeded
            latency: Execution time in seconds
            error: Error message if failed
            execution_id: Unique execution identifier
        """
        # Update aggregated metrics
        self.metrics["tool_calls"][tool_name] += 1
        self.metrics["tool_latency"][tool_name].append(latency)

        if not success:
            self.metrics["tool_errors"][tool_name] += 1

        # Add to detailed log (keep last 1000)
        metric = ToolCallMetric(
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool_name=tool_name,
            success=success,
            latency=latency,
            error=error,
            execution_id=execution_id
        )
        self.tool_call_log.append(metric)
        if len(self.tool_call_log) > 1000:
            self.tool_call_log.pop(0)

        # Send to all backends
        for backend in self.backends:
            try:
                backend.log_tool_call(tool_name, success, latency, error, execution_id)
            except Exception as e:
                print(f"⚠️  Backend error: {e}")

    def log_search_query(
        self,
        query: str,
        num_results: int,
        latency: float,
        cache_hit: bool = False
    ) -> None:
        """
        Log tool search query.

        Args:
            query: Search query text
            num_results: Number of results returned
            latency: Search time in seconds
            cache_hit: Whether results were cached
        """
        metric = SearchMetric(
            timestamp=datetime.now(timezone.utc).isoformat(),
            query=query,
            num_results=num_results,
            latency=latency,
            cache_hit=cache_hit
        )

        self.search_log.append(metric)
        if len(self.search_log) > 1000:
            self.search_log.pop(0)

        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1

        # Send to all backends
        for backend in self.backends:
            try:
                backend.log_search_query(query, num_results, latency, cache_hit)
            except Exception as e:
                print(f"⚠️  Backend error: {e}")

    def log_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ) -> None:
        """
        Log LLM token usage.

        Args:
            input_tokens: Input tokens used
            output_tokens: Output tokens generated
            cached_tokens: Tokens read from cache
        """
        self.metrics["token_usage"]["input"] += input_tokens
        self.metrics["token_usage"]["output"] += output_tokens
        self.metrics["token_usage"]["cached"] += cached_tokens

        # Send to all backends
        for backend in self.backends:
            try:
                backend.log_token_usage(input_tokens, output_tokens, cached_tokens)
            except Exception as e:
                print(f"⚠️  Backend error: {e}")

    def get_tool_metrics(self, tool_name: str) -> dict[str, Any]:
        """
        Get aggregated metrics for a specific tool.

        Args:
            tool_name: Tool to analyze

        Returns:
            Dictionary with call count, error rate, latency percentiles
        """
        calls = self.metrics["tool_calls"].get(tool_name, 0)
        errors = self.metrics["tool_errors"].get(tool_name, 0)
        latencies = self.metrics["tool_latency"].get(tool_name, [])

        if not calls:
            return {"error": f"No metrics for tool '{tool_name}'"}

        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        p50 = sorted_latencies[len(sorted_latencies) // 2] if sorted_latencies else 0
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)] if sorted_latencies else 0

        return {
            "tool_name": tool_name,
            "total_calls": calls,
            "errors": errors,
            "error_rate": errors / calls if calls else 0,
            "success_rate": (calls - errors) / calls if calls else 0,
            "latency": {
                "min": min(latencies) if latencies else 0,
                "max": max(latencies) if latencies else 0,
                "avg": sum(latencies) / len(latencies) if latencies else 0,
                "p50": p50,
                "p95": p95,
                "p99": p99
            }
        }

    def get_summary(self) -> dict[str, Any]:
        """
        Get overall monitoring summary.

        Returns:
            Dictionary with all aggregated metrics
        """
        total_calls = sum(self.metrics["tool_calls"].values())
        total_errors = sum(self.metrics["tool_errors"].values())

        cache_total = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = self.metrics["cache_hits"] / cache_total if cache_total else 0

        return {
            "overview": {
                "total_tool_calls": total_calls,
                "total_errors": total_errors,
                "overall_error_rate": total_errors / total_calls if total_calls else 0,
                "unique_tools": len(self.metrics["tool_calls"]),
                "search_queries": len(self.search_log),
                "cache_hit_rate": cache_hit_rate
            },
            "top_tools": self._get_top_tools(5),
            "token_usage": self.metrics["token_usage"],
            "cache_performance": {
                "hits": self.metrics["cache_hits"],
                "misses": self.metrics["cache_misses"],
                "hit_rate": cache_hit_rate
            }
        }

    def get_recent_errors(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent tool errors.

        Args:
            limit: Maximum number of errors to return

        Returns:
            List of recent error records
        """
        errors = [
            asdict(m) for m in self.tool_call_log
            if not m.success
        ]
        return errors[-limit:]

    def export_metrics(self, filepath: str) -> None:
        """
        Export all metrics to JSON file.

        Args:
            filepath: Output file path
        """
        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "summary": self.get_summary(),
            "tool_metrics": {
                name: self.get_tool_metrics(name)
                for name in self.metrics["tool_calls"].keys()
            },
            "recent_calls": [asdict(m) for m in self.tool_call_log[-100:]],
            "recent_searches": [asdict(m) for m in self.search_log[-100:]]
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

    def flush(self) -> None:
        """
        Flush all backends (useful for W&B, graceful shutdown).
        Call this at the end of your program.
        """
        for backend in self.backends:
            try:
                backend.flush()
            except Exception as e:
                print(f"⚠️  Backend flush error: {e}")

    def _get_top_tools(self, limit: int = 5) -> list[dict[str, Any]]:
        """Get top tools by call count."""
        tools = [
            {"tool": name, "calls": count}
            for name, count in self.metrics["tool_calls"].items()
        ]
        return sorted(tools, key=lambda x: x["calls"], reverse=True)[:limit]


# Convenience functions

def create_monitor(log_dir: str = ".tool_logs") -> ToolUsageMonitor:
    """Create a new monitoring instance."""
    return ToolUsageMonitor(log_to_file=True, log_dir=log_dir)


def print_metrics_report(monitor: ToolUsageMonitor) -> None:
    """Print formatted metrics report."""
    summary = monitor.get_summary()

    print("=" * 80)
    print("TOOL USAGE MONITORING REPORT")
    print("=" * 80)

    print("\n📊 Overview:")
    overview = summary["overview"]
    print(f"   Total tool calls:    {overview['total_tool_calls']:,}")
    print(f"   Total errors:        {overview['total_errors']:,}")
    print(f"   Overall error rate:  {overview['overall_error_rate']:.1%}")
    print(f"   Unique tools used:   {overview['unique_tools']}")
    print(f"   Search queries:      {overview['search_queries']:,}")
    print(f"   Cache hit rate:      {overview['cache_hit_rate']:.1%}")

    print("\n🔧 Top Tools:")
    for tool in summary["top_tools"]:
        metrics = monitor.get_tool_metrics(tool["tool"])
        print(f"   {tool['tool']:<30} {tool['calls']:>5} calls  "
              f"(p50: {metrics['latency']['p50']*1000:.0f}ms, "
              f"errors: {metrics['error_rate']:.1%})")

    print("\n💰 Token Usage:")
    tokens = summary["token_usage"]
    print(f"   Input tokens:   {tokens['input']:>10,}")
    print(f"   Output tokens:  {tokens['output']:>10,}")
    print(f"   Cached tokens:  {tokens['cached']:>10,}")

    total_tokens = tokens['input'] + tokens['output']
    if tokens['cached'] > 0:
        savings = tokens['cached'] / (total_tokens + tokens['cached']) * 100
        print(f"   Cache savings:  {savings:>9.1f}%")

    print("\n🚨 Recent Errors:")
    errors = monitor.get_recent_errors(5)
    if errors:
        for err in errors:
            print(f"   [{err['timestamp']}] {err['tool_name']}: {err['error']}")
    else:
        print("   No recent errors")

    print("\n" + "=" * 80)
