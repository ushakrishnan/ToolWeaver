"""Tests for workspace skill persistence."""

import shutil
import tempfile
from pathlib import Path

import pytest

from orchestrator._internal.execution.workspace import (
    SkillNotFound,
    WorkspaceManager,
    WorkspaceQuota,
    WorkspaceQuotaExceeded,
    WorkspaceSkill,
)


@pytest.fixture
def temp_workspace():
    """Create temporary workspace directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def workspace(temp_workspace):
    """Create WorkspaceManager instance."""
    return WorkspaceManager(
        session_id="test-session",
        workspace_root=temp_workspace
    )


class TestWorkspaceSkill:
    """Test WorkspaceSkill dataclass."""

    def test_create_skill(self):
        """Test creating a skill."""
        skill = WorkspaceSkill(
            name="test_skill",
            code="def hello(): return 'world'",
            description="A test skill"
        )

        assert skill.name == "test_skill"
        assert skill.version == 1
        assert skill.hash != ""
        assert len(skill.dependencies) == 0

    def test_skill_to_dict(self):
        """Test converting skill to dictionary."""
        skill = WorkspaceSkill(
            name="test",
            code="code",
            description="desc"
        )

        data = skill.to_dict()

        assert isinstance(data, dict)
        assert data["name"] == "test"
        assert "created_at" in data

    def test_skill_from_dict(self):
        """Test creating skill from dictionary."""
        data = {
            "name": "test",
            "code": "code",
            "description": "desc",
            "version": 1,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "dependencies": ["numpy"],
            "tags": ["ml"],
            "examples": [],
            "hash": "abc123"
        }

        skill = WorkspaceSkill.from_dict(data)

        assert skill.name == "test"
        assert skill.dependencies == ["numpy"]
        assert skill.tags == ["ml"]

    def test_skill_to_markdown(self):
        """Test converting skill to markdown."""
        skill = WorkspaceSkill(
            name="data_parser",
            code="def parse(data): return data",
            description="Parse data",
            dependencies=["pandas"],
            tags=["data", "parsing"],
            examples=["parse({'a': 1})"]
        )

        md = skill.to_markdown()

        assert "# data_parser" in md
        assert "Parse data" in md
        assert "pandas" in md
        assert "data, parsing" in md
        assert "```python" in md

    def test_skill_from_markdown(self):
        """Test parsing skill from markdown."""
        md = """# test_skill

A test skill

**Tags**: test, demo

## Dependencies

- `numpy`
- `pandas`

## Code

```python
def hello():
    return 'world'
```

## Examples

### Example 1

```python
result = hello()
```

## Metadata

- Version: 2
- Created: 2024-01-01T00:00:00
- Updated: 2024-01-02T00:00:00
- Hash: `abc123`
"""

        skill = WorkspaceSkill.from_markdown(md)

        assert skill.name == "test_skill"
        assert "test skill" in skill.description.lower()
        assert skill.version == 2
        assert "numpy" in skill.dependencies
        assert "pandas" in skill.dependencies
        assert "test" in skill.tags
        assert "hello" in skill.code


class TestWorkspaceManager:
    """Test WorkspaceManager."""

    def test_create_workspace(self, workspace):
        """Test creating workspace."""
        assert workspace.workspace_dir.exists()
        assert workspace.skills_dir.exists()
        assert workspace.intermediate_dir.exists()
        assert workspace.metadata_file.exists()

    def test_save_skill(self, workspace):
        """Test saving a skill."""
        skill = workspace.save_skill(
            name="test_parser",
            code="def parse(data): return data",
            description="A test parser",
            dependencies=["pandas"],
            tags=["parsing"]
        )

        assert skill.name == "test_parser"
        assert skill.version == 1
        assert (workspace.skills_dir / "test_parser.json").exists()
        assert (workspace.skills_dir / "test_parser.md").exists()

    def test_load_skill(self, workspace):
        """Test loading a skill."""
        # Save skill first
        workspace.save_skill(
            name="loader_test",
            code="def load(): pass",
            description="Test loading"
        )

        # Load it
        skill = workspace.load_skill("loader_test")

        assert skill.name == "loader_test"
        assert "def load()" in skill.code

    def test_load_nonexistent_skill(self, workspace):
        """Test loading skill that doesn't exist."""
        with pytest.raises(SkillNotFound):
            workspace.load_skill("nonexistent")

    def test_skill_versioning(self, workspace):
        """Test that updating skill increments version."""
        # Save initial version
        skill_v1 = workspace.save_skill(
            name="versioned",
            code="def v1(): pass",
            description="Version 1"
        )

        assert skill_v1.version == 1

        # Save updated version
        skill_v2 = workspace.save_skill(
            name="versioned",
            code="def v2(): pass",
            description="Version 2"
        )

        assert skill_v2.version == 2

    def test_list_skills(self, workspace):
        """Test listing skills."""
        # Save multiple skills
        workspace.save_skill("skill1", "code1", "desc1")
        workspace.save_skill("skill2", "code2", "desc2", tags=["tag1"])
        workspace.save_skill("skill3", "code3", "desc3", tags=["tag2"])

        # List all
        all_skills = workspace.list_skills()
        assert len(all_skills) == 3

        # Filter by tag
        tagged = workspace.list_skills(tags=["tag1"])
        assert len(tagged) == 1
        assert tagged[0].name == "skill2"

    def test_delete_skill(self, workspace):
        """Test deleting a skill."""
        # Save skill
        workspace.save_skill("to_delete", "code", "desc")

        # Verify it exists
        skill = workspace.load_skill("to_delete")
        assert skill is not None

        # Delete it
        workspace.delete_skill("to_delete")

        # Verify it's gone
        with pytest.raises(SkillNotFound):
            workspace.load_skill("to_delete")

    def test_delete_nonexistent_skill(self, workspace):
        """Test deleting skill that doesn't exist."""
        with pytest.raises(SkillNotFound):
            workspace.delete_skill("nonexistent")

    def test_save_intermediate(self, workspace):
        """Test saving intermediate data."""
        data = {"result": [1, 2, 3], "status": "complete"}

        workspace.save_intermediate("query_result", data)

        # Verify file exists
        intermediate_file = workspace.intermediate_dir / "query_result.json"
        assert intermediate_file.exists()

    def test_load_intermediate(self, workspace):
        """Test loading intermediate data."""
        # Save data
        data = {"value": 42}
        workspace.save_intermediate("test_data", data)

        # Load it
        loaded = workspace.load_intermediate("test_data")

        assert loaded == data
        assert loaded["value"] == 42

    def test_load_nonexistent_intermediate(self, workspace):
        """Test loading intermediate that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            workspace.load_intermediate("nonexistent")

    def test_list_intermediates(self, workspace):
        """Test listing intermediate files."""
        workspace.save_intermediate("data1", {"a": 1})
        workspace.save_intermediate("data2", {"b": 2})

        intermediates = workspace.list_intermediates()

        assert len(intermediates) == 2
        assert "data1" in intermediates
        assert "data2" in intermediates

    def test_get_workspace_stats(self, workspace):
        """Test getting workspace statistics."""
        # Add some data
        workspace.save_skill("skill1", "code", "desc")
        workspace.save_intermediate("data1", {"a": 1})

        stats = workspace.get_workspace_stats()

        assert stats["session_id"] == "test-session"
        assert stats["skills"] == 1
        assert stats["intermediates"] == 1
        assert stats["total_size_bytes"] > 0
        assert "created_at" in stats

    def test_clear_workspace(self, workspace):
        """Test clearing workspace."""
        # Add data
        workspace.save_skill("skill1", "code", "desc")
        workspace.save_intermediate("data1", {"a": 1})

        # Verify data exists
        assert len(workspace.list_skills()) == 1
        assert len(workspace.list_intermediates()) == 1

        # Clear workspace
        workspace.clear_workspace()

        # Verify data is gone
        assert len(workspace.list_skills()) == 0
        assert len(workspace.list_intermediates()) == 0

        stats = workspace.get_workspace_stats()
        assert stats["skills"] == 0
        assert stats["total_size_bytes"] == 0


class TestWorkspaceQuota:
    """Test workspace quota enforcement."""

    def test_quota_max_size(self, temp_workspace):
        """Test max size quota."""
        # Create workspace with small quota
        quota = WorkspaceQuota(max_size_bytes=1000)
        workspace = WorkspaceManager(
            session_id="quota-test",
            workspace_root=temp_workspace,
            quota=quota
        )

        # Try to save large skill
        large_code = "x = 1\n" * 1000  # ~6KB

        with pytest.raises(WorkspaceQuotaExceeded):
            workspace.save_skill("large", large_code, "Large skill")

    def test_quota_max_files(self, temp_workspace):
        """Test max files quota."""
        # Create workspace with small file limit
        quota = WorkspaceQuota(max_files=2)
        workspace = WorkspaceManager(
            session_id="quota-test",
            workspace_root=temp_workspace,
            quota=quota
        )

        # Save two skills (should work)
        workspace.save_skill("skill1", "code1", "desc1")
        workspace.save_skill("skill2", "code2", "desc2")

        # Try to save third (should fail)
        with pytest.raises(WorkspaceQuotaExceeded):
            workspace.save_skill("skill3", "code3", "desc3")

    def test_quota_max_skill_size(self, temp_workspace):
        """Test max skill size quota."""
        # Create workspace with small per-skill limit
        quota = WorkspaceQuota(max_skill_size=100)
        workspace = WorkspaceManager(
            session_id="quota-test",
            workspace_root=temp_workspace,
            quota=quota
        )

        # Try to save large skill
        large_code = "x = 1\n" * 100

        with pytest.raises(WorkspaceQuotaExceeded):
            workspace.save_skill("large", large_code, "Large skill")

    def test_quota_max_intermediate_size(self, temp_workspace):
        """Test max intermediate size quota."""
        # Create workspace with small per-intermediate limit
        quota = WorkspaceQuota(max_intermediate_size=100)
        workspace = WorkspaceManager(
            session_id="quota-test",
            workspace_root=temp_workspace,
            quota=quota
        )

        # Try to save large intermediate
        large_data = {"data": ["x" * 1000]}

        with pytest.raises(WorkspaceQuotaExceeded):
            workspace.save_intermediate("large", large_data)


class TestWorkspaceIntegration:
    """Integration tests for realistic workflows."""

    def test_agent_workflow(self, workspace):
        """Test realistic agent workflow."""
        # Step 1: Agent writes data parser skill
        parser_skill = workspace.save_skill(
            name="csv_parser",
            code="""
def parse_csv(data):
    lines = data.strip().split('\\n')
    headers = lines[0].split(',')
    rows = []
    for line in lines[1:]:
        values = line.split(',')
        rows.append(dict(zip(headers, values)))
    return rows
""",
            description="Parse CSV data into list of dicts",
            dependencies=[],
            tags=["parsing", "csv"],
            examples=[
                "data = 'name,age\\nAlice,30\\nBob,25'",
                "result = parse_csv(data)"
            ]
        )

        assert parser_skill.version == 1

        # Step 2: Agent uses skill and saves intermediate result
        # (In real scenario, agent would exec() the code)
        csv_data = "name,age\nAlice,30\nBob,25"
        # parsed = parse_csv(csv_data)  # Would execute skill code
        parsed = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

        workspace.save_intermediate("parsed_users", parsed)

        # Step 3: Agent creates aggregation skill
        workspace.save_skill(
            name="count_by_age",
            code="""
def count_by_age(users):
    from collections import Counter
    ages = [u['age'] for u in users]
    return dict(Counter(ages))
""",
            description="Count users by age",
            dependencies=["collections"],
            tags=["aggregation"]
        )

        # Step 4: Agent resumes session, loads previous work
        loaded_users = workspace.load_intermediate("parsed_users")
        assert len(loaded_users) == 2

        parser = workspace.load_skill("csv_parser")
        assert "parse_csv" in parser.code

        # Step 5: Check workspace stats
        stats = workspace.get_workspace_stats()
        assert stats["skills"] == 2
        assert stats["intermediates"] == 1

    def test_skill_evolution(self, workspace):
        """Test skill being updated over time."""
        # Version 1: Basic implementation
        v1 = workspace.save_skill(
            name="transformer",
            code="def transform(x): return x * 2",
            description="Transform data v1"
        )
        assert v1.version == 1

        # Version 2: Improved implementation
        v2 = workspace.save_skill(
            name="transformer",
            code="def transform(x, multiplier=2): return x * multiplier",
            description="Transform data v2 with configurable multiplier"
        )
        assert v2.version == 2

        # Version 3: Add validation
        v3 = workspace.save_skill(
            name="transformer",
            code="""
def transform(x, multiplier=2):
    if not isinstance(x, (int, float)):
        raise ValueError("x must be numeric")
    return x * multiplier
""",
            description="Transform data v3 with validation"
        )
        assert v3.version == 3

        # Load latest version
        latest = workspace.load_skill("transformer")
        assert latest.version == 3
        assert "ValueError" in latest.code

    def test_multi_agent_workspace(self, temp_workspace):
        """Test multiple agents with separate workspaces."""
        # Agent 1 workspace
        agent1 = WorkspaceManager("agent-1", temp_workspace)
        agent1.save_skill("agent1_skill", "code1", "Agent 1 skill")

        # Agent 2 workspace
        agent2 = WorkspaceManager("agent-2", temp_workspace)
        agent2.save_skill("agent2_skill", "code2", "Agent 2 skill")

        # Verify isolation
        assert len(agent1.list_skills()) == 1
        assert len(agent2.list_skills()) == 1

        # Verify distinct skills
        assert agent1.list_skills()[0].name == "agent1_skill"
        assert agent2.list_skills()[0].name == "agent2_skill"

        # Agent 1 cannot access Agent 2's skills
        with pytest.raises(SkillNotFound):
            agent1.load_skill("agent2_skill")
