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
    err_msg: str | None = None
    try:
        # 1) Attempt main operation
        main_params = {"resource": "dataset_A", "action": "process"}
        main_result = await orchestrator.execute_tool("process_resource", main_params)
        print("Success on first try:", main_result)
        return
    except Exception as e:  # Simplified for example
        print("Initial failure:", e)
        err_msg = str(e)

    # 2) Diagnose via agent
    diag_req = {"resource": "dataset_A", "error": err_msg or "unknown"}
    diagnosis = await orchestrator.execute_agent_step(
        agent_name="diagnostic_agent",
        request=diag_req,
    )
    print("Diagnosis:", diagnosis)

    # 3) Remediate via tool/agent
    fix_req = {"resource": "dataset_A", "instructions": diagnosis}
    remediation = await orchestrator.execute_agent_step(
        agent_name="remediation_agent",
        request=fix_req,
    )
    print("Remediation:", remediation)

    # 4) Retry original operation
    retry_result = await orchestrator.execute_tool("process_resource", main_params)
    print("Retry result:", retry_result)


if __name__ == "__main__":
    asyncio.run(main())
