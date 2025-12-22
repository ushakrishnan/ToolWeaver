import pytest

from orchestrator._internal.runtime.orchestrator import run_step


class DummyMCP:
    def __init__(self):
        self.tool_map = {}


class DummyResponse:
    def __init__(self, result, success=True):
        self.result = result
        self.success = success


class DummyA2A:
    def __init__(self):
        self.calls = []

    async def delegate_to_agent(self, request):
        self.calls.append(request)
        return DummyResponse({"ok": True, "context": request.context, "task": request.task})

    async def delegate_stream(self, request, chunk_timeout=None):
        self.calls.append(("stream", request.agent_id, chunk_timeout))
        yield "c1"
        yield "c2"


@pytest.mark.asyncio
async def test_run_step_agent_type_builds_context_and_delegates():
    mcp = DummyMCP()
    a2a = DummyA2A()

    step = {
        "type": "agent",
        "agent_id": "agent_1",
        "task": "do something",
        "inputs": ["foo"],
        "timeout_s": 5,
    }
    step_outputs = {"foo": {"bar": 1}}

    result = await run_step(step, step_outputs, mcp, monitor=None, a2a_client=a2a)

    assert result == {"ok": True, "context": {"foo": {"bar": 1}}, "task": "do something"}
    assert len(a2a.calls) == 1
    assert a2a.calls[0].agent_id == "agent_1"
    assert a2a.calls[0].context == {"foo": {"bar": 1}}


@pytest.mark.asyncio
async def test_run_step_agent_type_streams_when_requested():
    mcp = DummyMCP()
    a2a = DummyA2A()

    step = {
        "type": "agent",
        "agent_id": "agent_stream",
        "task": "stream",
        "stream": True,
        "chunk_timeout_s": 0.5,
    }

    result = await run_step(step, {}, mcp, monitor=None, a2a_client=a2a)

    assert result == {"chunks": ["c1", "c2"]}
    # Second call entry is the streaming tuple
    assert ("stream", "agent_stream", 0.5) in a2a.calls
