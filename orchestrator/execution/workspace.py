"""
Workspace Skill Persistence

Enables agents to persist reusable code/skills and intermediate outputs to a workspace
for reuse and resumability. Provides sandboxed filesystem with scoped access.

Features:
- Persistent workspace directory per session/agent
- SKILL.md format for documenting reusable code patterns
- Automatic skill discovery and loading
- Quota management (disk space, file count)
- Sandboxed filesystem operations
- Version control for skills

Usage:
    from orchestrator.execution import WorkspaceManager
    
    # Create workspace
    workspace = WorkspaceManager(session_id="agent-123")
    
    # Save skill
    workspace.save_skill(
        name="data_parser",
        code=parser_code,
        description="Parse CSV data",
        dependencies=["pandas"]
    )
    
    # Load skill later
    skill = workspace.load_skill("data_parser")
    exec(skill.code)
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class WorkspaceQuotaExceeded(Exception):
    """Raised when workspace quota is exceeded."""
    pass


class SkillNotFound(Exception):
    """Raised when requested skill doesn't exist."""
    pass


@dataclass
class WorkspaceQuota:
    """Quota limits for workspace."""
    max_size_bytes: int = 100 * 1024 * 1024  # 100MB
    max_files: int = 1000
    max_skill_size: int = 1 * 1024 * 1024  # 1MB per skill
    max_intermediate_size: int = 10 * 1024 * 1024  # 10MB per intermediate file


@dataclass
class WorkspaceSkill:
    """A reusable code skill stored in workspace."""
    name: str
    code: str
    description: str
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    hash: str = ""  # Code hash for integrity
    
    def __post_init__(self) -> None:
        """Calculate code hash after initialization."""
        if not self.hash:
            self.hash = hashlib.sha256(self.code.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkspaceSkill":
        """Create from dictionary."""
        return cls(**data)
    
    def to_markdown(self) -> str:
        """Convert to SKILL.md format.
        
        Returns Markdown documentation for the skill.
        """
        md = f"# {self.name}\n\n"
        md += f"{self.description}\n\n"
        
        if self.tags:
            md += f"**Tags**: {', '.join(self.tags)}\n\n"
        
        if self.dependencies:
            md += "## Dependencies\n\n"
            for dep in self.dependencies:
                md += f"- `{dep}`\n"
            md += "\n"
        
        md += "## Code\n\n"
        md += f"```python\n{self.code}\n```\n\n"
        
        if self.examples:
            md += "## Examples\n\n"
            for i, example in enumerate(self.examples, 1):
                md += f"### Example {i}\n\n"
                md += f"```python\n{example}\n```\n\n"
        
        md += "## Metadata\n\n"
        md += f"- Version: {self.version}\n"
        md += f"- Created: {self.created_at}\n"
        md += f"- Updated: {self.updated_at}\n"
        md += f"- Hash: `{self.hash}`\n"
        
        return md
    
    @classmethod
    def from_markdown(cls, md: str) -> "WorkspaceSkill":
        """Parse from SKILL.md format.
        
        Basic parser that extracts code and metadata from markdown.
        """
        import re
        
        # Extract name from # heading
        name_match = re.search(r'^# (.+)$', md, re.MULTILINE)
        name = name_match.group(1) if name_match else "unnamed"
        
        # Extract description (text between heading and **Tags** or ##)
        # Try Tags first, then ## section
        desc_match = re.search(r'^# .+?\n+(.+?)\n+\*\*Tags\*\*', md, re.DOTALL | re.MULTILINE)
        if not desc_match:
            desc_match = re.search(r'^# .+?\n+(.+?)\n+##', md, re.DOTALL | re.MULTILINE)
        description = desc_match.group(1).strip() if desc_match else ""
        
        # Extract code from ```python blocks
        code_blocks = re.findall(r'```python\n(.+?)\n```', md, re.DOTALL)
        code = code_blocks[0] if code_blocks else ""
        
        # Extract dependencies
        deps_match = re.search(r'## Dependencies\n\n((?:- `.+`\n)+)', md)
        dependencies = []
        if deps_match:
            dependencies = re.findall(r'- `(.+)`', deps_match.group(1))
        
        # Extract tags
        tags_match = re.search(r'\*\*Tags\*\*: (.+)', md)
        tags = []
        if tags_match:
            tags = [tag.strip() for tag in tags_match.group(1).split(',')]
        
        # Extract examples (skip first code block which is the main code)
        examples = code_blocks[1:] if len(code_blocks) > 1 else []
        
        # Extract metadata
        version_match = re.search(r'- Version: (\d+)', md)
        version = int(version_match.group(1)) if version_match else 1
        
        created_match = re.search(r'- Created: (.+)', md)
        created_at = created_match.group(1) if created_match else datetime.now(timezone.utc).isoformat()
        
        updated_match = re.search(r'- Updated: (.+)', md)
        updated_at = updated_match.group(1) if updated_match else datetime.now(timezone.utc).isoformat()
        
        hash_match = re.search(r'- Hash: `(.+)`', md)
        hash_val = hash_match.group(1) if hash_match else ""
        
        return cls(
            name=name,
            code=code,
            description=description,
            version=version,
            created_at=created_at,
            updated_at=updated_at,
            dependencies=dependencies,
            tags=tags,
            examples=examples,
            hash=hash_val
        )


class WorkspaceManager:
    """Manages persistent workspace for agent skills and intermediate outputs.
    
    Example:
        workspace = WorkspaceManager(session_id="agent-123")
        
        # Save skill
        workspace.save_skill(
            name="data_parser",
            code="def parse(data): ...",
            description="Parse CSV data"
        )
        
        # Load skill
        skill = workspace.load_skill("data_parser")
        
        # Save intermediate output
        workspace.save_intermediate("query_results", data)
        
        # Load intermediate output
        data = workspace.load_intermediate("query_results")
    """
    
    def __init__(
        self,
        session_id: str,
        workspace_root: Optional[Path] = None,
        quota: Optional[WorkspaceQuota] = None
    ) -> None:
        """Initialize workspace manager.
        
        Args:
            session_id: Unique identifier for this workspace
            workspace_root: Root directory for all workspaces (default: ./.toolweaver/workspaces)
            quota: Quota limits for workspace
        """
        self.session_id = session_id
        self.quota = quota or WorkspaceQuota()
        
        # Set workspace root
        if workspace_root is None:
            workspace_root = Path.cwd() / ".toolweaver" / "workspaces"
        
        self.workspace_root = Path(workspace_root)
        self.workspace_dir = self.workspace_root / session_id
        
        # Create workspace directories
        self.skills_dir = self.workspace_dir / "skills"
        self.intermediate_dir = self.workspace_dir / "intermediate"
        self.metadata_file = self.workspace_dir / "metadata.json"
        
        self.metadata: Dict[str, Any] = {}
        self._ensure_directories()
        self._load_metadata()
    
    def _ensure_directories(self) -> None:
        """Create workspace directories if they don't exist."""
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.intermediate_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_metadata(self) -> None:
        """Load workspace metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "session_id": self.session_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "skill_count": 0,
                "intermediate_count": 0,
                "total_size": 0,
            }
            self._save_metadata()
    
    def _save_metadata(self) -> None:
        """Save workspace metadata."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _check_quota(self, size: int, is_skill: bool = True) -> None:
        """Check if adding a file would exceed quota.
        
        Args:
            size: Size of file in bytes
            is_skill: Whether this is a skill (vs intermediate)
        
        Raises:
            WorkspaceQuotaExceeded: If quota would be exceeded
        """
        # Check total size
        if self.metadata["total_size"] + size > self.quota.max_size_bytes:
            raise WorkspaceQuotaExceeded(
                f"Workspace size limit exceeded: {self.quota.max_size_bytes} bytes"
            )
        
        # Check file count
        total_files = self.metadata["skill_count"] + self.metadata["intermediate_count"]
        if total_files + 1 > self.quota.max_files:
            raise WorkspaceQuotaExceeded(
                f"File count limit exceeded: {self.quota.max_files} files"
            )
        
        # Check per-file size
        if is_skill and size > self.quota.max_skill_size:
            raise WorkspaceQuotaExceeded(
                f"Skill size limit exceeded: {self.quota.max_skill_size} bytes"
            )
        elif not is_skill and size > self.quota.max_intermediate_size:
            raise WorkspaceQuotaExceeded(
                f"Intermediate file size limit exceeded: {self.quota.max_intermediate_size} bytes"
            )
    
    def save_skill(
        self,
        name: str,
        code: str,
        description: str,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        examples: Optional[List[str]] = None
    ) -> WorkspaceSkill:
        """Save a reusable skill to workspace.
        
        Args:
            name: Skill name (used as filename)
            code: Python code for the skill
            description: Human-readable description
            dependencies: List of required packages
            tags: Tags for categorization
            examples: Usage examples
        
        Returns:
            WorkspaceSkill object
        
        Raises:
            WorkspaceQuotaExceeded: If quota would be exceeded
        """
        # Check if skill already exists (increment version)
        version = 1
        skill_file = self.skills_dir / f"{name}.json"
        if skill_file.exists():
            existing = self.load_skill(name)
            version = existing.version + 1
        
        logger.debug(f"Saving skill '{name}' (version={version})")
        
        # Create skill object
        skill = WorkspaceSkill(
            name=name,
            code=code,
            description=description,
            version=version,
            dependencies=dependencies or [],
            tags=tags or [],
            examples=examples or []
        )
        
        # Check quota
        skill_json = json.dumps(skill.to_dict())
        self._check_quota(len(skill_json.encode()), is_skill=True)
        
        # Save JSON
        with open(skill_file, 'w') as f:
            f.write(skill_json)
        
        # Save Markdown documentation
        md_file = self.skills_dir / f"{name}.md"
        with open(md_file, 'w') as f:
            f.write(skill.to_markdown())
        
        # Update metadata
        if version == 1:
            self.metadata["skill_count"] += 1
        self.metadata["total_size"] += len(skill_json.encode())
        self._save_metadata()
        
        logger.info(
            f"Skill saved",
            extra={
                "skill_name": name,
                "skill_version": version,
                "code_lines": len(code.split('\n')),
                "dependencies": len(skill.dependencies),
                "tags": skill.tags,
                "session_id": self.session_id,
            }
        )
        return skill
    
    def load_skill(self, name: str) -> WorkspaceSkill:
        """Load a skill from workspace.
        
        Args:
            name: Skill name
        
        Returns:
            WorkspaceSkill object
        
        Raises:
            SkillNotFound: If skill doesn't exist
        """
        skill_file = self.skills_dir / f"{name}.json"
        
        logger.debug(f"Loading skill '{name}' from workspace")
        
        if not skill_file.exists():
            logger.warning(f"Skill not found: {name}")
            raise SkillNotFound(f"Skill not found: {name}")
        
        with open(skill_file, 'r') as f:
            data = json.load(f)
        
        skill = WorkspaceSkill.from_dict(data)
        logger.debug(
            f"Skill loaded",
            extra={
                "skill_name": name,
                "skill_version": skill.version,
                "dependencies": len(skill.dependencies),
                "session_id": self.session_id,
            }
        )
        return skill
    
    def list_skills(self, tags: Optional[List[str]] = None) -> List[WorkspaceSkill]:
        """List all skills in workspace.
        
        Args:
            tags: Optional tag filter
        
        Returns:
            List of WorkspaceSkill objects
        """
        skills = []
        
        for skill_file in self.skills_dir.glob("*.json"):
            with open(skill_file, 'r') as f:
                data = json.load(f)
            skill = WorkspaceSkill.from_dict(data)
            
            # Filter by tags if provided
            if tags is None or any(tag in skill.tags for tag in tags):
                skills.append(skill)
        
        return sorted(skills, key=lambda s: s.updated_at, reverse=True)
    
    def delete_skill(self, name: str) -> None:
        """Delete a skill from workspace.
        
        Args:
            name: Skill name
        
        Raises:
            SkillNotFound: If skill doesn't exist
        """
        skill_file = self.skills_dir / f"{name}.json"
        md_file = self.skills_dir / f"{name}.md"
        
        if not skill_file.exists():
            raise SkillNotFound(f"Skill not found: {name}")
        
        # Get size before deleting
        size = skill_file.stat().st_size
        
        # Delete files
        skill_file.unlink()
        if md_file.exists():
            md_file.unlink()
        
        # Update metadata
        self.metadata["skill_count"] -= 1
        self.metadata["total_size"] -= size
        self._save_metadata()
        
        logger.info(f"Deleted skill: {name}")
    
    def save_intermediate(self, name: str, data: Any) -> None:
        """Save intermediate output to workspace.
        
        Args:
            name: Name for the intermediate file
            data: Data to save (must be JSON-serializable)
        
        Raises:
            WorkspaceQuotaExceeded: If quota would be exceeded
        """
        intermediate_file = self.intermediate_dir / f"{name}.json"
        
        # Check if this is an update (file existed before)
        is_update = intermediate_file.exists()
        
        logger.debug(f"Saving intermediate '{name}' (update={is_update})")
        
        # Serialize data
        data_json = json.dumps(data, indent=2)
        
        # Check quota
        self._check_quota(len(data_json.encode()), is_skill=False)
        
        # Save
        with open(intermediate_file, 'w') as f:
            f.write(data_json)
        
        # Update metadata
        if not is_update:
            self.metadata["intermediate_count"] += 1
        self.metadata["total_size"] += len(data_json.encode())
        self._save_metadata()
        
        logger.info(
            f"Intermediate saved",
            extra={
                "intermediate_name": name,
                "is_update": is_update,
                "size_bytes": len(data_json.encode()),
                "session_id": self.session_id,
            }
        )
    
    def load_intermediate(self, name: str) -> Any:
        """Load intermediate output from workspace.
        
        Args:
            name: Name of the intermediate file
        
        Returns:
            Loaded data
        
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        intermediate_file = self.intermediate_dir / f"{name}.json"
        
        logger.debug(f"Loading intermediate '{name}' from workspace")
        
        if not intermediate_file.exists():
            logger.warning(f"Intermediate not found: {name}")
            raise FileNotFoundError(f"Intermediate file not found: {name}")
        
        with open(intermediate_file, 'r') as f:
            data = json.load(f)
        
        logger.debug(
            f"Intermediate loaded",
            extra={
                "intermediate_name": name,
                "data_type": type(data).__name__,
                "session_id": self.session_id,
            }
        )
        return data
    
    def list_intermediates(self) -> List[str]:
        """List all intermediate files in workspace.
        
        Returns:
            List of intermediate file names
        """
        return [f.stem for f in self.intermediate_dir.glob("*.json")]
    
    def get_workspace_stats(self) -> Dict[str, Any]:
        """Get workspace statistics.
        
        Returns:
            Dict with workspace stats
        """
        return {
            "session_id": self.session_id,
            "skills": self.metadata["skill_count"],
            "intermediates": self.metadata["intermediate_count"],
            "total_size_bytes": self.metadata["total_size"],
            "total_size_mb": round(self.metadata["total_size"] / (1024 * 1024), 2),
            "quota_used_percent": round(
                100 * self.metadata["total_size"] / self.quota.max_size_bytes, 1
            ),
            "created_at": self.metadata["created_at"],
        }
    
    def clear_workspace(self) -> None:
        """Clear all files from workspace (keeps metadata)."""
        # Delete all skills
        for skill_file in self.skills_dir.glob("*"):
            skill_file.unlink()
        
        # Delete all intermediates
        for intermediate_file in self.intermediate_dir.glob("*"):
            intermediate_file.unlink()
        
        # Reset metadata
        self.metadata["skill_count"] = 0
        self.metadata["intermediate_count"] = 0
        self.metadata["total_size"] = 0
        self._save_metadata()
        
        logger.info(f"Cleared workspace: {self.session_id}")
