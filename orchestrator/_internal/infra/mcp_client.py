import asyncio
import time
from collections import OrderedDict
from typing import Dict, Any, Optional
from ..dispatch.workers import (
    receipt_ocr_worker,
    line_item_parser_worker,
    expense_categorizer_worker,
    fetch_data_worker,
    store_data_worker,
    apply_changes_worker,
    process_resource_worker,
)
from ..execution.code_exec_worker import code_exec_worker

_tool_map = {
    "receipt_ocr": receipt_ocr_worker,
    "line_item_parser": line_item_parser_worker,
    "expense_categorizer": expense_categorizer_worker,
    "code_exec": code_exec_worker,
    # Advanced example utilities
    "fetch_data": fetch_data_worker,
    "store_data": store_data_worker,
    "apply_changes": apply_changes_worker,
    "process_resource": process_resource_worker,
}

_idempotency_store: "OrderedDict[str, tuple[float, Any]]" = OrderedDict()
_IDEMPOTENCY_TTL_S = 600
_IDEMPOTENCY_MAX = 256

class MCPClientShim:
    def __init__(
        self,
        *,
        max_retries: int = 0,
        retry_backoff_s: float = 0.1,
        circuit_breaker_threshold: int = 3,
        circuit_reset_s: int = 30,
        observer: Optional[callable] = None,
    ):
        self.tool_map = _tool_map
        self._max_retries = max_retries
        self._retry_backoff_s = retry_backoff_s
        self._circuit_breaker_threshold = circuit_breaker_threshold
        self._circuit_reset_s = circuit_reset_s
        self._consecutive_failures = 0
        self._circuit_open_until: Optional[float] = None
        self._observer = observer

    async def call_tool(self, tool_name: str, payload: Dict[str, Any], idempotency_key: Optional[str] = None, timeout: int = 30):
        if idempotency_key:
            cached = self._get_cached(idempotency_key)
            if cached is not None:
                self._emit("mcp.cache_hit", {"tool": tool_name, "idempotency_key": idempotency_key})
                return cached

        if self._is_circuit_open():
            raise RuntimeError("MCP circuit open due to recent failures")

        last_exc: Optional[Exception] = None
        self._emit("mcp.start", {"tool": tool_name, "idempotency_key": idempotency_key})
        for attempt in range(self._max_retries + 1):
            coro = self.tool_map[tool_name](payload)
            try:
                result = await asyncio.wait_for(coro, timeout=timeout)
                self._reset_circuit()
                if idempotency_key:
                    self._store(idempotency_key, result)
                self._emit("mcp.complete", {
                    "tool": tool_name,
                    "attempt": attempt + 1,
                    "success": True,
                })
                return result
            except asyncio.TimeoutError as exc:
                last_exc = RuntimeError(f"Tool {tool_name} timed out after {timeout}s")
            except Exception as exc:  # noqa: BLE001
                last_exc = exc

            self._consecutive_failures += 1
            if self._consecutive_failures >= self._circuit_breaker_threshold:
                self._open_circuit()
                break

            if attempt < self._max_retries:
                await asyncio.sleep(self._retry_backoff_s * (2 ** attempt))

        if isinstance(last_exc, RuntimeError):
            raise last_exc
        if last_exc:
            raise last_exc
        self._emit("mcp.complete", {
            "tool": tool_name,
            "attempt": self._max_retries + 1,
            "success": False,
            "error": str(last_exc) if last_exc else "unknown",
        })
        raise RuntimeError("Tool execution failed for unknown reasons")

    async def call_tool_stream(
        self,
        tool_name: str,
        payload: Dict[str, Any],
        *,
        timeout: int = 30,
        chunk_timeout: Optional[float] = None,
    ):
        """Stream tool output as an async generator.

        Notes:
            - Streaming responses are not cached for idempotency.
            - Retries restart the stream; callers should handle potential duplicates.
        """
        if self._is_circuit_open():
            raise RuntimeError("MCP circuit open due to recent failures")

        last_exc: Optional[Exception] = None
        self._emit("mcp.stream.start", {"tool": tool_name})

        for attempt in range(self._max_retries + 1):
            coro = self.tool_map[tool_name](payload)
            try:
                async for chunk in self._iterate_stream(coro, timeout, chunk_timeout):
                    self._emit("mcp.stream.chunk", {
                        "tool": tool_name,
                        "attempt": attempt + 1,
                    })
                    yield chunk
                self._reset_circuit()
                self._emit("mcp.stream.complete", {
                    "tool": tool_name,
                    "attempt": attempt + 1,
                    "success": True,
                })
                return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc

            self._consecutive_failures += 1
            if self._consecutive_failures >= self._circuit_breaker_threshold:
                self._open_circuit()
                break

            if attempt < self._max_retries:
                await asyncio.sleep(self._retry_backoff_s * (2 ** attempt))

        self._emit("mcp.stream.complete", {
            "tool": tool_name,
            "attempt": self._max_retries + 1,
            "success": False,
            "error": str(last_exc) if last_exc else "unknown",
        })
        if last_exc:
            raise last_exc
        raise RuntimeError("Tool stream failed for unknown reasons")

    def _get_cached(self, key: str):
        entry = _idempotency_store.get(key)
        if not entry:
            return None
        ts, val = entry
        if (time.time() - ts) > _IDEMPOTENCY_TTL_S:
            _idempotency_store.pop(key, None)
            return None
        _idempotency_store.move_to_end(key)
        return val

    def _store(self, key: str, val: Any):
        _idempotency_store[key] = (time.time(), val)
        _idempotency_store.move_to_end(key)
        if len(_idempotency_store) > _IDEMPOTENCY_MAX:
            _idempotency_store.popitem(last=False)

    def _is_circuit_open(self) -> bool:
        if self._circuit_open_until is None:
            return False
        if time.time() < self._circuit_open_until:
            return True
        self._reset_circuit()
        return False

    def _open_circuit(self) -> None:
        self._circuit_open_until = time.time() + self._circuit_reset_s

    def _reset_circuit(self) -> None:
        self._consecutive_failures = 0
        self._circuit_open_until = None

    def _emit(self, event: str, data: Dict[str, Any]) -> None:
        if self._observer:
            try:
                self._observer(event, data)
            except Exception:
                pass

    async def _iterate_stream(self, stream_coro, overall_timeout: int, chunk_timeout: Optional[float]):
        """Iterate an async generator with optional per-chunk timeout."""
        iterator = stream_coro.__aiter__()
        while True:
            try:
                next_item = iterator.__anext__()
            except StopAsyncIteration:
                return
            try:
                if chunk_timeout:
                    chunk = await asyncio.wait_for(next_item, timeout=chunk_timeout)
                else:
                    chunk = await asyncio.wait_for(next_item, timeout=overall_timeout)
            except StopAsyncIteration:
                return
            yield chunk
