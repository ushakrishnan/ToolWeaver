"""
Tests for tool composition.
"""

import asyncio

import pytest

from orchestrator.tools.composition import (
    CompositionChain,
    CompositionExecutor,
    CompositionStep,
    build_parameter_mapping,
    composite_tool,
)


@pytest.mark.asyncio
async def test_basic_linear_chain_execution():
    async def step1_tool(input_value: str) -> dict:
        return {"output": input_value.upper(), "length": len(input_value)}

    async def step2_tool(output: str) -> dict:
        return {"result": output + "!", "processed": True}

    executor = CompositionExecutor(
        tool_resolver=lambda ref: {"step1": step1_tool, "step2": step2_tool}.get(ref)
    )

    chain = (
        CompositionChain(name="test_chain")
        .add_step(
            CompositionStep(
                name="step1",
                tool_ref="step1",
                input_schema={"input_value": str},
            )
        )
        .add_step(
            CompositionStep(
                name="step2",
                tool_ref="step2",
                input_schema={"output": str},
                output_mapping={"output": "output"},
            )
        )
    )

    result = await executor.execute(chain, {"input_value": "hello"})

    assert result.success
    assert result.step_results["step1"]["output"] == "HELLO"
    assert result.step_results["step2"]["result"] == "HELLO!"
    assert result.final_output["result"] == "HELLO!"


@pytest.mark.asyncio
async def test_chain_validation_empty():
    executor = CompositionExecutor()
    chain = CompositionChain(name="empty_chain")
    result = await executor.execute(chain, {})
    assert not result.success
    assert "no steps" in result.error.lower()


@pytest.mark.asyncio
async def test_step_timeout_handling():
    async def slow_tool(value: str) -> dict:
        await asyncio.sleep(1.0)
        return {"result": value}

    executor = CompositionExecutor(
        tool_resolver=lambda ref: slow_tool if ref == "slow" else None
    )

    chain = (
        CompositionChain(name="timeout_test")
        .add_step(
            CompositionStep(
                name="slow_step",
                tool_ref="slow",
                input_schema={"value": str},
                timeout_sec=0.1,
            )
        )
    )

    result = await executor.execute(chain, {"value": "test"})
    assert not result.success
    assert "timeout" in result.error.lower()


@pytest.mark.asyncio
async def test_step_error_propagation_raise():
    async def fail_tool(value: str) -> dict:
        raise ValueError("Expected failure")

    executor = CompositionExecutor(
        tool_resolver=lambda ref: fail_tool
    )

    chain = (
        CompositionChain(name="error_test")
        .add_step(
            CompositionStep(
                name="fail_step",
                tool_ref="fail",
                input_schema={"value": str},
                on_error="raise",
            )
        )
    )

    result = await executor.execute(chain, {"value": "test"})
    assert not result.success
    assert "Expected failure" in result.error


@pytest.mark.asyncio
async def test_step_error_continue():
    async def fail_tool(value: str) -> dict:
        raise ValueError("Expected failure")

    async def pass_tool(value: str = None) -> dict:
        return {"result": "recovered"}

    async def resolver(ref: str):
        return {"fail": fail_tool, "pass": pass_tool}.get(ref)

    executor = CompositionExecutor(tool_resolver=resolver)

    chain = (
        CompositionChain(name="continue_test")
        .add_step(
            CompositionStep(
                name="fail_step",
                tool_ref="fail",
                input_schema={"value": str},
                on_error="continue",
            )
        )
        .add_step(
            CompositionStep(
                name="pass_step",
                tool_ref="pass",
                input_schema={"value": str},
            )
        )
    )

    result = await executor.execute(chain, {"value": "test"})
    assert result.success
    assert result.step_results["fail_step"] is None
    assert result.step_results["pass_step"]["result"] == "recovered"


@pytest.mark.asyncio
async def test_parameter_mapping_passthrough():
    data = {"name": "Alice", "age": 30, "email": "alice@example.com"}
    schema = {"name": str, "age": int}

    mapped = build_parameter_mapping(data, schema)
    assert mapped == {"name": "Alice", "age": 30}


@pytest.mark.asyncio
async def test_parameter_mapping_explicit():
    data = {"source_name": "Bob", "source_age": 25}
    schema = {"name": str, "age": int}
    explicit = {"name": "source_name", "age": "source_age"}

    mapped = build_parameter_mapping(data, schema, explicit)
    assert mapped == {"name": "Bob", "age": 25}


@pytest.mark.asyncio
async def test_composite_tool_decorator():
    @composite_tool(name="test_comp", description="Test composition")
    def my_chain():
        return CompositionChain(name="test_comp").add_step(
            CompositionStep(name="step1", tool_ref="t1", input_schema={})
        )

    chain = my_chain()
    assert chain.name == "test_comp"
    assert chain.description == "Test composition"
    assert len(chain.steps) == 1


def test_composition_step_validates_on_error():
    with pytest.raises(ValueError):
        CompositionStep(
            name="bad",
            tool_ref="t",
            on_error="invalid",
        )


@pytest.mark.asyncio
async def test_retry_on_transient_failure():
    call_count = 0

    async def flaky_tool(value: str) -> dict:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise RuntimeError("Transient error")
        return {"result": value, "attempts": call_count}

    executor = CompositionExecutor(
        tool_resolver=lambda ref: flaky_tool if ref == "flaky" else None
    )

    chain = (
        CompositionChain(name="retry_test")
        .add_step(
            CompositionStep(
                name="flaky_step",
                tool_ref="flaky",
                input_schema={"value": str},
                retry_count=2,
            )
        )
    )

    result = await executor.execute(chain, {"value": "test"})
    assert result.success
    assert result.step_results["flaky_step"]["attempts"] == 2


@pytest.mark.asyncio
async def test_sync_tool_support():
    def sync_tool(value: str) -> dict:
        return {"result": value.upper()}

    executor = CompositionExecutor(
        tool_resolver=lambda ref: sync_tool
    )

    chain = (
        CompositionChain(name="sync_test")
        .add_step(
            CompositionStep(
                name="sync_step",
                tool_ref="sync",
                input_schema={"value": str},
            )
        )
    )

    result = await executor.execute(chain, {"value": "hello"})
    assert result.success
    assert result.step_results["sync_step"]["result"] == "HELLO"


@pytest.mark.asyncio
async def test_three_step_chain():
    async def fetch(url: str) -> dict:
        return {"content": f"<html>{url}</html>"}

    async def parse(content: str) -> dict:
        return {"title": "Parsed", "body": content}

    async def extract(body: str) -> dict:
        return {"extracted": body[:10]}

    async def resolver(ref: str):
        tools = {"fetch": fetch, "parse": parse, "extract": extract}
        return tools.get(ref)

    executor = CompositionExecutor(tool_resolver=resolver)

    chain = (
        CompositionChain(name="fetch_parse_extract")
        .add_step(
            CompositionStep(
                name="fetch",
                tool_ref="fetch",
                input_schema={"url": str},
                output_mapping={"content": "content"},
            )
        )
        .add_step(
            CompositionStep(
                name="parse",
                tool_ref="parse",
                input_schema={"content": str},
                output_mapping={"body": "body"},
            )
        )
        .add_step(
            CompositionStep(
                name="extract",
                tool_ref="extract",
                input_schema={"body": str},
            )
        )
    )

    result = await executor.execute(chain, {"url": "http://example.com"})
    assert result.success
    assert "extracted" in result.final_output
