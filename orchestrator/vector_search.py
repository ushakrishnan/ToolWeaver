"""Shim module for backwards compatibility.

Tries to re-export the full Qdrant-backed engine. If optional deps are missing,
provides a lightweight in-memory fallback that matches the tested API.
"""
import logging
logger = logging.getLogger(__name__)

try:
    from .tools.vector_search import VectorToolSearchEngine as _FullVectorToolSearchEngine
    VectorToolSearchEngine = _FullVectorToolSearchEngine
except Exception as e:
    logger.warning(f"Falling back to in-memory VectorToolSearchEngine due to import error: {e}")
    from typing import List, Tuple, Optional
    import time

    from .models import ToolCatalog, ToolDefinition

    class VectorToolSearchEngine:
        def __init__(
            self,
            qdrant_url: str = "http://localhost:6333",
            collection_name: str = "toolweaver_tools",
            embedding_dim: int = 384,
            fallback_to_memory: bool = True
        ):
            self.qdrant_url = qdrant_url
            self.collection_name = collection_name
            self.embedding_dim = embedding_dim
            self.fallback_to_memory = fallback_to_memory
            self.embedding_model = None  # Lazy load
            # Memory fallback storage
            self.memory_embeddings: List[Tuple[str, set]] = []  # (tool_name, token_set)
            self.memory_tools: List[ToolDefinition] = []

        def _init_embedding_model(self):
            # No heavy model, mark as loaded
            self.embedding_model = "fallback"

        def index_catalog(self, catalog: ToolCatalog, batch_size: int = 64) -> bool:
            # Use memory embedding fallback
            tools = list(catalog.tools.values())
            if len(tools) == 0:
                return False
            self._init_embedding_model()
            self.memory_embeddings.clear()
            self.memory_tools = tools
            for tool in tools:
                text = f"{tool.name} {tool.description}"
                tokens = set(text.lower().split())
                self.memory_embeddings.append((tool.name, tokens))
            return True

        def search(
            self,
            query: str,
            catalog: ToolCatalog,
            top_k: int = 5,
            domain: Optional[str] = None,
            min_score: float = 0.3
        ) -> List[Tuple[ToolDefinition, float]]:
            # Ensure indexed
            if not self.memory_tools:
                self.index_catalog(catalog)
            q_tokens = set(query.lower().split())
            candidates = self.memory_tools
            if domain:
                candidates = [t for t in candidates if t.domain == domain]
            scored: List[Tuple[ToolDefinition, float]] = []
            for tool in candidates:
                t_tokens = set((f"{tool.name} {tool.description}").lower().split())
                inter = len(q_tokens & t_tokens)
                union = len(q_tokens | t_tokens) or 1
                sim = inter / union
                if sim >= min_score:
                    scored.append((tool, float(sim)))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]

    __all__ = ["VectorToolSearchEngine"]
