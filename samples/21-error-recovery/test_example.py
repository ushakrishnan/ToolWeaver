import asyncio

import pytest

import workflow


class DummyOrchestrator:
    def __init__(self):
        self.tool_attempts = 0

    async def execute_tool(self, name: str, params: dict):
        self.tool_attempts += 1
        if self.tool_attempts == 1:
            raise RuntimeError("boom")
        return {"status": "ok"}

    async def execute_agent_step(self, agent_name: str, request: dict):
        return {"agent": agent_name, "request": request, "action": "fix"}


@pytest.mark.asyncio
async def test_workflow_recovers(monkeypatch):
    dummy = DummyOrchestrator()
    monkeypatch.setattr(workflow, "Orchestrator", lambda: dummy)

    await workflow.main()

    assert dummy.tool_attempts == 2
