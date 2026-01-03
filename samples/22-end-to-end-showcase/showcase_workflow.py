from pathlib import Path
from typing import Any, cast

try:
    from orchestrator import Orchestrator as _CoreOrchestrator  # type: ignore[attr-defined]
    Orchestrator = _CoreOrchestrator  # type: ignore[assignment]
except Exception:
    class Orchestrator:  # type: ignore
        async def execute_tool(self, name: str, params: dict[str, Any]) -> dict[str, Any]:
            return {"ok": True, "name": name, "params": params}
        async def execute_agent_step(self, agent_name: str, request: dict[str, Any], stream: bool = False) -> dict[str, Any]:
            return {"summary": f"Analysis of {request.get('text','')}"}

from orchestrator import skill_library as sl


async def main() -> None:
    orch = Orchestrator()

    fetched = await orch.execute_tool("fetch_data", {"url": "https://example.com/data.json"})
    analysis = await orch.execute_agent_step("analyze", {"text": str(fetched)}, stream=False)

    skill_code = """
from typing import List

def summarize_lengths(items: List[str]) -> int:
    return sum(len(x) for x in items)
"""
    sl.save_skill(name="summarize_lengths", code=skill_code, metadata={"tags": ["utility", "summary"]})

    sk = sl.get_skill("summarize_lengths")
    if sk is None:
        print("Skill not found")
        return

    code = Path(cast(str, sk.code_path)).read_text()
    scope: dict[str, Any] = {}
    exec(code, scope)
    total_len = scope["summarize_lengths"]([analysis.get("summary", ""), "second input"])

    stored = await orch.execute_tool("store_data", {"collection": "results", "document": {"total_len": total_len}})

    print("Fetched:", fetched)
    print("Analysis:", analysis)
    print("Stored:", stored)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
