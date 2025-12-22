import asyncio
import pytest

from orchestrator._internal.dispatch.hybrid_dispatcher import dispatch_step


class DummyMCP:
    def __init__(self):
        self.tool_map = {}


class DummyResponse:
    def __init__(self, result):
        self.result = result


class DummyA2A:
    def __init__(self, responses=None, stream_chunks=None):
        self.responses = responses or {}
        self.stream_chunks = stream_chunks or {}
        self.calls = []

    async def delegate_to_agent(self, request):
        self.calls.append(("delegate", request.agent_id))
        return DummyResponse(self.responses.get(request.agent_id, None))

    async def delegate_stream(self, request, chunk_timeout=None):
        self.calls.append(("stream", request.agent_id))
        for chunk in self.stream_chunks.get(request.agent_id, []):
            await asyncio.sleep(0)
            yield chunk


@pytest.mark.asyncio
async def test_dispatch_agent_delegation_returns_result():
    mcp = DummyMCP()
    a2a = DummyA2A(responses={"agent_1": {"ok": True}})

    step = {
        "tool": "agent_agent_1",
        "input": {"task": "do", "context": {"x": 1}},
        "timeout_s": 5,
    }

    result = await dispatch_step(step, {}, mcp, None, a2a)
    assert result == {"ok": True}
    assert ("delegate", "agent_1") in a2a.calls


@pytest.mark.asyncio
async def test_dispatch_agent_streaming_collects_chunks():
    mcp = DummyMCP()
    a2a = DummyA2A(stream_chunks={"agent_stream": ["c1", "c2"]})

    step = {
        "tool": "agent_agent_stream",
        "input": {"task": "stream"},
        "stream": True,
    }

    result = await dispatch_step(step, {}, mcp, None, a2a)
    assert result == {"chunks": ["c1", "c2"]}
    assert ("stream", "agent_stream") in a2a.calls


@pytest.mark.asyncio
async def test_dispatch_mcp_streaming_collects_chunks():
    async def worker(payload):
        yield "m1"
        yield "m2"

    class MCP:
        def __init__(self):
            self.tool_map = {"stream_tool": worker}

        async def call_tool_stream(self, name, payload, timeout=30, chunk_timeout=None):
            async for c in worker(payload):
                yield c

        async def call_tool(self, name, payload, idempotency_key=None, timeout=30):
            return "not-used"

    mcp = MCP()
    a2a = DummyA2A()

    step = {
        "tool": "stream_tool",
        "input": {},
        "stream": True,
    }

    result = await dispatch_step(step, {}, mcp, None, a2a)
    assert result == {"chunks": ["m1", "m2"]}
