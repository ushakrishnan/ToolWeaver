# Dynamic import to handle dashed folder name
import importlib.util
import pathlib
import types

spec = importlib.util.spec_from_file_location(
    "workflow22",
    str(pathlib.Path(__file__).parent / "workflow.py"),
)
workflow22 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow22)  # type: ignore


class DummyOrchestrator:
    async def execute_tool(self, name: str, params: dict):
        if name == "fetch_data":
            return {"data": {"message": "hello"}}
        if name == "store_data":
            assert params["document"]["total_len"] >= 1
            return {"ok": True}
        raise AssertionError("unknown tool")

    async def execute_agent_step(self, agent_name: str, request: dict, stream: bool = False):
        assert agent_name == "analyze"
        return {"summary": "hello world"}


def test_showcase_smoke(monkeypatch):
    dummy = DummyOrchestrator()
    monkeypatch.setattr(workflow22, "Orchestrator", lambda: dummy)

    # In-memory skill library stubs
    store = {}

    def save_skill(name: str, code: str, metadata: dict):
        import os
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".py")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        store[name] = path
        return types.SimpleNamespace(name=name, code_path=path, version="0.0.1")

    def get_skill(name: str):
        return types.SimpleNamespace(name=name, code_path=store[name], version="0.0.1")

    from orchestrator._internal.execution import skill_library as sl
    monkeypatch.setattr(sl, "save_skill", save_skill)
    monkeypatch.setattr(sl, "get_skill", get_skill)

    # Run
    import asyncio
    asyncio.run(workflow22.main())
