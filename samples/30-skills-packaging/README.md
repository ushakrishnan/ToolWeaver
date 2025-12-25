# Skills Packaging & Reuse

Demonstrates how to package a tool as a skill, load it back, and keep tools in sync with the skill library.

## Run
```bash
python samples/30-skills-packaging/skills_demo.py
```

## Prerequisites
- Install from PyPI:
```bash
pip install toolweaver
```

## What it shows
- Define a tool via decorator
- Fetch its `ToolDefinition`
- Save it as a skill (`save_tool_as_skill`)
- Load it back as a tool (`load_tool_from_skill`)
- Optionally sync to latest version (`sync_tool_with_skill`)
