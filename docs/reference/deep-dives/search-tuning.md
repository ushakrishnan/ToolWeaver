# Search Tuning

Hybrid retrieval (BM25 + embeddings) drives tool selection.

Levers
- Domain filter: narrow early when the request is scoped.
- Top-k: balance recall vs token cost (e.g., 5–10 tools to planner).
- Embedding model: 384-dim (MiniLM) by default; larger models for nuance at higher cost.
- Thresholds: drop low-similarity hits to avoid planner confusion.

Caching
- Cache discovery results for common queries to reduce latency and token use.

Evaluation
- Track hit quality and planner success rates; adjust thresholds and top-k accordingly.
