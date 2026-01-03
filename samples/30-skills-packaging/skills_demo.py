from typing import cast

from orchestrator import (
    get_tool_info,
    get_tool_skill,
    load_tool_from_skill,
    save_tool_as_skill,
    sync_tool_with_skill,
    tool,
)
from orchestrator.shared.models import ToolDefinition


@tool(name="add_numbers", description="Add two integers")
def add_numbers(a: int, b: int) -> dict:
    return {"sum": a + b}


def main() -> None:
    # Get ToolDefinition for our tool
    td = cast(ToolDefinition, get_tool_info("add_numbers", detail_level="full"))
    assert td is not None, "Tool definition not found"

    # Save as a skill
    skill = save_tool_as_skill(td, add_numbers, tags=["demo", "math"])
    print(f"Saved skill: {skill.name}@{skill.version}")

    # Load tool from skill library
    td2, loaded_fn = load_tool_from_skill("add_numbers")
    print(f"Loaded tool from skill: {td2.name} ({td2.description})")

    # Execute loaded function
    result = loaded_fn(2, 3)
    print("Execution result:", result)

    # Optional: show skill backing info and sync
    backing = get_tool_skill("add_numbers")
    if backing:
        print(f"Tool 'add_numbers' backed by skill {backing.name}@{backing.version}")
        synced = sync_tool_with_skill("add_numbers")
        if synced:
            print("Synced to latest skill version.")


if __name__ == "__main__":
    main()
