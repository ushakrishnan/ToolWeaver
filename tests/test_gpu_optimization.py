"""
Tests for GPU-accelerated embedding generation (Phase 7 Component 4)

Tests cover:
1. GPU detection (CUDA, MPS, CPU fallback)
2. Batch embedding generation with caching
3. Pre-computation at startup
4. Performance improvements with GPU
5. Cache hit/miss behavior
"""

import pytest
import numpy as np
import torch
from unittest.mock import Mock, patch, MagicMock

from orchestrator.vector_search import VectorToolSearchEngine
from orchestrator.models import (
    ToolCatalog,
    ToolDefinition,
    ToolParameter,
    ToolExample
)


@pytest.fixture
def sample_tools():
    """Create sample tools for testing"""
    tools = []
    
    # GitHub tools
    tools.append(ToolDefinition(
        name="create_github_pr",
        description="Create a pull request on GitHub",
        type="function",
        parameters=[
            ToolParameter(name="repo", type="string", required=True, description="Repository name"),
            ToolParameter(name="title", type="string", required=True, description="PR title"),
        ],
        examples=[
            ToolExample(
                scenario="Create PR for new feature",
                input={"repo": "myrepo", "title": "Add feature"},
                output={"pr_url": "https://github.com/myrepo/pulls/1"}
            )
        ],
        domain="github"
    ))
    
    tools.append(ToolDefinition(
        name="list_github_issues",
        description="List open issues in a GitHub repository",
        type="function",
        parameters=[
            ToolParameter(name="repo", type="string", required=True, description="Repository name"),
        ],
        examples=[],
        domain="github"
    ))
    
    # Slack tool
    tools.append(ToolDefinition(
        name="send_slack_message",
        description="Send a message to a Slack channel",
        type="function",
        parameters=[
            ToolParameter(name="channel", type="string", required=True, description="Channel name"),
            ToolParameter(name="message", type="string", required=True, description="Message text"),
        ],
        examples=[],
        domain="slack"
    ))
    
    return tools


@pytest.fixture
def sample_catalog(sample_tools):
    """Create a sample tool catalog"""
    catalog = ToolCatalog(name="test_catalog")
    for tool in sample_tools:
        catalog.add_tool(tool)
    return catalog


class TestGPUDetection:
    """Test GPU detection and device selection"""
    
    def test_detect_cuda_available(self):
        """Test CUDA GPU detection"""
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.cuda.get_device_name', return_value='NVIDIA RTX 4090'):
                with patch('torch.cuda.get_device_properties') as mock_props:
                    mock_props.return_value = Mock(total_memory=24 * 1024**3)  # 24 GB
                    
                    engine = VectorToolSearchEngine(
                        qdrant_url="http://localhost:6333",
                        use_gpu=True,
                        precompute_embeddings=False
                    )
                    
                    assert engine.device == "cuda"
    
    def test_detect_mps_available(self):
        """Test Apple Silicon MPS detection"""
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=True):
                engine = VectorToolSearchEngine(
                    qdrant_url="http://localhost:6333",
                    use_gpu=True,
                    precompute_embeddings=False
                )
                
                assert engine.device == "mps"
    
    def test_fallback_to_cpu(self):
        """Test CPU fallback when no GPU available"""
        with patch('torch.cuda.is_available', return_value=False):
            with patch('torch.backends.mps.is_available', return_value=False):
                engine = VectorToolSearchEngine(
                    qdrant_url="http://localhost:6333",
                    use_gpu=True,
                    precompute_embeddings=False
                )
                
                assert engine.device == "cpu"
    
    def test_gpu_disabled_by_config(self):
        """Test GPU disabled by configuration"""
        with patch('torch.cuda.is_available', return_value=True):
            engine = VectorToolSearchEngine(
                qdrant_url="http://localhost:6333",
                use_gpu=False,  # Explicitly disable GPU
                precompute_embeddings=False
            )
            
            assert engine.device == "cpu"


class TestBatchEmbeddingGeneration:
    """Test batch embedding generation with GPU acceleration"""
    
    def test_batch_embeddings_without_cache(self):
        """Test batch embedding generation from scratch"""
        engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            precompute_embeddings=False
        )
        engine._init_embedding_model()
        
        texts = [
            "Create a pull request on GitHub",
            "Send a message to Slack",
            "List open issues in repository"
        ]
        
        embeddings = engine._generate_embeddings_batch(texts, batch_size=32, show_progress=False)
        
        assert embeddings.shape == (3, 384)  # 3 texts, 384 dimensions
        assert isinstance(embeddings, np.ndarray)
        
        # Check that embeddings are normalized (L2 norm ≈ 1.0)
        for emb in embeddings:
            norm = np.linalg.norm(emb)
            assert 0.99 <= norm <= 1.01, f"Embedding not normalized: {norm}"
    
    def test_batch_embeddings_with_cache(self):
        """Test that cached embeddings are reused"""
        engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            precompute_embeddings=False
        )
        engine._init_embedding_model()
        
        texts = [
            "Create a pull request on GitHub",
            "Send a message to Slack",
        ]
        
        # First call - should generate embeddings
        embeddings1 = engine._generate_embeddings_batch(texts, batch_size=32, show_progress=False)
        
        # Second call - should use cache
        embeddings2 = engine._generate_embeddings_batch(texts, batch_size=32, show_progress=False)
        
        # Results should be identical
        np.testing.assert_array_almost_equal(embeddings1, embeddings2)
        
        # Cache should have entries
        assert len(engine.embedding_cache) >= 2
    
    def test_batch_size_adjustment_for_gpu(self):
        """Test that batch size is increased for GPU"""
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.cuda.get_device_name', return_value='NVIDIA RTX 4090'):
                with patch('torch.cuda.get_device_properties') as mock_props:
                    mock_props.return_value = Mock(total_memory=24 * 1024**3)
                    
                    engine = VectorToolSearchEngine(
                        qdrant_url="http://localhost:6333",
                        use_gpu=True,
                        precompute_embeddings=False
                    )
                    
                    assert engine.device == "cuda"
                    
                    # Test that GPU uses larger batch size
                    # (We can't test the actual behavior without a real GPU,
                    # but we can verify the device is set correctly)
    
    def test_partial_cache_hit(self):
        """Test mixed cache hit/miss scenario"""
        engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            precompute_embeddings=False
        )
        engine._init_embedding_model()
        
        # Generate embeddings for first 2 texts
        texts1 = [
            "Create a pull request on GitHub",
            "Send a message to Slack",
        ]
        embeddings1 = engine._generate_embeddings_batch(texts1, batch_size=32, show_progress=False)
        
        # Now generate embeddings for 3 texts (2 cached, 1 new)
        texts2 = [
            "Create a pull request on GitHub",  # Cached
            "Send a message to Slack",  # Cached
            "List open issues in repository"  # New
        ]
        embeddings2 = engine._generate_embeddings_batch(texts2, batch_size=32, show_progress=False)
        
        # First 2 embeddings should match
        np.testing.assert_array_almost_equal(embeddings2[0], embeddings1[0])
        np.testing.assert_array_almost_equal(embeddings2[1], embeddings1[1])
        
        # Third embedding should be new
        assert embeddings2.shape == (3, 384)


class TestPrecomputation:
    """Test embedding pre-computation at startup"""
    
    def test_precompute_catalog_embeddings(self, sample_catalog):
        """Test pre-computation of all catalog embeddings"""
        engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            precompute_embeddings=True
        )
        engine._init_embedding_model()
        
        # Pre-compute embeddings
        engine.precompute_catalog_embeddings(sample_catalog)
        
        # Verify cache has entries for all tools
        assert len(engine.embedding_cache) == len(sample_catalog.tools)
        
        # Verify embeddings are valid
        for cache_key, embedding in engine.embedding_cache.items():
            assert embedding.shape == (384,)
            norm = np.linalg.norm(embedding)
            assert 0.99 <= norm <= 1.01
    
    def test_precompute_empty_catalog(self):
        """Test pre-computation with empty catalog"""
        engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            precompute_embeddings=True
        )
        engine._init_embedding_model()
        
        empty_catalog = ToolCatalog(name="empty")
        
        # Should not crash
        engine.precompute_catalog_embeddings(empty_catalog)
        
        # Cache should be empty
        assert len(engine.embedding_cache) == 0
    
    def test_precompute_disabled_by_config(self, sample_catalog):
        """Test that pre-computation can be disabled"""
        engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            precompute_embeddings=False  # Disabled
        )
        engine._init_embedding_model()
        
        # Pre-compute should do nothing
        engine.precompute_catalog_embeddings(sample_catalog)
        
        # Cache should be empty (pre-computation was disabled)
        assert len(engine.embedding_cache) == 0
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_precompute_timing_with_cuda(self, sample_catalog):
        """Test that CUDA timing works for pre-computation"""
        engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            use_gpu=True,
            fallback_to_memory=True,
            precompute_embeddings=True
        )
        engine._init_embedding_model()
        
        # This should not crash with CUDA timing
        engine.precompute_catalog_embeddings(sample_catalog)
        
        # Verify cache populated
        assert len(engine.embedding_cache) > 0


class TestSearchWithCache:
    """Test search functionality with embedding cache"""
    
    def test_search_uses_cache(self, sample_catalog):
        """Test that search uses cached embeddings"""
        engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            precompute_embeddings=True
        )
        engine._init_embedding_model()
        
        # Pre-compute embeddings
        engine.precompute_catalog_embeddings(sample_catalog)
        cache_size_before = len(engine.embedding_cache)
        
        # Index catalog (should use cached embeddings)
        engine.index_catalog(sample_catalog, batch_size=32)
        
        # Perform search
        results = engine.search("create pull request", sample_catalog, top_k=3)
        
        # Cache size should not change significantly (query embedding added)
        cache_size_after = len(engine.embedding_cache)
        assert cache_size_after - cache_size_before <= 1  # Only query embedding added
        
        # Should return relevant results
        assert len(results) > 0
        assert results[0][0].name == "create_github_pr"
    
    def test_search_without_precompute(self, sample_catalog):
        """Test search without pre-computation (cold start)"""
        engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            precompute_embeddings=False  # No pre-computation
        )
        engine._init_embedding_model()
        
        # Index catalog (generates embeddings on-demand)
        engine.index_catalog(sample_catalog, batch_size=32)
        
        # Perform search
        results = engine.search("create pull request", sample_catalog, top_k=3)
        
        # Should still work correctly
        assert len(results) > 0
        assert results[0][0].name == "create_github_pr"


class TestCacheKeyGeneration:
    """Test cache key generation"""
    
    def test_cache_key_consistency(self):
        """Test that same text generates same cache key"""
        engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            precompute_embeddings=False
        )
        
        text = "Create a pull request on GitHub"
        
        key1 = engine._get_cache_key(text)
        key2 = engine._get_cache_key(text)
        
        assert key1 == key2
    
    def test_cache_key_uniqueness(self):
        """Test that different texts generate different cache keys"""
        engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            precompute_embeddings=False
        )
        
        text1 = "Create a pull request on GitHub"
        text2 = "Send a message to Slack"
        
        key1 = engine._get_cache_key(text1)
        key2 = engine._get_cache_key(text2)
        
        assert key1 != key2
    
    def test_cache_key_truncation(self):
        """Test that cache key uses first 100 chars"""
        engine = VectorToolSearchEngine(
            qdrant_url="http://localhost:6333",
            fallback_to_memory=True,
            precompute_embeddings=False
        )
        
        # Two texts identical in first 100 chars
        text1 = "A" * 100 + "B" * 50
        text2 = "A" * 100 + "C" * 50
        
        key1 = engine._get_cache_key(text1)
        key2 = engine._get_cache_key(text2)
        
        # Should generate same key (uses first 100 chars)
        assert key1 == key2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
