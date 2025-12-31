
import pytest
import workflow


class DummyOrchestrator:
    def __init__(self):
        self.tool_calls = []

    async def discover_tools(self, use_cache: bool = True):
        return ["fetch_data", "analysis_agent", "store_data"]

    async def execute_tool(self, name: str, params: dict):
        self.tool_calls.append(name)
        if name == "fetch_data":
            return {"data": {"value": 1}}
        if name == "store_data":
            return {"stored": params.get("destination")}
        return {}

    async def execute_agent_step(self, agent_name: str, request: dict, stream: bool = False):
        return {"summary": f"ok:{agent_name}", "input": request}


class DummyMonitoring:
    def log_tool_call(self, *_, **__):
        return None


@pytest.mark.asyncio
async def test_workflow_smoke(monkeypatch):
    dummy = DummyOrchestrator()
    monkeypatch.setattr(workflow, "Orchestrator", lambda: dummy)
    monkeypatch.setattr(workflow, "MonitoringBackend", lambda: DummyMonitoring())

    await workflow.main()

    assert dummy.tool_calls == ["fetch_data", "store_data"]
