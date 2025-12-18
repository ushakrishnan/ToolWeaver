# Benchmarks

Benchmark suites live in `tests/benchmark_scale.py` and cover search, indexing, sharding, and phase-to-phase comparisons. This document explains how to run them and captures the latest baseline numbers.

## What is covered
- Phase 3 (BM25) search latency: cold/warm
- Phase 7 (vector) search latency: precomputed vs cold start
- Indexing throughput (100, 500, 1000 tools)
- Sharded catalog lookup latency and domain efficiency
- Phase 3 vs Phase 7 improvement summary

## Prerequisites
- Python environment with project dependencies installed (`pip install -r requirements.txt`)
- Optional: `pytest-benchmark` for richer metrics. If absent, a lightweight fallback fixture runs 3 samples and reports `stats.mean`.
- Optional: Qdrant at `http://localhost:6333`; the suite falls back to in-memory mode when unavailable.
- Hugging Face model downloads (e.g., `all-MiniLM-L6-v2`) occur on first run and can retry on transient network errors.

## How to run
- Quiet run (passes/failures only):
  ```bash
  python -m pytest tests/benchmark_scale.py -q
  ```
- Capture timings/prints (recommended for baselines):
  ```bash
  python -m pytest tests/benchmark_scale.py -s -q
  ```
- With pytest-benchmark installed, you can also use its reporting flags (e.g., `--benchmark-json`), but the suite will run without it.

## Latest baseline (2025-12-17, Windows, CPU, fallback benchmark fixture)
- Phase 3 search avg (BM25): 100→1550.05ms, 500→6178.77ms, 1000→14896.73ms; 5000 tools cold/warm: 200653.63ms / 83.92ms
- Phase 7 search avg (vector, precompute): 100→8.05ms, 500→5.62ms, 1000→4.84ms; 5000 warm: 27.48ms (precompute 40,537.44ms, index 9,514.83ms)
- Phase 7 search avg (vector, cold): 100→3.75ms, 500→12.26ms, 1000→17.59ms
- Indexing (vector): 100→9,218.19ms, 500→11,882.44ms, 1000→17,564.82ms (1000/100 ratio: 1.91x)
- Sharded catalog search avg: 100→0.02ms, 500→0.01ms, 1000→0.01ms; domain vs global (1000 tools): 0.01ms vs 0.03ms
- Phase 3 vs Phase 7 improvement (summary print): 100 tools→17.6x; 500→3189.2x; 1000→1485.9x (note: times reflect fallback fixture sampling and transient Hugging Face retries during model download)

## Notes
- Numbers above are from the fallback benchmark fixture (3 samples each) and should be treated as ballpark. Install `pytest-benchmark` and re-run for more statistically robust metrics.
- First runs may be slower due to model downloads and cache warm-up. Subsequent runs reuse local models.
