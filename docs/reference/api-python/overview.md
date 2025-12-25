# Python Public API Overview

ToolWeaver exposes a clean, package-first API via `orchestrator`. This section documents grouped capabilities with why/what/how and examples.

## Simple Explanation
The Python API gives you clear building blocks to register, discover, and run tools. Most teams start with decorators to turn functions into tools; use templates when you need full control; use YAML loaders to configure tools without code.

## Technical Explanation
The public surface lives under `orchestrator.*` and is organized by domains: registration (decorators, templates, YAML), catalog (discovery/search), runtime (configuration, logging), extension (plugins, skills), and interop (A2A). Use the Exports Index for a flat symbol lookup and the group pages for patterns and examples.

How to navigate:
- Start with these guides for concepts and examples: Decorators, Templates, YAML loaders, Skill bridge, Discovery, Plugins, Configuration, Logging, A2A client, Version & security.
- Need a symbol fast? Jump to the flat [API Exports Index](exports/index.md).
- Calling over HTTP instead of Python? See the [REST API Overview](../api-rest/overview.md).
- Prefer runnable code? Browse the [Samples index](../../samples/index.md).

Groups:
- Decorators: register tools quickly with type-hinted functions
- Templates: full-control classes for tool definitions
- YAML loaders: config-driven registration
- Skill bridge: save/load tools as reusable skills
- Discovery/search: list, search, browse tools
- Plugins: extend ToolWeaver
- Configuration: manage runtime settings
- Logging: observability helpers
- Agent-to-agent client (A2A): delegate work to other agents
- Version & security: package version and auto secrets redaction

Start with the quick summary: [Public API](../api.md), then dive into groups below.