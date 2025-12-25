# Skills Packaging & Reuse

## Simple Explanation
Save a tool as a reusable skill, load it back later, and keep tools synced to the latest skill version.

## Technical Explanation
Use `save_tool_as_skill()` to persist a tool's source and metadata into the skill library, `load_tool_from_skill()` to reconstruct a runnable tool (definition + function), and `sync_tool_with_skill()` to update a tool to the latest version. This enables versioning and sharing across projects.

**When to use**
- You want a portable, versioned catalog of tools across teams
- You need to pin or upgrade tool versions deterministically

**Key Primitives**
- `save_tool_as_skill()` — persist source + metadata
- `load_tool_from_skill()` — reconstruct tool from library
- `sync_tool_with_skill()` — update to latest version
- `get_tool_skill()` — view backing skill metadata

**Try it**
- Run the sample: [samples/30-skills-packaging/skills_demo.py](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/30-skills-packaging/skills_demo.py)
- See the README: [samples/30-skills-packaging/README.md](https://github.com/ushakrishnan/ToolWeaver/blob/main/samples/30-skills-packaging/README.md)

**Why run this**
- Establish a versioned tool catalog for teams
- Practice saving/loading tools as skills without changing app code
- Learn how to sync tools across environments reproducibly

**Gotchas**
- Ensure decorators are stripped when saving source; library runs plain functions
- Use semantic versioning to communicate changes
- Validate payload schemas across versions to prevent runtime breaks
