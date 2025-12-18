import asyncio
import pytest

from orchestrator.infra.mcp_client import MCPClientShim


@pytest.mark.asyncio
async def test_mcp_idempotency_cache_ttl_and_lru():
    client = MCPClientShim()

    async def worker(payload):
        return payload["x"]

    client.tool_map = {"echo": worker}

    # First call caches
    result1 = await client.call_tool("echo", {"x": 1}, idempotency_key="k1")
    assert result1 == 1

    # Cached
    result2 = await client.call_tool("echo", {"x": 2}, idempotency_key="k1")
    assert result2 == 1


@pytest.mark.asyncio
async def test_mcp_retry_then_success():
    calls = {"count": 0}

    async def flaky(payload):
        calls["count"] += 1
        if calls["count"] < 2:
            raise RuntimeError("fail once")
        return "ok"

    client = MCPClientShim(max_retries=2, retry_backoff_s=0.01)
    client.tool_map = {"flaky": flaky}

    result = await client.call_tool("flaky", {})
    assert result == "ok"
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_mcp_circuit_opens_after_failures():
    async def always_fail(payload):
        raise RuntimeError("boom")

    client = MCPClientShim(max_retries=0, circuit_breaker_threshold=1, circuit_reset_s=1)
    client.tool_map = {"bad": always_fail}

    with pytest.raises(RuntimeError):
        await client.call_tool("bad", {})

    # Circuit should be open now
    with pytest.raises(RuntimeError, match="circuit open"):
        await client.call_tool("bad", {})

    # Wait for reset and ensure it attempts again
    await asyncio.sleep(1.05)
    with pytest.raises(RuntimeError):
        await client.call_tool("bad", {})


@pytest.mark.asyncio
async def test_mcp_observer_events():
    events = []

    def observer(evt, data):
        events.append((evt, data))

    async def worker(payload):
        return "ok"

    client = MCPClientShim(observer=observer)
    client.tool_map = {"ok": worker}

    await client.call_tool("ok", {}, idempotency_key="observer-1")

    assert any(e[0] == "mcp.start" for e in events)
    assert any(e[0] == "mcp.complete" and e[1].get("success") is True for e in events)
    # cache hit should emit on second call
    await client.call_tool("ok", {}, idempotency_key="observer-1")
    assert any(e[0] == "mcp.cache_hit" for e in events)


@pytest.mark.asyncio
async def test_mcp_streaming_emits_chunks_and_events():
    events = []

    def observer(evt, data):
        events.append((evt, data))

    async def stream_worker(payload):
        for i in range(3):
            await asyncio.sleep(0)
            yield f"chunk-{i}"

    client = MCPClientShim(observer=observer)
    client.tool_map = {"stream": stream_worker}

    chunks = []
    async for chunk in client.call_tool_stream("stream", {}, chunk_timeout=1):
        chunks.append(chunk)

    assert chunks == ["chunk-0", "chunk-1", "chunk-2"]
    assert any(e[0] == "mcp.stream.start" for e in events)
    assert any(e[0] == "mcp.stream.chunk" for e in events)
    assert any(e[0] == "mcp.stream.complete" and e[1].get("success") is True for e in events)


@pytest.mark.asyncio
async def test_mcp_streaming_retries_on_chunk_timeout():
    calls = {"attempt": 0}

    async def flaky_stream(payload):
        calls["attempt"] += 1
        if calls["attempt"] == 1:
            await asyncio.sleep(0.05)  # exceed chunk_timeout before first yield
            yield "never"
        else:
            yield "good-0"
            yield "good-1"

    client = MCPClientShim(max_retries=1, retry_backoff_s=0.0)
    client.tool_map = {"stream": flaky_stream}

    chunks = []
    async for chunk in client.call_tool_stream("stream", {}, chunk_timeout=0.01):
        chunks.append(chunk)

    assert chunks == ["good-0", "good-1"]
    assert calls["attempt"] == 2
