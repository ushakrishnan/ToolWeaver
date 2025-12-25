# FAQ

## Is ToolWeaver a framework?
No. It’s a package-first library you embed in your apps.

## How do I register tools?
Use decorators (`@mcp_tool`), template classes, or YAML loaders.

## Can I expose tools over HTTP?
Yes—use the FastAPI adapter to expose REST endpoints.

## What about safety?
Secrets redaction, PII filtering, template sanitization, idempotency, and sandboxed execution are built in.

## Do I need Redis?
No. The file cache works by default; Redis adds speed and distribution.

## Does it work with planners?
Yes. You can use ToolWeaver with planners and agents to select and call tools.

See:
- [Python API](../reference/api-python/overview.md)
- [REST API](../reference/api-rest/overview.md)
- [Tutorials](../tutorials/parallel-agents.md)
