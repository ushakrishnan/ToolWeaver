# Small Model Improvements

Use lightweight models for execution to save cost while keeping quality acceptable.

Guidelines
- Use small models (e.g., Phi-3, Llama variants) for extraction/classification/routing; keep large models for planning.
- Calibrate prompts for small models with few-shot examples; keep outputs structured.
- Cache aggressively when small models are deterministic enough.

When to fall back to large models
- Complex reasoning, synthesis, or when small model confidence drops.
- Cold-start scenarios without cached context.
