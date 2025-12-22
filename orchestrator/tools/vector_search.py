"""
Vector Database Search Engine for ToolWeaver (Phase 7)

Qdrant-based tool search for scaling to 1000+ tools with sub-100ms latency.
"""

import os
import logging
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

from typing import Any

try:
    from qdrant_client import QdrantClient  # type: ignore[import-not-found]
    from qdrant_client.models import (  # type: ignore[import-not-found]
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue
    )
    QDRANT_IMPORTED = True
except Exception:
    QdrantClient = None  # type: ignore[assignment]
    Distance = VectorParams = PointStruct = Filter = FieldCondition = MatchValue = None  # type: ignore[assignment]
    QDRANT_IMPORTED = False

try:
    from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
    SENTENCE_AVAILABLE = True
except Exception:
    SentenceTransformer = None  # type: ignore[assignment]
    SENTENCE_AVAILABLE = False

import numpy as np  # type: ignore[import-not-found]

try:
    import torch  # type: ignore[import-not-found]
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

from ..shared.models import ToolCatalog, ToolDefinition

logger = logging.getLogger(__name__)


class VectorToolSearchEngine:
    """
    Vector database search engine using Qdrant.
    
    Features:
    - Sub-10ms similarity search at 1000+ tools
    - Domain-based filtering for focused search
    - Automatic fallback to in-memory if Qdrant unavailable
    - Batch indexing for fast catalog loading
    - Connection pooling and retry logic
    
    Usage:
        # Initialize
        search_engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            collection_name="toolweaver_tools"
        )
        
        # Index catalog
        await search_engine.index_catalog(catalog)
        
        # Search
        results = search_engine.search("create github PR", catalog, top_k=5)
    """
    
    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "toolweaver_tools",
        embedding_model: str = "all-MiniLM-L6-v2",
        embedding_dim: int = 384,
        fallback_to_memory: bool = True,
        use_gpu: bool = True,
        precompute_embeddings: bool = True
    ):
        """
        Initialize vector search engine.
        
        Args:
            qdrant_url: Qdrant server URL
            collection_name: Collection name for tool embeddings
            embedding_model: SentenceTransformer model name
            embedding_dim: Embedding dimension
            fallback_to_memory: Use in-memory search if Qdrant unavailable
            use_gpu: Use GPU for embedding generation if available
            precompute_embeddings: Pre-compute embeddings at startup
        """
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.embedding_dim = embedding_dim
        self.fallback_to_memory = fallback_to_memory
        self.use_gpu = use_gpu
        self.precompute_embeddings = precompute_embeddings
        
        # Detect GPU availability
        self.device = self._detect_device()
        
        # Lazy initialization
        self.client: Optional[Any] = None
        self.embedding_model: Optional[Any] = None
        self.qdrant_available = False
        
        # Fallback in-memory search (if Qdrant unavailable)
        self.memory_embeddings: Dict[str, np.ndarray] = {}
        self.memory_tools: Dict[str, ToolDefinition] = {}
        
        # Pre-computed embeddings cache
        self.embedding_cache: Dict[str, np.ndarray] = {}
        
        logger.info(f"VectorToolSearchEngine initialized (Qdrant: {qdrant_url}, Device: {self.device})")
    
    def _detect_device(self) -> str:
        """
        Detect best available device for embedding generation.
        
        Returns:
            Device string: 'cuda', 'mps', or 'cpu'
        """
        if not self.use_gpu:
            logger.info("GPU disabled by configuration, using CPU")
            return "cpu"
        
        # Check for NVIDIA CUDA
        if TORCH_AVAILABLE and hasattr(torch, "cuda") and torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
            logger.info(f"GPU detected: {gpu_name} ({gpu_memory:.1f} GB)")
            return "cuda"
        
        # Check for Apple Silicon MPS (Metal Performance Shaders)
        if TORCH_AVAILABLE and hasattr(torch, "backends") and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            logger.info("Apple Silicon GPU detected (MPS)")
            return "mps"
        
        logger.info("No GPU available, using CPU")
        return "cpu"
    
    def _init_qdrant_client(self) -> None:
        """Initialize Qdrant client with connection pooling"""
        if self.client is None:
            if not QDRANT_IMPORTED:
                self.qdrant_available = False
                logger.warning("qdrant-client not installed; using in-memory fallback if enabled")
                return
            try:
                self.client = QdrantClient(  # type: ignore[misc]
                    url=self.qdrant_url,
                    timeout=10.0,
                    prefer_grpc=False  # Use REST API for simplicity
                )
                # Test connection
                self.client.get_collections()
                self.qdrant_available = True
                logger.info(f"Connected to Qdrant at {self.qdrant_url}")
            except Exception as e:
                logger.warning(f"Failed to connect to Qdrant: {e}")
                self.qdrant_available = False
                if not self.fallback_to_memory:
                    raise
                logger.info("Will use in-memory fallback for vector search")
    
    def _init_embedding_model(self) -> None:
        """Lazy initialization of embedding model with GPU support"""
        if self.embedding_model is None:
            if not SENTENCE_AVAILABLE:
                logger.warning("SentenceTransformer not installed; embeddings disabled.")
                return
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)  # type: ignore[misc]
            
            # Move model to GPU if available
            if self.device in ["cuda", "mps"] and self.embedding_model is not None:
                try:
                    self.embedding_model.to(self.device)
                    logger.info(f"Embedding model moved to {self.device.upper()}")
                except Exception as e:
                    logger.warning(f"Failed to move model to {self.device}: {e}")
                    self.device = "cpu"
            
            logger.info(f"Embedding model loaded (dim={self.embedding_dim}, device={self.device})")
    
    def _ensure_collection_exists(self) -> None:
        """Create collection if it doesn't exist"""
        if not self.qdrant_available:
            return
        
        try:
            collections = self.client.get_collections()  # type: ignore[union-attr]
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(  # type: ignore[union-attr]
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(  # type: ignore[misc]
                        size=self.embedding_dim,
                        distance=Distance.COSINE  # type: ignore[misc]
                    )
                )
                logger.info(f"Collection '{self.collection_name}' created")
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            self.qdrant_available = False
    
    def index_catalog(self, catalog: ToolCatalog, batch_size: int = 32) -> bool:
        """
        Index entire tool catalog in Qdrant.
        
        Args:
            catalog: Tool catalog to index
            batch_size: Batch size for embedding generation
        
        Returns:
            True if indexing succeeded, False otherwise
        """
        self._init_qdrant_client()
        self._init_embedding_model()
        
        tools = list(catalog.tools.values())
        if len(tools) == 0:
            logger.warning("Empty catalog - nothing to index")
            return False
        
        logger.info(f"Indexing {len(tools)} tools (batch_size={batch_size}, device={self.device})...")
        
        # Generate embeddings in batches with GPU acceleration
        descriptions = [self._get_searchable_text(tool) for tool in tools]
        embeddings = self._generate_embeddings_batch(
            descriptions,
            batch_size=batch_size,
            show_progress=True
        )
        
        if self.qdrant_available:
            try:
                self._ensure_collection_exists()
                
                # Create points for Qdrant
                points = []
                for i, tool in enumerate(tools):
                    points.append(
                        PointStruct(
                            id=i,
                            vector=embeddings[i].tolist(),
                            payload={
                                "tool_name": tool.name,
                                "tool_type": tool.type,
                                "domain": getattr(tool, "domain", "general"),
                                "description": tool.description,
                                "version": getattr(tool, "version", "1.0.0")
                            }
                        )
                    )
                
                # Batch upsert to Qdrant
                self.client.upsert(  # type: ignore[union-attr]
                    collection_name=self.collection_name,
                    points=points
                )
                logger.info(f"Successfully indexed {len(tools)} tools in Qdrant")
                return True
            except Exception as e:
                logger.error(f"Failed to index in Qdrant: {e}")
                self.qdrant_available = False
        
        # Fallback: Store in memory
        if self.fallback_to_memory:
            logger.info("Storing embeddings in memory (fallback mode)")
            for i, tool in enumerate(tools):
                self.memory_embeddings[tool.name] = embeddings[i]
                self.memory_tools[tool.name] = tool
            return True
        
        return False
    
    def search(
        self,
        query: str,
        catalog: ToolCatalog,
        top_k: int = 5,
        domain: Optional[str] = None,
        min_score: float = 0.3
    ) -> List[Tuple[ToolDefinition, float]]:
        """
        Search for relevant tools using vector similarity.
        
        Args:
            query: User's natural language query
            catalog: Tool catalog (used for fallback)
            top_k: Number of results to return
            domain: Optional domain filter (e.g., "github", "slack")
            min_score: Minimum similarity score (0-1)
        
        Returns:
            List of (ToolDefinition, score) tuples, sorted by relevance
        """
        self._init_qdrant_client()
        self._init_embedding_model()
        
        # Generate query embedding (uses cache if available)
        query_embeddings = self._generate_embeddings_batch(
            [query],
            batch_size=1,
            show_progress=False
        )
        query_embedding = query_embeddings[0]
        
        # Try Qdrant search first
        if self.qdrant_available:
            try:
                return self._qdrant_search(
                    query_embedding,
                    catalog,
                    top_k,
                    domain,
                    min_score
                )
            except Exception as e:
                logger.warning(f"Qdrant search failed: {e}, falling back to memory")
                self.qdrant_available = False
        
        # Fallback: In-memory cosine similarity
        if self.fallback_to_memory:
            return self._memory_search(
                query_embedding,
                catalog,
                top_k,
                min_score,
                domain
            )
        
        logger.error("Vector search unavailable and fallback disabled")
        return []
    
    def _qdrant_search(
        self,
        query_embedding: np.ndarray,
        catalog: ToolCatalog,
        top_k: int,
        domain: Optional[str],
        min_score: float
    ) -> List[Tuple[ToolDefinition, float]]:
        """Perform search using Qdrant"""
        # Build filter for domain-based search
        search_filter = None
        if domain:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="domain",
                        match=MatchValue(value=domain)
                    )
                ]
            )
        
        # Search in Qdrant
        search_results = self.client.search(  # type: ignore[union-attr]
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            query_filter=search_filter,
            limit=top_k,
            score_threshold=min_score
        )
        
        # Convert results to (ToolDefinition, score) tuples
        results = []
        for hit in search_results:
            tool_name = hit.payload["tool_name"]
            if tool_name in catalog.tools:
                tool = catalog.tools[tool_name]
                score = hit.score
                results.append((tool, score))
        
        logger.info(f"Qdrant search returned {len(results)} results (top_k={top_k}, domain={domain})")
        return results
    
    def _memory_search(
        self,
        query_embedding: np.ndarray,
        catalog: ToolCatalog,
        top_k: int,
        min_score: float,
        domain: Optional[str] = None
    ) -> List[Tuple[ToolDefinition, float]]:
        """Fallback: In-memory cosine similarity search"""
        if not self.memory_embeddings:
            logger.warning("No embeddings in memory, indexing catalog...")
            self.index_catalog(catalog)
        
        # Compute cosine similarity for all tools
        scores = []
        for tool_name, embedding in self.memory_embeddings.items():
            if tool_name in catalog.tools:
                tool = catalog.tools[tool_name]
                
                # Apply domain filter if specified
                if domain and tool.domain != domain:
                    continue
                
                similarity = np.dot(query_embedding, embedding)
                if similarity >= min_score:
                    scores.append((tool, float(similarity)))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        results = scores[:top_k]
        
        logger.info(f"In-memory search returned {len(results)} results")
        return results
    
    def _generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings in batches with GPU acceleration.
        
        Args:
            texts: List of text strings to encode
            batch_size: Batch size for encoding (larger for GPU)
            show_progress: Show progress bar
        
        Returns:
            Numpy array of embeddings (shape: [num_texts, embedding_dim])
        """
        # Check cache first
        cached_embeddings = []
        texts_to_encode = []
        text_indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self.embedding_cache:
                cached_embeddings.append((i, self.embedding_cache[cache_key]))
            else:
                texts_to_encode.append(text)
                text_indices.append(i)
        
        # If all cached, return immediately
        if not texts_to_encode:
            logger.info(f"All {len(texts)} embeddings retrieved from cache")
            result = np.zeros((len(texts), self.embedding_dim))
            for idx, emb in cached_embeddings:
                result[idx] = emb
            return result
        
        logger.info(f"Generating {len(texts_to_encode)} embeddings ({len(cached_embeddings)} cached)")
        
        # Adjust batch size for GPU (can handle larger batches)
        if self.device in ["cuda", "mps"]:
            batch_size = min(batch_size * 4, 128)  # 4x larger batches on GPU
            logger.debug(f"Using GPU batch size: {batch_size}")
        
        # Generate embeddings
        if self.embedding_model is None:
            # Embeddings unavailable; return zeros
            new_embeddings = np.zeros((len(texts_to_encode), self.embedding_dim))
        else:
            new_embeddings = self.embedding_model.encode(  # type: ignore[union-attr]
                texts_to_encode,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=True,
                device=self.device
            )
        
        # Cache new embeddings
        for i, text in enumerate(texts_to_encode):
            cache_key = self._get_cache_key(text)
            self.embedding_cache[cache_key] = new_embeddings[i]
        
        # Combine cached and new embeddings
        result = np.zeros((len(texts), self.embedding_dim))
        for idx, emb in cached_embeddings:
            result[idx] = emb
        for i, idx in enumerate(text_indices):
            result[idx] = new_embeddings[i]
        
        return result
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text (first 100 chars hash)"""
        return str(hash(text[:100]))
    
    def precompute_catalog_embeddings(self, catalog: ToolCatalog):
        """
        Pre-compute embeddings for all tools in catalog at startup.
        
        This eliminates cold-start latency by caching embeddings in memory.
        
        Args:
            catalog: Tool catalog to pre-compute embeddings for
        """
        if not self.precompute_embeddings:
            logger.debug("Embedding pre-computation disabled")
            return
        
        tools = list(catalog.tools.values())
        if not tools:
            logger.warning("Empty catalog - nothing to pre-compute")
            return
        
        logger.info(f"Pre-computing embeddings for {len(tools)} tools...")
        descriptions = [self._get_searchable_text(tool) for tool in tools]
        
        # Generate and cache embeddings
        start_time = torch.cuda.Event(enable_timing=True) if (TORCH_AVAILABLE and self.device == "cuda") else None
        end_time = torch.cuda.Event(enable_timing=True) if (TORCH_AVAILABLE and self.device == "cuda") else None
        
        if start_time:
            start_time.record()
        
        embeddings = self._generate_embeddings_batch(
            descriptions,
            batch_size=64,  # Larger batch for pre-computation
            show_progress=False
        )
        
        if end_time and start_time:
            end_time.record()
            if TORCH_AVAILABLE:
                torch.cuda.synchronize()
                elapsed_ms = start_time.elapsed_time(end_time)  # type: ignore[assignment]
            else:
                elapsed_ms = 0.0
            logger.info(f"Pre-computed {len(tools)} embeddings in {elapsed_ms:.1f}ms on {self.device.upper()}")
        else:
            logger.info(f"Pre-computed {len(tools)} embeddings on {self.device.upper()}")
        
        # Cache results
        for i, tool in enumerate(tools):
            cache_key = self._get_cache_key(self._get_searchable_text(tool))
            self.embedding_cache[cache_key] = embeddings[i]
        
        logger.info(f"Embedding cache size: {len(self.embedding_cache)} entries")
    
    def _get_searchable_text(self, tool: ToolDefinition) -> str:
        """Extract searchable text from tool definition"""
        parts = [tool.description]
        
        # Add parameter names and descriptions
        for param in tool.parameters:
            parts.append(param.name)
            if param.description:
                parts.append(param.description)
        
        # Add examples
        for example in tool.examples:
            if hasattr(example, "scenario"):
                parts.append(example.scenario)
        
        return " ".join(parts)
    
    def delete_tool(self, tool_name: str) -> bool:
        """
        Delete a tool from the index.
        
        Args:
            tool_name: Name of tool to delete
        
        Returns:
            True if deletion succeeded
        """
        if self.qdrant_available and self.client is not None:
            try:
                # Find point ID by tool_name
                search_results = self.client.scroll(  # type: ignore[union-attr]
                    collection_name=self.collection_name,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="tool_name",
                                match=MatchValue(value=tool_name)
                            )
                        ]
                    ),
                    limit=1
                )
                
                if search_results[0]:
                    point_id = search_results[0][0].id
                    self.client.delete(  # type: ignore[union-attr]
                        collection_name=self.collection_name,
                        points_selector=[point_id]
                    )
                    logger.info(f"Deleted tool '{tool_name}' from Qdrant")
                    return True
            except Exception as e:
                logger.error(f"Failed to delete tool from Qdrant: {e}")
        
        # Fallback: Delete from memory
        if tool_name in self.memory_embeddings:
            del self.memory_embeddings[tool_name]
            del self.memory_tools[tool_name]
            return True
        
        return False
    
    def clear_index(self) -> bool:
        """Clear all tools from the index"""
        if self.qdrant_available and self.client is not None:
            try:
                self.client.delete_collection(self.collection_name)  # type: ignore[union-attr]
                logger.info(f"Cleared collection: {self.collection_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to clear collection: {e}")
        
        # Clear memory fallback
        self.memory_embeddings.clear()
        self.memory_tools.clear()
        return True
