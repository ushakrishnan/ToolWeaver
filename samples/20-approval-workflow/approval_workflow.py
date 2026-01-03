import asyncio

# Optional import with fallback so this example can be smoke-tested without full install
try:
    from orchestrator import Orchestrator as _CoreOrchestrator  # type: ignore
except Exception:
    _CoreOrchestrator = None

# Provide an Orchestrator symbol for tests to monkeypatch
Orchestrator = _CoreOrchestrator if _CoreOrchestrator is not None else object  # type: ignore


async def main():
    orchestrator = Orchestrator()

    # 1) Draft via agent
    draft_req = {"task": "summarize PR #123", "tone": "concise"}
    draft = await orchestrator.execute_agent_step(
        agent_name="analysis_agent",
        request=draft_req,
        stream=True,
    )
    print("Draft:\n", draft)

    # 2) Validate via agent
    validation_req = {"content": draft, "policy": "security"}
    validation = await orchestrator.execute_agent_step(
        agent_name="validator_agent",
        request=validation_req,
    )
    print("Validation:\n", validation)

    # 3) Human approval (simplified prompt)
    approval = input("Approve? (y/n): ").strip().lower()
    if approval != "y":
        print("Rejected. No changes applied.")
        return

    # 4) Apply changes via tool
    apply_params = {"content": draft, "target": "prod"}
    result = await orchestrator.execute_tool("apply_changes", apply_params)
    print("Applied:", result)


if __name__ == "__main__":
    asyncio.run(main())
