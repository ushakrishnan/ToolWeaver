"""
Tool Search Engine for ToolWeaver

Implements hybrid search for intelligent tool selection:
- BM25 (keyword-based)
- Semantic embeddings (concept-based)
- Weighted combination for optimal results

Phase 3 Implementation
"""

import os
import time
import pickle
import hashlib
import logging
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

from typing import cast
import numpy as np  # type: ignore[import-not-found]

try:
    from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
    SENTENCE_AVAILABLE = True
except Exception:  # ImportError or runtime env issues
    SentenceTransformer = None  # type: ignore[assignment]
    SENTENCE_AVAILABLE = False

try:
    from rank_bm25 import BM25Okapi  # type: ignore[import-not-found]
    BM25_AVAILABLE = True
except Exception:
    BM25_AVAILABLE = False

from ..shared.models import ToolCatalog, ToolDefinition

logger = logging.getLogger(__name__)


class ToolSearchEngine:
    """
    Hybrid search engine for tool discovery.
    
    Combines:
    - BM25 (keyword matching) for exact/technical terms
    - Embeddings (semantic similarity) for conceptual matches
    
    Features:
    - Smart routing: Skip search for small catalogs (<20 tools)
    - Embedding caching: Avoid recomputation
    - Query caching: Fast repeated searches
    - Configurable weights for hybrid scoring
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",  # Fast, 384-dim, 80MB
        bm25_weight: float = 0.3,
        embedding_weight: float = 0.7,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize search engine.
        
        Args:
            embedding_model: SentenceTransformer model name
            bm25_weight: Weight for BM25 keyword scores (0-1)
            embedding_weight: Weight for embedding scores (0-1)
            cache_dir: Directory for caching embeddings and results
        """
        self.embedding_model_name = embedding_model
        self.embedding_model: Optional[Any] = None  # Lazy load
        self.bm25_weight = bm25_weight
        self.embedding_weight = embedding_weight
        
        # Set up cache directory
        self.cache_dir = cache_dir or Path.home() / ".toolweaver" / "search_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            f"ToolSearchEngine initialized (BM25: {bm25_weight:.1f}, "
            f"Embedding: {embedding_weight:.1f})"
        )
    
    def _init_embedding_model(self) -> None:
        """Lazy initialization of embedding model if available."""
        if self.embedding_model is None:
            if not SENTENCE_AVAILABLE:
                logger.warning("SentenceTransformer not installed; embedding search disabled.")
                return
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)  # type: ignore[misc]
            logger.info(
                f"Embedding model loaded (dim={self.embedding_model.get_sentence_embedding_dimension()})"
            )
    
    def search(
        self,
        query: str,
        catalog: ToolCatalog,
        top_k: int = 5,
        min_score: float = 0.3,
        *,
        domain: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> List[Tuple[ToolDefinition, float]]:
        """
        Search for relevant tools using hybrid approach.
        
        Args:
            query: User's natural language request
            catalog: Tool catalog to search
            top_k: Number of tools to return
            min_score: Minimum relevance score (0-1)
        
        Returns:
            List of (ToolDefinition, score) tuples, sorted by relevance
        
        Example:
            results = search_engine.search(
                "Send a Slack message",
                catalog,
                top_k=5
            )
            for tool, score in results:
                print(f"{tool.name}: {score:.2f}")
        """
        tools = [
            t for t in catalog.tools.values()
            if (domain is None or t.domain == domain)
            and (type_filter is None or t.type == type_filter)
        ]
        
        if len(tools) == 0:
            logger.warning("No tools available after filtering")
            return []
        
        # Smart routing: Skip search if tool count is small
        if len(tools) <= 20:
            logger.info(f"Tool count ({len(tools)}) ≤ 20, returning filtered tools")
            return [(tool, 1.0) for tool in tools[:top_k]]
        
        # Check cache for this query + tool catalog hash
        cache_key = self._get_cache_key(query, catalog, domain=domain, type_filter=type_filter)
        cached_results = self._load_from_cache(cache_key)
        if cached_results:
            logger.info(f"Cache hit for query: '{query[:50]}...'")
            return cached_results[:top_k]
        
        # Perform hybrid search
        start_time = time.time()
        
        bm25_scores = self._bm25_search(query, tools)
        embedding_scores = self._embedding_search(query, tools)
        
        # Combine scores with weighted average
        combined_scores = []
        for i, tool in enumerate(tools):
            combined_score = (
                self.bm25_weight * bm25_scores[i] +
                self.embedding_weight * embedding_scores[i]
            )
            if combined_score >= min_score:
                combined_scores.append((tool, combined_score))
        
        # Sort by score descending
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        results = combined_scores[:top_k]
        
        search_duration_ms = (time.time() - start_time) * 1000
        
        # Cache results
        self._save_to_cache(cache_key, results)
        
        logger.info(
            f"Search '{query[:40]}...' found {len(results)}/{len(tools)} tools "
            f"in {search_duration_ms:.0f}ms (top scores: {[f'{s:.2f}' for _, s in results[:3]]})"
        )
        
        return results
    
    def _bm25_search(self, query: str, tools: List[ToolDefinition]) -> np.ndarray:
        """
        BM25 keyword-based search (good for exact matches).
        
        Tokenizes tool descriptions and uses TF-IDF-like scoring
        to find tools matching query keywords.
        """
        # Build corpus from tool descriptions
        corpus = []
        for tool in tools:
            # Combine name, description, and parameter descriptions
            param_text = " ".join(p.description for p in tool.parameters)
            tool_text = f"{tool.name} {tool.description} {param_text}"
            corpus.append(tool_text)
        
        # Tokenize corpus (simple whitespace split + lowercase)
        tokenized_corpus = [doc.lower().split() for doc in corpus]
        
        # Build BM25 index (fallback to zeros if unavailable)
        if not BM25_AVAILABLE:
            return np.zeros(len(tokenized_corpus), dtype=float)
        bm25 = BM25Okapi(tokenized_corpus)  # type: ignore[misc]
        
        # Search
        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)
        
        # Normalize to 0-1 range
        max_score = max(scores) if max(scores) > 0 else 1.0
        normalized_scores = scores / max_score
        
        return normalized_scores
    
    def _embedding_search(self, query: str, tools: List[ToolDefinition]) -> np.ndarray:
        """
        Embedding-based semantic search (good for conceptual matches).
        
        Uses SentenceTransformer to encode query and tools into dense
        vectors, then computes cosine similarity.
        """
        self._init_embedding_model()
        if self.embedding_model is None:
            return np.zeros(len(tools), dtype=float)
        
        # Get query embedding
        query_embedding = self.embedding_model.encode(query, convert_to_tensor=False)  # type: ignore[union-attr]
        
        # Get tool embeddings (with caching)
        tool_embeddings = []
        for tool in tools:
            # Use name + description for embedding
            tool_text = f"{tool.name}: {tool.description}"
            embedding = self._get_or_compute_embedding(tool_text)
            tool_embeddings.append(embedding)
        
        tool_embeddings = np.array(tool_embeddings)
        
        # Compute cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        tool_norms = tool_embeddings / np.linalg.norm(tool_embeddings, axis=1, keepdims=True)
        similarities = np.dot(tool_norms, query_norm)
        
        # Convert from [-1, 1] to [0, 1] range
        normalized_similarities = (similarities + 1) / 2
        
        return normalized_similarities
    
    def _get_or_compute_embedding(self, text: str) -> np.ndarray:
        """
        Get cached embedding or compute and cache it.
        
        Uses MD5 hash of text as cache key to avoid recomputing
        embeddings for the same tool descriptions.
        """
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_file = self.cache_dir / f"emb_{text_hash}.npy"
        
        if cache_file.exists():
            return np.load(cache_file)
        
        # Compute embedding
        if self.embedding_model is None:
            # Should not happen due to guards; return zeros for safety
            return np.zeros(0, dtype=float)
        embedding = self.embedding_model.encode(text, convert_to_tensor=False)  # type: ignore[union-attr]
        
        # Save to cache
        np.save(cache_file, embedding)
        
        return embedding
    
    def _get_cache_key(
        self,
        query: str,
        catalog: ToolCatalog,
        *,
        domain: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> str:
        """Generate cache key from query, catalog, and filters"""
        # Hash catalog based on tool names (stable across runs)
        catalog_hash = hashlib.md5(
            str(sorted(catalog.tools.keys())).encode()
        ).hexdigest()
        
        # Hash query + filters
        filter_blob = f"{query}|{domain or ''}|{type_filter or ''}"
        query_hash = hashlib.md5(filter_blob.encode()).hexdigest()
        
        return f"{query_hash}_{catalog_hash}"
    
    def _load_from_cache(self, cache_key: str) -> Optional[List[Tuple[ToolDefinition, float]]]:
        """Load cached search results if fresh (<1 hour)"""
        cache_file = self.cache_dir / f"search_{cache_key}.pkl"
        
        if cache_file.exists():
            # Check if cache is fresh (< 1 hour old)
            age_seconds = time.time() - cache_file.stat().st_mtime
            if age_seconds < 3600:  # 1 hour TTL
                try:
                    with open(cache_file, "rb") as f:
                            loaded = pickle.load(f)
                            return cast(List[Tuple[ToolDefinition, float]], loaded)
                except Exception as e:
                    logger.warning(f"Failed to load cache {cache_key}: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, results: List[Tuple[ToolDefinition, float]]) -> None:
        """Save search results to cache"""
        cache_file = self.cache_dir / f"search_{cache_key}.pkl"
        
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(results, f)
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_key}: {e}")
    
    def explain_results(
        self,
        query: str,
        results: List[Tuple[ToolDefinition, float]]
    ) -> str:
        """
        Generate human-readable explanation of why tools were selected.
        
        Useful for debugging and understanding search results.
        """
        lines = [f"Search results for: '{query}'\n"]
        
        for i, (tool, score) in enumerate(results, 1):
            relevance = (
                "🔥 Highly relevant" if score > 0.8 else
                "✓ Relevant" if score > 0.6 else
                "~ Somewhat relevant"
            )
            
            lines.append(
                f"{i}. {tool.name} (score: {score:.2f}) {relevance}\n"
                f"   Type: {tool.type}\n"
                f"   Description: {tool.description[:80]}...\n"
            )
        
        if not results:
            lines.append("No relevant tools found. Try a different query.")
        
        return "\n".join(lines)
    
    def clear_cache(self) -> None:
        """Clear all cached embeddings and search results"""
        if self.cache_dir.exists():
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True)
            logger.info("Search cache cleared")


# Convenience function
def search_tools(
    query: str,
    catalog: ToolCatalog,
    top_k: int = 5,
    domain: Optional[str] = None,
    type_filter: Optional[str] = None,
    **kwargs
) -> List[ToolDefinition]:
    """
    Convenience function to search tools and return only ToolDefinitions.
    
    Args:
        query: Natural language query
        catalog: Tool catalog to search
        top_k: Number of results
        domain: Optional domain filter
        type_filter: Optional tool type filter
        **kwargs: Additional arguments for ToolSearchEngine
    
    Returns:
        List of ToolDefinitions (without scores)
    
    Example:
        tools = search_tools("send slack message", catalog, top_k=3)
        for tool in tools:
            print(tool.name)
    """
    engine = ToolSearchEngine(**kwargs)
    results = engine.search(
        query,
        catalog,
        top_k=top_k,
        domain=domain,
        type_filter=type_filter,
    )
    return [tool for tool, score in results]
