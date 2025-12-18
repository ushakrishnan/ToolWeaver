"""
Skill Library

Persist and list reusable code snippets ("skills") generated during orchestration/codegen.

Stores skills under ~/.toolweaver/skills with a manifest for metadata.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional


_ROOT = Path.home() / ".toolweaver" / "skills"
_ROOT.mkdir(parents=True, exist_ok=True)
_MANIFEST = _ROOT / "manifest.json"


@dataclass
class Skill:
    name: str
    code_path: str
    description: str = ""
    tags: List[str] = None
    metadata: Dict[str, Any] = None


def _load_manifest() -> Dict[str, Any]:
    if not _MANIFEST.exists():
        return {"skills": []}
    try:
        return json.loads(_MANIFEST.read_text())
    except Exception:
        return {"skills": []}


def _save_manifest(data: Dict[str, Any]) -> None:
    _MANIFEST.write_text(json.dumps(data, indent=2))


def save_skill(name: str, code: str, *, description: str = "", tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> Skill:
    """Save a skill's code to disk and register in manifest."""
    safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
    code_path = _ROOT / f"{safe_name}.py"
    code_path.write_text(code)

    skill = Skill(name=safe_name, code_path=str(code_path), description=description, tags=tags or [], metadata=metadata or {})
    data = _load_manifest()
    # Replace existing if present
    skills = [s for s in data.get("skills", []) if s.get("name") != safe_name]
    skills.append(asdict(skill))
    data["skills"] = skills
    _save_manifest(data)
    return skill


def list_skills() -> List[Skill]:
    data = _load_manifest()
    out: List[Skill] = []
    for s in data.get("skills", []):
        out.append(Skill(**s))
    return out


def get_skill(name: str) -> Optional[Skill]:
    for s in list_skills():
        if s.name == name:
            return s
    return None
