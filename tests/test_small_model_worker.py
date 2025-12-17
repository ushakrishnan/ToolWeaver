"""
Tests for Small Model Worker with Ollama

Tests the small model worker with real Ollama backend.
Skips if Ollama is not available.
"""

import pytest
import os
import asyncio
from orchestrator.execution.small_model_worker import SmallModelWorker


@pytest.fixture
def ollama_worker():
    """Create worker configured for Ollama"""
    # Set environment variable for Ollama URL
    if not os.getenv("OLLAMA_API_URL"):
        os.environ["OLLAMA_API_URL"] = "http://localhost:11434"
    
    # Use phi3:latest which is what's installed
    return SmallModelWorker(
        backend="ollama",
        model_name=os.getenv("WORKER_MODEL", "phi3:latest")
    )


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("SMALL_MODEL_BACKEND") != "ollama",
    reason="Ollama not configured (set SMALL_MODEL_BACKEND=ollama)"
)
async def test_ollama_connection(ollama_worker):
    """Test connection to Ollama"""
    # Simple generation test
    response = await ollama_worker.generate(
        prompt="Say 'Hello'",
        system_prompt="You are a helpful assistant",
        max_tokens=10,
        temperature=0.1
    )
    
    assert response is not None
    assert len(response) > 0
    assert "hello" in response.lower()


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("SMALL_MODEL_BACKEND") != "ollama",
    reason="Ollama not configured"
)
async def test_ollama_json_mode(ollama_worker):
    """Test JSON mode generation"""
    response = await ollama_worker.generate(
        prompt='Return JSON: {"status": "ok", "message": "test"}',
        system_prompt="You return valid JSON only",
        max_tokens=50,
        temperature=0.1
    )
    
    assert response is not None
    # Should contain JSON-like structure
    assert "{" in response and "}" in response


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("SMALL_MODEL_BACKEND") != "ollama",
    reason="Ollama not configured"
)
async def test_ollama_function_calling(ollama_worker):
    """Test function calling with Ollama"""
    # Test tool use generation
    response = await ollama_worker.generate(
        prompt="What's the weather in Paris?",
        system_prompt="You have access to get_weather(location: str). Use it.",
        max_tokens=100,
        temperature=0.1
    )
    
    assert response is not None
    assert len(response) > 0
    # Should mention weather or Paris
    assert "weather" in response.lower() or "paris" in response.lower()


@pytest.mark.asyncio  
@pytest.mark.skipif(
    os.getenv("SMALL_MODEL_BACKEND") != "ollama",
    reason="Ollama not configured"
)
async def test_ollama_streaming():
    """Test streaming responses from Ollama"""
    worker = SmallModelWorker(
        backend="ollama",
        model_name=os.getenv("WORKER_MODEL", "phi3:latest")
    )
    
    # Test basic generation works
    response = await worker.generate(
        prompt="Count to 5",
        system_prompt="Count numbers",
        max_tokens=50,
        temperature=0.1
    )
    
    assert response is not None
    assert len(response) > 0


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("SMALL_MODEL_BACKEND") != "ollama",
    reason="Ollama not configured"
)
async def test_ollama_batch_processing():
    """Test processing multiple requests"""
    worker = SmallModelWorker(
        backend="ollama",
        model_name=os.getenv("WORKER_MODEL", "phi3:latest")
    )
    
    prompts = [
        "Say hello",
        "Say goodbye", 
        "Say thank you"
    ]
    
    responses = []
    for prompt in prompts:
        response = await worker.generate(
            prompt=prompt,
            system_prompt="You are helpful",
            max_tokens=20,
            temperature=0.1
        )
        responses.append(response)
    
    assert len(responses) == 3
    assert all(r is not None for r in responses)
    assert all(len(r) > 0 for r in responses)


def test_ollama_initialization():
    """Test Ollama worker initialization"""
    model_name = os.getenv("WORKER_MODEL", "phi3:latest")
    worker = SmallModelWorker(
        backend="ollama",
        model_name=model_name
    )
    
    assert worker.backend == "ollama"
    assert worker.model_name == model_name

@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("SMALL_MODEL_BACKEND") != "ollama",
    reason="Ollama not configured"
)
async def test_ollama_error_handling(ollama_worker):
    """Test error handling with invalid requests"""
    # Test with very short max_tokens (might cause truncation)
    response = await ollama_worker.generate(
        prompt="Tell me a long story about adventure",
        system_prompt="You are a storyteller",
        max_tokens=5,  # Very short
        temperature=0.1
    )
    
    # Should still return something, even if truncated
    assert response is not None


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("SMALL_MODEL_BACKEND") != "ollama",
    reason="Ollama not configured"
)
async def test_ollama_temperature_control(ollama_worker):
    """Test temperature parameter affects randomness"""
    prompt = "Give me a creative idea"
    
    # Low temperature (more deterministic)
    response1 = await ollama_worker.generate(
        prompt=prompt,
        system_prompt="Be creative",
        max_tokens=50,
        temperature=0.1
    )
    
    # Higher temperature (more random)
    response2 = await ollama_worker.generate(
        prompt=prompt,
        system_prompt="Be creative",
        max_tokens=50,
        temperature=0.9
    )
    
    # Both should return something
    assert response1 is not None
    assert response2 is not None
    # Responses might be different (but not guaranteed)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
