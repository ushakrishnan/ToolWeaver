import asyncio
from typing import Dict, Any
from . import workers, code_exec_worker

_tool_map = {
    "receipt_ocr": workers.receipt_ocr_worker,
    "line_item_parser": workers.line_item_parser_worker,
    "expense_categorizer": workers.expense_categorizer_worker,
    "code_exec": code_exec_worker.code_exec_worker
}

_idempotency_store = {}

class MCPClientShim:
    def __init__(self):
        self.tool_map = _tool_map

    async def call_tool(self, tool_name: str, payload: Dict[str,Any], idempotency_key: str = None, timeout: int = 30):
        if idempotency_key and idempotency_key in _idempotency_store:
            return _idempotency_store[idempotency_key]

        coro = self.tool_map[tool_name](payload)
        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise RuntimeError(f"Tool {tool_name} timed out after {timeout}s")
        if idempotency_key:
            _idempotency_store[idempotency_key] = result
        return result
