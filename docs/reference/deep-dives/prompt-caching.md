# Prompt Caching

Multi-layer caching to cut cost and latency.

Layers
- Tool discovery cache: serialized tool metadata for fast lookup.
- Embedding cache: reuse embeddings for repeated tool texts.
- Query cache: reuse search results for recurring queries.
- LLM prompt cache: provider-side (Anthropic/OpenAI) discounts for repeated prompts/tooldefs.

Guidelines
- Tune TTLs per layer: short for queries, longer for embeddings and tool defs.
- Normalize tool definitions to maximize cache hits.
- Log cache hit rates; adjust before scaling traffic.
