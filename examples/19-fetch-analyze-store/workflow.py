import asyncio

# Optional imports with fallbacks so this example can be smoke-tested without full install
try:
    from orchestrator import Orchestrator as _CoreOrchestrator  # type: ignore
except Exception:
    _CoreOrchestrator = None

try:
    from orchestrator._internal.observability.monitoring import (
        ToolUsageMonitor as MonitoringBackend,  # type: ignore
    )
except Exception:  # Minimal no-op fallback
    class MonitoringBackend:  # type: ignore
        def log_tool_call(self, *_, **__):
            return None

# Provide an Orchestrator symbol for tests to monkeypatch
Orchestrator = _CoreOrchestrator if _CoreOrchestrator is not None else object  # type: ignore


async def main():
    orchestrator = Orchestrator()
    monitoring = MonitoringBackend()  # uses default configured backend

    # 1) Discover capabilities (tools + agents)
    catalog = await orchestrator.discover_tools(use_cache=True)
    print(f"Discovered {len(catalog)} capabilities (tools + agents)")

    # 2) Fetch data via tool (deterministic)
    fetch_params = {"source": "s3://example-bucket/raw.json"}
    fetch_result = await orchestrator.execute_tool("fetch_data", fetch_params)
    monitoring.log_tool_call("fetch_data", success=True, latency_ms=0, cost=0.0)

    # 3) Analyze via agent (streaming)
    analysis_req = {"payload": fetch_result.get("data"), "mode": "summarize"}
    analysis_result = await orchestrator.execute_agent_step(
        agent_name="analysis_agent",
        request=analysis_req,
        stream=True,
    )

    # 4) Store structured result via tool
    store_params = {"destination": "s3://example-bucket/analysis.json", "data": analysis_result}
    store_result = await orchestrator.execute_tool("store_data", store_params)
    monitoring.log_tool_call("store_data", success=True, latency_ms=0, cost=0.0)

    print("Analysis complete. Stored:", store_result)


if __name__ == "__main__":
    asyncio.run(main())
