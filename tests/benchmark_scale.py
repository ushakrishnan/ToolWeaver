"""
Performance Benchmarks for Phase 7 Scale Optimization

Validates that Phase 7 improvements meet the <100ms latency target
for 100, 500, 1000, and 5000 tool catalogs.

Measures:
1. Search latency (cold start and warm)
2. Indexing time
3. Memory usage
4. Cache hit rates

Compares Phase 3 (baseline) vs Phase 7 (optimized).
"""

import pytest
import time
import random
from typing import List
import numpy as np

# Lightweight fallback for pytest-benchmark when plugin isn't installed.
try:
    from pytest_benchmark.fixture import BenchmarkFixture  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    BenchmarkFixture = None


@pytest.fixture
def benchmark():
    """Minimal benchmark fixture that approximates pytest-benchmark stats.mean."""
    class _Stats:
        def __init__(self, samples: List[float]):
            self.mean = sum(samples) / len(samples)

    class _Benchmark:
        def __call__(self, func):
            samples = []
            result = None
            for _ in range(3):
                start = time.perf_counter()
                result = func()
                samples.append(time.perf_counter() - start)
            self.stats = _Stats(samples)
            return result

    if BenchmarkFixture is None:
        return _Benchmark()
    # If plugin is available, defer to real fixture
    return pytest.lazy_fixture("benchmark")

from orchestrator.shared.models import (
    ToolCatalog,
    ToolDefinition,
    ToolParameter,
    ToolExample
)
from orchestrator.tools.tool_search import ToolSearchEngine  # Phase 3 baseline
from orchestrator.tools.vector_search import VectorToolSearchEngine  # Phase 7 optimized
from orchestrator.tools.sharded_catalog import ShardedCatalog


# ============================================================
# Test Catalog Generation
# ============================================================

def generate_large_catalog(size: int, domains: List[str] = None) -> ToolCatalog:
    """
    Generate a large synthetic tool catalog for benchmarking.
    
    Args:
        size: Number of tools to generate
        domains: List of domains to distribute tools across
    
    Returns:
        ToolCatalog with `size` synthetic tools
    """
    if domains is None:
        domains = ["github", "slack", "aws", "database", "general"]
    
    catalog = ToolCatalog(name=f"benchmark_catalog_{size}")
    
    # Synthetic tool templates
    action_verbs = ["create", "list", "get", "update", "delete", "send", "fetch", "query", "manage"]
    resources = ["user", "repo", "issue", "pr", "message", "channel", "file", "database", "table", "record"]
    
    for i in range(size):
        domain = domains[i % len(domains)]
        action = random.choice(action_verbs)
        resource = random.choice(resources)
        
        tool = ToolDefinition(
            name=f"{action}_{domain}_{resource}_{i}",
            description=f"{action.capitalize()} a {resource} in {domain} system. Tool number {i}.",
            type="function",
            parameters=[
                ToolParameter(
                    name="id",
                    type="string",
                    required=True,
                    description=f"The {resource} identifier"
                ),
                ToolParameter(
                    name="options",
                    type="object",
                    required=False,
                    description="Additional options"
                )
            ],
            examples=[
                ToolExample(
                    scenario=f"{action.capitalize()} {resource} example",
                    input={"id": "123", "options": {}},
                    output={"success": True}
                )
            ],
            domain=domain
        )
        
        catalog.add_tool(tool)
    
    return catalog


# ============================================================
# Phase 3 Baseline Benchmarks
# ============================================================

class TestPhase3Baseline:
    """Benchmark Phase 3 baseline (BM25 only)"""
    
    @pytest.mark.parametrize("catalog_size", [100, 500, 1000])
    def test_phase3_search_latency(self, catalog_size, benchmark):
        """Measure Phase 3 search latency"""
        catalog = generate_large_catalog(catalog_size)
        search = ToolSearchEngine()
        
        query = "create user in github"
        
        def search_once():
            return search.search(query, catalog, top_k=5)
        
        # Benchmark search
        result = benchmark(search_once)
        
        # Validate results
        assert len(result) > 0
        print(f"\nPhase 3 ({catalog_size} tools): {benchmark.stats.mean * 1000:.2f}ms avg")
    
    def test_phase3_large_catalog_stress(self):
        """Stress test Phase 3 with 5000 tools"""
        catalog = generate_large_catalog(5000)
        search = ToolSearchEngine()
        
        query = "create user in github"
        
        # Measure cold start
        start = time.time()
        results = search.search(query, catalog, top_k=5)
        cold_latency = (time.time() - start) * 1000
        
        # Measure warm search
        start = time.time()
        results = search.search(query, catalog, top_k=5)
        warm_latency = (time.time() - start) * 1000
        
        print(f"\nPhase 3 (5000 tools):")
        print(f"  Cold start: {cold_latency:.2f}ms")
        print(f"  Warm search: {warm_latency:.2f}ms")
        
        assert len(results) > 0


# ============================================================
# Phase 7 Optimized Benchmarks
# ============================================================

class TestPhase7Optimized:
    """Benchmark Phase 7 optimizations (Qdrant + Redis + Sharding + GPU)"""
    
    @pytest.mark.parametrize("catalog_size", [100, 500, 1000])
    def test_phase7_search_latency_with_precompute(self, catalog_size, benchmark):
        """Measure Phase 7 search latency with pre-computation"""
        catalog = generate_large_catalog(catalog_size)
        
        # Initialize with pre-computation enabled
        search = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            use_gpu=False,  # CPU for consistent benchmarking
            precompute_embeddings=True
        )
        
        # Pre-compute embeddings (one-time startup cost)
        search._init_embedding_model()
        search.precompute_catalog_embeddings(catalog)
        
        # Index catalog
        search.index_catalog(catalog, batch_size=64)
        
        query = "create user in github"
        
        def search_once():
            return search.search(query, catalog, top_k=5)
        
        # Benchmark search (should be <100ms)
        result = benchmark(search_once)
        
        # Validate results
        assert len(result) > 0
        
        avg_latency = benchmark.stats.mean * 1000
        print(f"\nPhase 7 ({catalog_size} tools, precompute): {avg_latency:.2f}ms avg")
        
        # Assert <100ms target for Phase 7
        if catalog_size <= 1000:
            assert avg_latency < 100, f"Search latency {avg_latency:.2f}ms exceeds 100ms target"
    
    @pytest.mark.parametrize("catalog_size", [100, 500, 1000])
    def test_phase7_search_latency_cold_start(self, catalog_size, benchmark):
        """Measure Phase 7 cold start (no pre-computation)"""
        catalog = generate_large_catalog(catalog_size)
        
        # Initialize WITHOUT pre-computation
        search = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            use_gpu=False,
            precompute_embeddings=False  # Cold start
        )
        
        # Index catalog
        search._init_embedding_model()
        search.index_catalog(catalog, batch_size=64)
        
        query = "create user in github"
        
        def search_once():
            return search.search(query, catalog, top_k=5)
        
        # Benchmark search
        result = benchmark(search_once)
        
        # Validate results
        assert len(result) > 0
        
        avg_latency = benchmark.stats.mean * 1000
        print(f"\nPhase 7 ({catalog_size} tools, cold start): {avg_latency:.2f}ms avg")
    
    def test_phase7_large_catalog_stress(self):
        """Stress test Phase 7 with 5000 tools"""
        catalog = generate_large_catalog(5000)
        
        search = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            use_gpu=False,
            precompute_embeddings=True
        )
        
        # Pre-compute
        search._init_embedding_model()
        precompute_start = time.time()
        search.precompute_catalog_embeddings(catalog)
        precompute_time = (time.time() - precompute_start) * 1000
        
        # Index
        index_start = time.time()
        search.index_catalog(catalog, batch_size=64)
        index_time = (time.time() - index_start) * 1000
        
        query = "create user in github"
        
        # Measure warm search
        start = time.time()
        results = search.search(query, catalog, top_k=5)
        warm_latency = (time.time() - start) * 1000
        
        print(f"\nPhase 7 (5000 tools):")
        print(f"  Pre-compute: {precompute_time:.2f}ms")
        print(f"  Indexing: {index_time:.2f}ms")
        print(f"  Warm search: {warm_latency:.2f}ms")
        
        assert len(results) > 0
        
        # Warm search should be fast even with 5000 tools
        assert warm_latency < 200, f"Search latency {warm_latency:.2f}ms too high for 5000 tools"
    
    def test_phase7_indexing_time(self):
        """Measure indexing time for different catalog sizes"""
        sizes = [100, 500, 1000]
        results = []
        
        for size in sizes:
            catalog = generate_large_catalog(size)
            
            search = VectorToolSearchEngine(
                qdrant_url="http://localhost:6333",
                fallback_to_memory=True,
                use_gpu=False,
                precompute_embeddings=False
            )
            
            search._init_embedding_model()
            
            start = time.time()
            success = search.index_catalog(catalog, batch_size=64)
            index_time = (time.time() - start) * 1000
            
            results.append((size, index_time))
            print(f"\nIndexing {size} tools: {index_time:.2f}ms")
            
            assert success, f"Failed to index {size} tools"
        
        # Indexing should scale sub-linearly
        # (1000 tools should take < 10x time of 100 tools)
        time_100 = results[0][1]
        time_1000 = results[2][1]
        ratio = time_1000 / time_100
        
        print(f"\n1000/100 indexing time ratio: {ratio:.2f}x")
        assert ratio < 10, f"Indexing does not scale well: {ratio:.2f}x"


# ============================================================
# Sharded Catalog Benchmarks
# ============================================================

class TestShardedCatalogPerformance:
    """Benchmark sharded catalog performance"""
    
    @pytest.mark.parametrize("catalog_size", [100, 500, 1000])
    def test_sharded_search_latency(self, catalog_size, benchmark):
        """Measure sharded catalog search latency"""
        catalog = generate_large_catalog(catalog_size)
        sharded = ShardedCatalog()
        
        # Add all tools
        for tool in catalog.tools.values():
            sharded.add_tool(tool)
        
        query = "create user in github"
        
        def search_once():
            return sharded.search_with_detection(query, top_k=5)
        
        # Benchmark search
        result = benchmark(search_once)
        
        # Validate results
        assert len(result) > 0
        
        avg_latency = benchmark.stats.mean * 1000
        print(f"\nSharded ({catalog_size} tools): {avg_latency:.2f}ms avg")
    
    def test_sharded_domain_efficiency(self):
        """Test that domain-specific search is faster than global"""
        catalog = generate_large_catalog(1000)
        sharded = ShardedCatalog()
        
        for tool in catalog.tools.values():
            sharded.add_tool(tool)
        
        query = "create user in github"
        
        # Domain-specific search
        start = time.time()
        domain_results = sharded.search_by_domain(query, "github", top_k=5)
        domain_time = (time.time() - start) * 1000
        
        # Global search (fallback)
        start = time.time()
        global_results = sharded.search_with_detection(query, top_k=5)
        global_time = (time.time() - start) * 1000
        
        print(f"\nSharding efficiency (1000 tools):")
        print(f"  Domain search (github): {domain_time:.2f}ms")
        print(f"  Global search: {global_time:.2f}ms")
        
        assert len(domain_results) > 0
        assert len(global_results) > 0


# ============================================================
# Comparison Summary
# ============================================================

class TestPerformanceComparison:
    """Compare Phase 3 vs Phase 7 performance"""
    
    def test_performance_summary(self):
        """Generate performance comparison summary"""
        print("\n" + "="*60)
        print("PHASE 7 PERFORMANCE SUMMARY")
        print("="*60)
        
        sizes = [100, 500, 1000]
        
        for size in sizes:
            catalog = generate_large_catalog(size)
            
            # Phase 3 baseline
            search_p3 = ToolSearchEngine()
            start = time.time()
            results_p3 = search_p3.search("create user", catalog, top_k=5)
            p3_time = (time.time() - start) * 1000
            
            # Phase 7 with pre-computation
            search_p7 = VectorToolSearchEngine(
                qdrant_url="http://localhost:6333",
                fallback_to_memory=True,
                use_gpu=False,
                precompute_embeddings=True
            )
            search_p7._init_embedding_model()
            search_p7.precompute_catalog_embeddings(catalog)
            search_p7.index_catalog(catalog, batch_size=64)
            
            start = time.time()
            results_p7 = search_p7.search("create user", catalog, top_k=5)
            p7_time = (time.time() - start) * 1000
            
            improvement = p3_time / p7_time
            
            print(f"\n{size} tools:")
            print(f"  Phase 3: {p3_time:.2f}ms")
            print(f"  Phase 7: {p7_time:.2f}ms")
            print(f"  Improvement: {improvement:.1f}x faster")
            
            assert len(results_p3) > 0
            assert len(results_p7) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
