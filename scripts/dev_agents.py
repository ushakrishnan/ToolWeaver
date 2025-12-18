import asyncio
from aiohttp import web


async def analyze(request: web.Request):
    data = await request.json()
    payload = data.get("context") or data
    result = {"summary": f"analyzed {list(payload.keys())}", "ok": True}
    return web.json_response(result)


async def validate(request: web.Request):
    data = await request.json()
    content = (data.get("context") or {}).get("content")
    result = {"valid": bool(content), "notes": "ok" if content else "empty"}
    return web.json_response(result)


async def diagnose(request: web.Request):
    data = await request.json()
    err = (data.get("context") or {}).get("error", "unknown")
    result = {"diagnosis": f"saw:{err}", "steps": ["retry", "increase_timeout"]}
    return web.json_response(result)


async def remediate(request: web.Request):
    data = await request.json()
    result = {"remediation": "applied", "details": data.get("context")}
    return web.json_response(result)


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_post('/analyze', analyze)
    app.router.add_post('/validate', validate)
    app.router.add_post('/diagnose', diagnose)
    app.router.add_post('/remediate', remediate)
    return app


if __name__ == '__main__':
    web.run_app(create_app(), host='127.0.0.1', port=8089)
