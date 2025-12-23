# FAQ

**Q: Where should I import from?**
Use the public API in `orchestrator`. Avoid `_internal`.

**Q: Are decorators available yet?**
Placeholders exist; full decorators land in Phase 2.

**Q: How do I handle optional deps?**
Install extras (e.g., `pip install toolweaver[monitoring]`) and use error helpers.

**Q: How do I add my own tools today?**
Publish a plugin package and register via `orchestrator.plugins.register_plugin`.
