"""
Pluggable monitoring backends for ToolWeaver observability.

Supports multiple backends:
- Local: File-based logging (default, no dependencies)
- W&B: Weights & Biases for ML experiment tracking (optional)
- Prometheus: Metrics export for production monitoring (optional)
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Protocol
from datetime import datetime, timezone
from abc import ABC, abstractmethod


class MonitoringBackend(Protocol):
    """Interface for monitoring backends."""
    
    def log_tool_call(
        self,
        tool_name: str,
        success: bool,
        latency: float,
        error: Optional[str] = None,
        execution_id: Optional[str] = None
    ):
        """Log individual tool call."""
        ...
    
    def log_search_query(
        self,
        query: str,
        num_results: int,
        latency: float,
        cache_hit: bool = False
    ):
        """Log tool search query."""
        ...
    
    def log_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ):
        """Log LLM token usage."""
        ...
    
    def flush(self):
        """Flush any buffered data."""
        ...


class LocalBackend:
    """
    Local file-based monitoring backend (default).
    
    Logs to JSONL files in log directory.
    Zero external dependencies, works offline.
    """
    
    def __init__(self, log_dir: str = ".tool_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
    
    def log_tool_call(
        self,
        tool_name: str,
        success: bool,
        latency: float,
        error: Optional[str] = None,
        execution_id: Optional[str] = None
    ):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool_name": tool_name,
            "success": success,
            "latency": latency,
            "error": error,
            "execution_id": execution_id
        }
        self._write_log("tool_calls", entry)
    
    def log_search_query(
        self,
        query: str,
        num_results: int,
        latency: float,
        cache_hit: bool = False
    ):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "num_results": num_results,
            "latency": latency,
            "cache_hit": cache_hit
        }
        self._write_log("search_queries", entry)
    
    def log_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input": input_tokens,
            "output": output_tokens,
            "cached": cached_tokens
        }
        self._write_log("token_usage", entry)
    
    def flush(self):
        """No buffering for local backend."""
        pass
    
    def _write_log(self, log_type: str, entry: Dict[str, Any]):
        """Write log entry to daily JSONL file."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = Path(self.log_dir) / f"{log_type}_{date_str}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')


class WandbBackend:
    """
    Weights & Biases monitoring backend (optional).
    
    Requires: pip install wandb
    Requires: WANDB_API_KEY environment variable
    
    Benefits:
    - Beautiful dashboards
    - Experiment comparison
    - Team collaboration
    - Version tracking
    """
    
    def __init__(
        self,
        project: str = "toolweaver",
        entity: Optional[str] = None,
        run_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        try:
            import wandb
            self.wandb = wandb
        except ImportError:
            raise ImportError(
                "W&B backend requires wandb package. "
                "Install with: pip install wandb"
            )
        
        # Initialize run
        self.run = wandb.init(
            project=project,
            entity=entity,
            name=run_name,
            config=config or {},
            resume="allow"
        )
        
        # Counters for aggregation
        self.step = 0
    
    def log_tool_call(
        self,
        tool_name: str,
        success: bool,
        latency: float,
        error: Optional[str] = None,
        execution_id: Optional[str] = None
    ):
        self.wandb.log({
            f"tool/{tool_name}/latency": latency,
            f"tool/{tool_name}/success": 1 if success else 0,
            f"tool/{tool_name}/error": 0 if success else 1,
            "step": self.step
        })
        
        if error:
            self.wandb.alert(
                title=f"Tool Error: {tool_name}",
                text=error,
                level=self.wandb.AlertLevel.WARN
            )
        
        self.step += 1
    
    def log_search_query(
        self,
        query: str,
        num_results: int,
        latency: float,
        cache_hit: bool = False
    ):
        self.wandb.log({
            "search/latency": latency,
            "search/results": num_results,
            "search/cache_hit": 1 if cache_hit else 0,
            "step": self.step
        })
        self.step += 1
    
    def log_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ):
        total = input_tokens + output_tokens
        
        self.wandb.log({
            "tokens/input": input_tokens,
            "tokens/output": output_tokens,
            "tokens/cached": cached_tokens,
            "tokens/total": total,
            "tokens/cache_rate": cached_tokens / (total + cached_tokens) if (total + cached_tokens) > 0 else 0,
            "step": self.step
        })
        self.step += 1
    
    def flush(self):
        """Flush W&B logs."""
        if self.run:
            self.run.finish()


class PrometheusBackend:
    """
    Prometheus metrics backend (optional).
    
    Requires: pip install prometheus-client
    
    Exposes metrics on HTTP endpoint for Prometheus scraping.
    Ideal for production Kubernetes/Docker deployments.
    
    Metrics exposed:
    - toolweaver_tool_calls_total (counter)
    - toolweaver_tool_errors_total (counter)
    - toolweaver_tool_latency_seconds (histogram)
    - toolweaver_search_queries_total (counter)
    - toolweaver_cache_hits_total (counter)
    - toolweaver_tokens_total (counter)
    """
    
    def __init__(self, port: int = 8000):
        try:
            from prometheus_client import Counter, Histogram, start_http_server
            self.Counter = Counter
            self.Histogram = Histogram
        except ImportError:
            raise ImportError(
                "Prometheus backend requires prometheus-client package. "
                "Install with: pip install prometheus-client"
            )
        
        # Define metrics
        self.tool_calls = Counter(
            'toolweaver_tool_calls_total',
            'Total tool calls',
            ['tool_name', 'success']
        )
        
        self.tool_errors = Counter(
            'toolweaver_tool_errors_total',
            'Total tool errors',
            ['tool_name']
        )
        
        self.tool_latency = Histogram(
            'toolweaver_tool_latency_seconds',
            'Tool execution latency',
            ['tool_name'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
        )
        
        self.search_queries = Counter(
            'toolweaver_search_queries_total',
            'Total search queries',
            ['cache_hit']
        )
        
        self.cache_hits = Counter(
            'toolweaver_cache_hits_total',
            'Cache hits',
            ['type']
        )
        
        self.tokens = Counter(
            'toolweaver_tokens_total',
            'LLM tokens used',
            ['type']
        )
        
        # Start HTTP server for Prometheus scraping
        try:
            start_http_server(port)
            print(f"✅ Prometheus metrics server started on port {port}")
        except OSError:
            print(f"⚠️  Port {port} already in use, metrics server not started")
    
    def log_tool_call(
        self,
        tool_name: str,
        success: bool,
        latency: float,
        error: Optional[str] = None,
        execution_id: Optional[str] = None
    ):
        self.tool_calls.labels(
            tool_name=tool_name,
            success=str(success)
        ).inc()
        
        if not success:
            self.tool_errors.labels(tool_name=tool_name).inc()
        
        self.tool_latency.labels(tool_name=tool_name).observe(latency)
    
    def log_search_query(
        self,
        query: str,
        num_results: int,
        latency: float,
        cache_hit: bool = False
    ):
        self.search_queries.labels(
            cache_hit=str(cache_hit)
        ).inc()
        
        if cache_hit:
            self.cache_hits.labels(type="search").inc()
    
    def log_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ):
        self.tokens.labels(type="input").inc(input_tokens)
        self.tokens.labels(type="output").inc(output_tokens)
        self.tokens.labels(type="cached").inc(cached_tokens)
    
    def flush(self):
        """Prometheus metrics are always available via HTTP."""
        pass


def create_backend(backend_type: str, **kwargs) -> MonitoringBackend:
    """
    Factory function to create monitoring backends.
    
    Args:
        backend_type: "local", "wandb", or "prometheus"
        **kwargs: Backend-specific configuration
        
    Returns:
        MonitoringBackend instance
        
    Examples:
        # Local (default)
        backend = create_backend("local", log_dir=".tool_logs")
        
        # W&B
        backend = create_backend("wandb", project="my-project")
        
        # Prometheus
        backend = create_backend("prometheus", port=8000)
    """
    if backend_type == "local":
        return LocalBackend(**kwargs)
    elif backend_type == "wandb":
        return WandbBackend(**kwargs)
    elif backend_type == "prometheus":
        return PrometheusBackend(**kwargs)
    else:
        raise ValueError(f"Unknown backend type: {backend_type}")
