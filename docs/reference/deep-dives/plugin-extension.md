# Plugin Extension

## Simple Explanation
Add tools to ToolWeaver without modifying core code by registering a plugin that provides tools and an execution method.

## Technical Explanation
Plugins implement `get_tools()` and `execute()`. Register at runtime with `register_plugin(name, plugin)`, retrieve via `get_plugin(name)`, list with `list_plugins()`. The registry validates names, uniqueness, and interface compliance.

**When to use**
- Third‑party integrations or domain‑specific tools
- Runtime extensions in apps without forking core

**Key Primitives**
- `register_plugin()` / `unregister_plugin()`
- `get_plugin()` / `list_plugins()` / `discover_plugins()`
- `PluginProtocol` — required interface

**Try it**
- Run the sample: [samples/31-plugin-extension/plugin_demo.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/31-plugin-extension/plugin_demo.py)
- See the README: [samples/31-plugin-extension/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/31-plugin-extension/README.md)

**Why run this**
- Add tools at runtime without forking core code
- Validate plugin interface and registry behavior quickly
- Prototype integrations to gauge fit before packaging

**Gotchas**
- Enforce unique tool names across plugins
- Handle async `execute()` correctly; return structured dicts
- Use entry points for discovery in packaged plugins
