from __future__ import annotations

from aiohttp import web

# Simple nested schema for demo
NESTED_SCHEMA = {
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "profile": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["age"],
                },
            },
            "required": ["id"],
        }
    },
    "required": ["user"],
}

TOOLS = [
    {
        "name": "process_user",
        "type": "mcp",
        "description": "Process nested user payload",
        "parameters": [],
        "input_schema": NESTED_SCHEMA,
        "output_schema": {"type": "object"},
        "metadata": {"source": "mock_mcp"},
        "source": "external_mcp",
    }
]

async def tools_handler(request: web.Request) -> web.Response:
    return web.json_response(TOOLS)

async def execute_handler(request: web.Request) -> web.Response:
    data = await request.json()
    name = data.get("name")
    params = data.get("params", {})
    if name == "process_user":
        # Echo back the nested payload for demo
        return web.json_response({"ok": True, "echo": params})
    return web.json_response({"error": "unknown tool"}, status=400)


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/tools", tools_handler)
    app.router.add_post("/execute", execute_handler)
    return app

if __name__ == "__main__":
    web.run_app(create_app(), port=9876)
