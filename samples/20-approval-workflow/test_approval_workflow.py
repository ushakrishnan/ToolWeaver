import builtins

import approval_workflow
import pytest


class DummyOrchestrator:
    def __init__(self):
        self.calls = []

    async def execute_agent_step(self, agent_name: str, request: dict, stream: bool = False):
        self.calls.append(("agent", agent_name))
        return {"agent": agent_name, "request": request}

    async def execute_tool(self, name: str, params: dict):
        self.calls.append(("tool", name))
        return {"applied": True, "target": params.get("target")}


@pytest.mark.asyncio
async def test_workflow_smoke(monkeypatch):
    dummy = DummyOrchestrator()
    monkeypatch.setattr(approval_workflow, "Orchestrator", lambda: dummy)
    monkeypatch.setattr(builtins, "input", lambda _: "y")

    await approval_workflow.main()

    assert ("tool", "apply_changes") in dummy.calls
