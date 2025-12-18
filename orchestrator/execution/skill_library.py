"""
Skill Library

Persist and list reusable code snippets ("skills") generated during orchestration/codegen.

Stores skills under ~/.toolweaver/skills with a manifest for metadata.
Optional Redis caching for hot skill lookups (set REDIS_URL env var).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


_ROOT = Path.home() / ".toolweaver" / "skills"
_ROOT.mkdir(parents=True, exist_ok=True)
_MANIFEST = _ROOT / "manifest.json"

# Optional Redis cache
_redis_client: Optional[Any] = None
_CACHE_TTL = 7 * 24 * 60 * 60  # 7 days


def _get_redis() -> Optional[Any]:
    """Get Redis client if REDIS_URL is set and redis is installed."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    
    if not REDIS_AVAILABLE:
        return None
    
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    
    try:
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        _redis_client.ping()  # Test connection
        return _redis_client
    except Exception:
        return None


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
    """
    Save a skill's code to disk and register in manifest.
    
    Also caches in Redis if available for fast lookups.
    """
    safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
    code_path = _ROOT / f"{safe_name}.py"
    code_path.write_text(code)

    skill = Skill(name=safe_name, code_path=str(code_path), description=description, tags=tags or [], metadata=metadata or {})
    
    # Save to manifest (disk)
    data = _load_manifest()
    skills = [s for s in data.get("skills", []) if s.get("name") != safe_name]
    skills.append(asdict(skill))
    data["skills"] = skills
    _save_manifest(data)
    
    # Cache in Redis if available
    r = _get_redis()
    if r:
        try:
            cache_key = f"skill:{safe_name}"
            r.setex(cache_key, _CACHE_TTL, json.dumps(asdict(skill)))
        except Exception:
            pass  # Redis cache is optional; silently fail
    
    return skill


def list_skills() -> List[Skill]:
    data = _load_manifest()
    out: List[Skill] = []
    for s in data.get("skills", []):
        out.append(Skill(**s))
    return out


def get_skill(name: str) -> Optional[Skill]:
    """
    Get a skill by name.
    
    Checks Redis cache first (if available), falls back to disk.
    """
    # Try Redis cache first
    r = _get_redis()
    if r:
        try:
            cache_key = f"skill:{name}"
            cached = r.get(cache_key)
            if cached:
                return Skill(**json.loads(cached))
        except Exception:
            pass  # Fall through to disk
    
    # Fall back to disk
    for s in list_skills():
        if s.name == name:
            # Warm cache if Redis is available
            if r:
                try:
                    r.setex(f"skill:{name}", _CACHE_TTL, json.dumps(asdict(s)))
                except Exception:
                    pass
            return s
    return None
