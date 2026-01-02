"""
Unit tests for tool usage monitoring (Phase 5: Monitoring).

Tests cover:
- Tool call logging
- Search query tracking
- Token usage tracking
- Metrics aggregation
- Error tracking
- Export functionality
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from orchestrator._internal.observability.monitoring import (
    ToolUsageMonitor,
    create_monitor,
    print_metrics_report,
)


@pytest.fixture
def temp_log_dir():
    """Create temporary log directory."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def monitor(temp_log_dir):
    """Create monitor instance."""
    return ToolUsageMonitor(log_to_file=True, log_dir=temp_log_dir)


class TestBasicLogging:
    """Test basic logging functionality."""

    def test_log_successful_tool_call(self, monitor):
        """Test logging a successful tool call."""
        monitor.log_tool_call(
            tool_name="receipt_ocr",
            success=True,
            latency=0.5,
            execution_id="exec-001"
        )

        assert monitor.metrics["tool_calls"]["receipt_ocr"] == 1
        assert monitor.metrics["tool_errors"]["receipt_ocr"] == 0
        assert len(monitor.metrics["tool_latency"]["receipt_ocr"]) == 1
        assert monitor.metrics["tool_latency"]["receipt_ocr"][0] == 0.5

    def test_log_failed_tool_call(self, monitor):
        """Test logging a failed tool call."""
        monitor.log_tool_call(
            tool_name="parse_line_items",
            success=False,
            latency=0.2,
            error="Invalid input format"
        )

        assert monitor.metrics["tool_calls"]["parse_line_items"] == 1
        assert monitor.metrics["tool_errors"]["parse_line_items"] == 1
        assert len(monitor.tool_call_log) == 1
        assert monitor.tool_call_log[0].error == "Invalid input format"

    def test_log_search_query(self, monitor):
        """Test logging a search query."""
        monitor.log_search_query(
            query="process receipt image",
            num_results=5,
            latency=0.1,
            cache_hit=False
        )

        assert len(monitor.search_log) == 1
        assert monitor.metrics["cache_misses"] == 1
        assert monitor.search_log[0].query == "process receipt image"

    def test_log_token_usage(self, monitor):
        """Test logging token usage."""
        monitor.log_token_usage(
            input_tokens=100,
            output_tokens=50,
            cached_tokens=200
        )

        assert monitor.metrics["token_usage"]["input"] == 100
        assert monitor.metrics["token_usage"]["output"] == 50
        assert monitor.metrics["token_usage"]["cached"] == 200


class TestMetricsAggregation:
    """Test metrics aggregation."""

    def test_get_tool_metrics(self, monitor):
        """Test getting metrics for a specific tool."""
        # Log multiple calls
        monitor.log_tool_call("tool1", True, 0.1)
        monitor.log_tool_call("tool1", True, 0.2)
        monitor.log_tool_call("tool1", False, 0.3, error="Error")
        monitor.log_tool_call("tool1", True, 0.15)

        metrics = monitor.get_tool_metrics("tool1")

        assert metrics["total_calls"] == 4
        assert metrics["errors"] == 1
        assert metrics["error_rate"] == 0.25
        assert metrics["success_rate"] == 0.75
        assert metrics["latency"]["min"] == 0.1
        assert metrics["latency"]["max"] == 0.3
        assert 0.1 < metrics["latency"]["avg"] < 0.3

    def test_latency_percentiles(self, monitor):
        """Test latency percentile calculations."""
        # Log calls with known latencies
        for i in range(100):
            monitor.log_tool_call("test_tool", True, i / 1000)  # 0-99ms

        metrics = monitor.get_tool_metrics("test_tool")

        # p50 should be around 50ms
        assert 0.04 < metrics["latency"]["p50"] < 0.06
        # p95 should be around 95ms
        assert 0.09 < metrics["latency"]["p95"] < 0.1

    def test_get_summary(self, monitor):
        """Test overall summary generation."""
        # Log various activities
        monitor.log_tool_call("tool1", True, 0.1)
        monitor.log_tool_call("tool2", True, 0.2)
        monitor.log_tool_call("tool1", False, 0.3, error="Error")
        monitor.log_search_query("query", 5, 0.1, cache_hit=True)
        monitor.log_token_usage(100, 50, 200)

        summary = monitor.get_summary()

        assert summary["overview"]["total_tool_calls"] == 3
        assert summary["overview"]["total_errors"] == 1
        assert summary["overview"]["unique_tools"] == 2
        assert summary["overview"]["search_queries"] == 1
        assert summary["overview"]["cache_hit_rate"] == 1.0  # 1 hit, 0 misses

        assert "top_tools" in summary
        assert "token_usage" in summary
        assert "cache_performance" in summary


class TestErrorTracking:
    """Test error tracking functionality."""

    def test_recent_errors(self, monitor):
        """Test retrieving recent errors."""
        # Log successful and failed calls
        monitor.log_tool_call("tool1", True, 0.1)
        monitor.log_tool_call("tool2", False, 0.2, error="Error 1")
        monitor.log_tool_call("tool3", False, 0.3, error="Error 2")

        errors = monitor.get_recent_errors(limit=10)

        assert len(errors) == 2
        assert errors[0]["error"] == "Error 1"
        assert errors[1]["error"] == "Error 2"
        assert all(not e["success"] for e in errors)

    def test_recent_errors_limit(self, monitor):
        """Test recent errors respects limit."""
        # Log many errors
        for i in range(20):
            monitor.log_tool_call(f"tool{i}", False, 0.1, error=f"Error {i}")

        errors = monitor.get_recent_errors(limit=5)

        assert len(errors) == 5
        # Should get last 5 errors (15-19)
        assert errors[-1]["error"] == "Error 19"


class TestCacheMetrics:
    """Test cache performance tracking."""

    def test_cache_hit_rate(self, monitor):
        """Test cache hit rate calculation."""
        # Log cache hits and misses
        monitor.log_search_query("query1", 5, 0.1, cache_hit=True)
        monitor.log_search_query("query2", 5, 0.1, cache_hit=True)
        monitor.log_search_query("query3", 5, 0.1, cache_hit=False)

        summary = monitor.get_summary()
        cache = summary["cache_performance"]

        assert cache["hits"] == 2
        assert cache["misses"] == 1
        assert cache["hit_rate"] == 2/3  # 66.7%

    def test_empty_cache_metrics(self, monitor):
        """Test cache metrics when no searches logged."""
        summary = monitor.get_summary()

        assert summary["cache_performance"]["hit_rate"] == 0.0


class TestFileLogging:
    """Test file-based logging."""

    def test_log_file_creation(self, monitor, temp_log_dir):
        """Test log files are created."""
        monitor.log_tool_call("test_tool", True, 0.1)

        # Check log file exists
        log_files = list(Path(temp_log_dir).glob("tool_calls_*.jsonl"))
        assert len(log_files) == 1

        # Read and verify content
        with open(log_files[0]) as f:
            line = f.readline()
            entry = json.loads(line)
            assert entry["tool_name"] == "test_tool"
            assert entry["success"] is True

    def test_multiple_log_types(self, monitor, temp_log_dir):
        """Test different log types create separate files."""
        monitor.log_tool_call("tool1", True, 0.1)
        monitor.log_search_query("query", 5, 0.1)
        monitor.log_token_usage(100, 50)

        log_dir = Path(temp_log_dir)
        assert len(list(log_dir.glob("tool_calls_*.jsonl"))) == 1
        assert len(list(log_dir.glob("search_queries_*.jsonl"))) == 1
        assert len(list(log_dir.glob("token_usage_*.jsonl"))) == 1


class TestExport:
    """Test metrics export functionality."""

    def test_export_metrics(self, monitor, temp_log_dir):
        """Test exporting metrics to JSON."""
        # Log some data
        monitor.log_tool_call("tool1", True, 0.1)
        monitor.log_tool_call("tool2", False, 0.2, error="Error")
        monitor.log_search_query("query", 5, 0.1)
        monitor.log_token_usage(100, 50)

        # Export
        export_path = Path(temp_log_dir) / "metrics_export.json"
        monitor.export_metrics(str(export_path))

        # Verify
        assert export_path.exists()

        with open(export_path) as f:
            data = json.load(f)

        assert "summary" in data
        assert "tool_metrics" in data
        assert "recent_calls" in data
        assert "recent_searches" in data
        assert data["summary"]["overview"]["total_tool_calls"] == 2


class TestLogRotation:
    """Test log size limits."""

    def test_tool_call_log_rotation(self, monitor):
        """Test tool call log respects 1000 entry limit."""
        # Log 1500 calls
        for i in range(1500):
            monitor.log_tool_call(f"tool{i % 10}", True, 0.1)

        # Should only keep last 1000
        assert len(monitor.tool_call_log) == 1000

    def test_search_log_rotation(self, monitor):
        """Test search log respects 1000 entry limit."""
        # Log 1500 searches
        for i in range(1500):
            monitor.log_search_query(f"query{i}", 5, 0.1)

        # Should only keep last 1000
        assert len(monitor.search_log) == 1000


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_monitor(self, temp_log_dir):
        """Test create_monitor helper."""
        monitor = create_monitor(log_dir=temp_log_dir)

        assert isinstance(monitor, ToolUsageMonitor)
        assert monitor.log_to_file is True
        assert monitor.log_dir == temp_log_dir

    def test_print_metrics_report(self, monitor, capsys):
        """Test print_metrics_report helper."""
        # Log some data
        monitor.log_tool_call("tool1", True, 0.1)
        monitor.log_token_usage(100, 50, 200)

        # Print report
        print_metrics_report(monitor)

        # Verify output
        captured = capsys.readouterr()
        assert "TOOL USAGE MONITORING REPORT" in captured.out
        assert "Overview:" in captured.out
        assert "Top Tools:" in captured.out
        assert "Token Usage:" in captured.out


class TestTopTools:
    """Test top tools tracking."""

    def test_top_tools_ranking(self, monitor):
        """Test top tools are ranked by call count."""
        # Log calls with different frequencies
        for _i in range(10):
            monitor.log_tool_call("tool1", True, 0.1)
        for _i in range(5):
            monitor.log_tool_call("tool2", True, 0.1)
        for _i in range(3):
            monitor.log_tool_call("tool3", True, 0.1)

        summary = monitor.get_summary()
        top_tools = summary["top_tools"]

        assert len(top_tools) <= 5
        assert top_tools[0]["tool"] == "tool1"
        assert top_tools[0]["calls"] == 10
        assert top_tools[1]["tool"] == "tool2"
        assert top_tools[1]["calls"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
