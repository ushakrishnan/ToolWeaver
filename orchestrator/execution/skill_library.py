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
from typing import Dict, Any, List, Optional, Tuple
import logging

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from sentence_transformers import SentenceTransformer
    import numpy as np
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logger = logging.getLogger(__name__)

import re


def _increment_version(version: str, bump_type: str = "patch") -> str:
    """
    Increment semantic version (major.minor.patch).
    
    Args:
        version: Current version (e.g., "0.1.0")
        bump_type: "major", "minor", or "patch"
    
    Returns:
        Next version string
    """
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        return "0.1.0"
    
    major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    return f"{major}.{minor}.{patch}"


_ROOT = Path.home() / ".toolweaver" / "skills"
_ROOT.mkdir(parents=True, exist_ok=True)
_MANIFEST = _ROOT / "manifest.json"

# Optional Redis cache
_redis_client: Optional[Any] = None
_CACHE_TTL = 7 * 24 * 60 * 60  # 7 days

# Optional Qdrant search
_qdrant_client: Optional[Any] = None
_embedding_model: Optional[Any] = None


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
    dependencies: List[str] = None  # Names of skills this skill depends on
    version: str = "0.1.0"  # Semantic version
    created_at: Optional[str] = None  # ISO timestamp
    updated_at: Optional[str] = None  # ISO timestamp


def _load_manifest() -> Dict[str, Any]:
    if not _MANIFEST.exists():
        return {"skills": []}
    try:
        return json.loads(_MANIFEST.read_text())
    except Exception:
        return {"skills": []}


def _save_manifest(data: Dict[str, Any]) -> None:
    _MANIFEST.write_text(json.dumps(data, indent=2))


def _detect_dependencies(code: str) -> List[str]:
    """
    Detect skill dependencies by looking for execute_skill() calls.
    
    Returns:
        List of skill names referenced in the code
    """
    import re
    
    dependencies: List[str] = []
    
    # Pattern 1: orchestrator.execute_skill("skill_name")
    pattern1 = r'execute_skill\s*\(\s*["\']([^"\']+)["\']\s*[,\)]'
    dependencies.extend(re.findall(pattern1, code))
    
    # Pattern 2: get_skill("skill_name") or load_skill("skill_name")
    pattern2 = r'(?:get|load)_skill\s*\(\s*["\']([^"\']+)["\']\s*\)'
    dependencies.extend(re.findall(pattern2, code))
    
    return list(set(dependencies))  # Deduplicate


def _check_circular_dependencies(skill_name: str, dependencies: List[str]) -> Optional[List[str]]:
    """
    Check for circular dependencies in skill graph.
    
    Returns:
        Cycle path if found, None otherwise
    """
    def has_cycle(current: str, visited: set, path: List[str]) -> Optional[List[str]]:
        if current in visited:
            # Found cycle
            cycle_start = path.index(current)
            return path[cycle_start:] + [current]
        
        skill = get_skill(current)
        if not skill or not skill.dependencies:
            return None
        
        visited.add(current)
        path.append(current)
        
        for dep in skill.dependencies:
            cycle = has_cycle(dep, visited.copy(), path.copy())
            if cycle:
                return cycle
        
        return None
    
    # Check each dependency for cycles
    for dep in dependencies:
        cycle = has_cycle(dep, {skill_name}, [skill_name])
        if cycle:
            return cycle
    
    return None


def save_skill(name: str, code: str, *, description: str = "", tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> Skill:
    """
    Save a skill's code to disk and register in manifest.
    
    Automatically detects dependencies and checks for circular references.
    Also caches in Redis if available for fast lookups.
    Indexes in Qdrant if available for semantic search.
    """
    from datetime import datetime
    
    safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
    code_path = _ROOT / f"{safe_name}.py"
    
    # Detect dependencies
    dependencies = _detect_dependencies(code)
    
    # Check for circular dependencies
    if dependencies:
        cycle = _check_circular_dependencies(safe_name, dependencies)
        if cycle:
            logger.warning(f"Circular dependency detected: {' -> '.join(cycle)}")
            # Note: We still save but log the warning
    
    code_path.write_text(code)
    
    # Check if this is a new skill or update
    now = datetime.now().isoformat()
    existing = get_skill(safe_name)
    
    if existing:
        # This is an update - use existing creation time
        created_at = existing.created_at or now
        version = "0.1.0"  # Reset version on new save (use update_skill for versioning)
    else:
        # New skill
        created_at = now
        version = "0.1.0"

    skill = Skill(
        name=safe_name,
        code_path=str(code_path),
        description=description,
        tags=tags or [],
        metadata=metadata or {},
        dependencies=dependencies,
        version=version,
        created_at=created_at,
        updated_at=now
    )
    
    # Save to manifest (disk)
    data = _load_manifest()
    skills = [s for s in data.get("skills", []) if s.get("name") != safe_name]
    skills.append(asdict(skill))
    data["skills"] = skills
    
    # Track version history
    if "version_history" not in data:
        data["version_history"] = {}
    if safe_name not in data["version_history"]:
        data["version_history"][safe_name] = []
    if skill.version not in data["version_history"][safe_name]:
        data["version_history"][safe_name].append(skill.version)
    
    _save_manifest(data)
    
    # Cache in Redis if available
    r = _get_redis()
    if r:
        try:
            cache_key = f"skill:{safe_name}"
            r.setex(cache_key, _CACHE_TTL, json.dumps(asdict(skill)))
        except Exception:
            pass  # Redis cache is optional; silently fail
    
    # Index in Qdrant if available
    _index_skill_in_qdrant(skill)
    
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


def _get_qdrant() -> Optional[Tuple[Any, Any]]:
    """
    Get Qdrant client and embedding model if QDRANT_URL is set.
    
    Returns:
        (client, model) tuple or None
    """
    global _qdrant_client, _embedding_model
    
    if not QDRANT_AVAILABLE:
        return None
    
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        return None
    
    # Return cached clients
    if _qdrant_client and _embedding_model:
        return (_qdrant_client, _embedding_model)
    
    try:
        # Initialize client with timeout
        _qdrant_client = QdrantClient(url=qdrant_url, timeout=5.0)
        
        # Test connection by listing collections
        _qdrant_client.get_collections()
        
        # Load embedding model
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Ensure collection exists
        collection_name = os.getenv("QDRANT_COLLECTION", "toolweaver_skills")
        try:
            _qdrant_client.get_collection(collection_name)
        except Exception:
            # Create collection if missing
            _qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            logger.info(f"Created Qdrant collection: {collection_name}")
        
        return (_qdrant_client, _embedding_model)
    except Exception as e:
        logger.debug(f"Qdrant unavailable: {e}")
        # Reset globals to prevent partial initialization
        _qdrant_client = None
        _embedding_model = None
        return None


def _index_skill_in_qdrant(skill: Skill) -> None:
    """Index a skill in Qdrant for semantic search."""
    result = _get_qdrant()
    if not result:
        return
    
    client, model = result
    collection_name = os.getenv("QDRANT_COLLECTION", "toolweaver_skills")
    
    try:
        # Read code content
        code = Path(skill.code_path).read_text() if Path(skill.code_path).exists() else ""
        
        # Build searchable text
        search_text = f"{skill.name} {skill.description} {' '.join(skill.tags or [])} {code[:500]}"
        
        # Generate embedding (suppress output)
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            embedding = model.encode(search_text, show_progress_bar=False).tolist()
        
        # Upsert to Qdrant
        client.upsert(
            collection_name=collection_name,
            points=[PointStruct(
                id=hash(skill.name) & 0x7FFFFFFF,  # Ensure positive int
                vector=embedding,
                payload={
                    "name": skill.name,
                    "description": skill.description,
                    "tags": skill.tags or [],
                    "code_path": skill.code_path
                }
            )]
        )
        logger.debug(f"Indexed skill in Qdrant: {skill.name}")
    except Exception as e:
        logger.debug(f"Failed to index skill {skill.name}: {e}")


def get_dependency_graph() -> Dict[str, List[str]]:
    """
    Build a dependency graph for all skills.
    
    Returns:
        Dict mapping skill names to their dependencies
    """
    graph: Dict[str, List[str]] = {}
    
    for skill in list_skills():
        graph[skill.name] = skill.dependencies or []
    
    return graph


def get_skill_dependents(skill_name: str) -> List[str]:
    """
    Find all skills that depend on the given skill.
    
    Args:
        skill_name: Name of skill to find dependents for
    
    Returns:
        List of skill names that depend on this skill
    """
    dependents: List[str] = []
    
    for skill in list_skills():
        if skill.dependencies and skill_name in skill.dependencies:
            dependents.append(skill.name)
    
    return dependents


def visualize_dependency_graph(output_format: str = "text") -> str:
    """
    Generate a visual representation of the skill dependency graph.
    
    Args:
        output_format: "text" or "mermaid"
    
    Returns:
        Graph representation as string
    """
    graph = get_dependency_graph()
    
    if output_format == "mermaid":
        # Mermaid flowchart format
        lines = ["```mermaid", "graph TD"]
        
        for skill, deps in graph.items():
            if deps:
                for dep in deps:
                    lines.append(f"    {dep} --> {skill}")
            else:
                # Standalone skill
                lines.append(f"    {skill}")
        
        lines.append("```")
        return "\n".join(lines)
    
    else:
        # Simple text format
        lines = ["Skill Dependency Graph:", ""]
        
        for skill, deps in graph.items():
            if deps:
                lines.append(f"{skill}:")
                for dep in deps:
                    lines.append(f"  ← depends on: {dep}")
            else:
                lines.append(f"{skill}: (no dependencies)")
        
        return "\n".join(lines)


def search_skills(query: str, top_k: int = 5) -> List[Tuple[Skill, float]]:
    """
    Semantic search over saved skills.
    
    Uses Qdrant vector search if available, otherwise falls back to keyword match.
    
    Args:
        query: Natural language query (e.g., "multiply two numbers")
        top_k: Number of results to return
    
    Returns:
        List of (skill, score) tuples sorted by relevance
    
    Example:
        results = search_skills("data validation", top_k=3)
        for skill, score in results:
            print(f"{skill.name}: {score:.2f}")
    """
    result = _get_qdrant()
    
    # Vector search path
    if result:
        client, model = result
        collection_name = os.getenv("QDRANT_COLLECTION", "toolweaver_skills")
        
        try:
            # Generate query embedding (suppress progress bar)
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                query_embedding = model.encode(query, show_progress_bar=False).tolist()
            
            # Search Qdrant
            search_results = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k
            )
            
            # Convert to skills
            output: List[Tuple[Skill, float]] = []
            for hit in search_results:
                payload = hit.payload
                skill = Skill(
                    name=payload["name"],
                    code_path=payload["code_path"],
                    description=payload.get("description", ""),
                    tags=payload.get("tags", []),
                    metadata={}
                )
                output.append((skill, hit.score))
            
            return output
        except Exception as e:
            logger.debug(f"Qdrant search failed: {e}")
            # Fall through to keyword search
    
    # Fallback: keyword match
    all_skills = list_skills()
    query_lower = query.lower()
    
    matches: List[Tuple[Skill, float]] = []
    for skill in all_skills:
        score = 0.0
        
        # Check name
        if query_lower in skill.name.lower():
            score += 1.0
        
        # Check description
        if skill.description and query_lower in skill.description.lower():
            score += 0.5
        
        # Check tags
        for tag in (skill.tags or []):
            if query_lower in tag.lower():
                score += 0.3
        
        if score > 0:
            matches.append((skill, score))
    
    # Sort by score and return top_k
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:top_k]


def get_skill_versions(name: str) -> List[str]:
    """
    Get all versions of a skill.
    
    Args:
        name: Skill name
    
    Returns:
        List of version strings, sorted newest first
    """
    data = _load_manifest()
    
    if "version_history" not in data:
        data["version_history"] = {}
    
    versions = data["version_history"].get(name, [])
    # Sort versions in descending order (newest first)
    return sorted(versions, key=lambda v: tuple(map(int, v.split('.'))), reverse=True)


def get_skill_version(name: str, version: str) -> Optional[Skill]:
    """
    Get a specific version of a skill.
    
    Args:
        name: Skill name
        version: Version string (e.g., "0.2.0")
    
    Returns:
        Skill object or None if not found
    """
    data = _load_manifest()
    
    if "version_history" not in data:
        return None
    
    skill_versions = data["version_history"].get(name, [])
    
    if version not in skill_versions:
        return None
    
    # Load versioned code file
    version_code_path = _ROOT / f"{name}_{version}.py"
    
    if not version_code_path.exists():
        return None
    
    code = version_code_path.read_text()
    
    # Find metadata in skills list for this version
    for s in data.get("skills", []):
        if s.get("name") == name and s.get("version") == version:
            return Skill(**s)
    
    return None


def update_skill(name: str, code: str, *, description: str = None, tags: Optional[List[str]] = None, bump_type: str = "patch") -> Skill:
    """
    Update an existing skill with new code.
    
    Creates a new version automatically.
    
    Args:
        name: Skill name
        code: New code
        description: Optional new description
        tags: Optional new tags
        bump_type: "major", "minor", or "patch" (default: patch)
    
    Returns:
        New Skill object with incremented version
    
    Raises:
        KeyError: If skill not found
    """
    safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
    
    # Get current skill
    current = get_skill(safe_name)
    if not current:
        raise KeyError(f"Skill not found: {safe_name}")
    
    # Increment version
    new_version = _increment_version(current.version, bump_type)
    
    # Archive old version
    old_code_path = _ROOT / f"{safe_name}.py"
    archived_path = _ROOT / f"{safe_name}_{current.version}.py"
    
    if old_code_path.exists() and not archived_path.exists():
        old_code = old_code_path.read_text()
        archived_path.write_text(old_code)
    
    # Save new version
    code_path = _ROOT / f"{safe_name}.py"
    code_path.write_text(code)
    
    # Detect dependencies
    dependencies = _detect_dependencies(code)
    
    # Create new skill record
    from datetime import datetime
    skill = Skill(
        name=safe_name,
        code_path=str(code_path),
        description=description if description is not None else current.description,
        tags=tags if tags is not None else current.tags,
        metadata=current.metadata or {},
        dependencies=dependencies,
        version=new_version,
        created_at=current.created_at,
        updated_at=datetime.now().isoformat()
    )
    
    # Update manifest
    data = _load_manifest()
    
    # Keep old version records in skills list (versioned entries)
    skills = data.get("skills", [])
    
    # Replace current version only
    skills = [s for s in skills if not (s.get("name") == safe_name and s.get("version") != current.version)]
    
    # Add old version as archive if not already there
    old_skill_dict = asdict(current)
    if old_skill_dict not in skills:
        skills.append(old_skill_dict)
    
    # Add new version
    skills.append(asdict(skill))
    data["skills"] = skills
    
    # Track version history
    if "version_history" not in data:
        data["version_history"] = {}
    
    if safe_name not in data["version_history"]:
        data["version_history"][safe_name] = []
    
    # Add versions to history
    for v in [current.version, new_version]:
        if v not in data["version_history"][safe_name]:
            data["version_history"][safe_name].append(v)
    
    _save_manifest(data)
    
    # Update caches
    r = _get_redis()
    if r:
        try:
            cache_key = f"skill:{safe_name}"
            r.setex(cache_key, _CACHE_TTL, json.dumps(asdict(skill)))
        except Exception:
            pass
    
    # Re-index in Qdrant
    _index_skill_in_qdrant(skill)
    
    return skill


def rollback_skill(name: str, version: str) -> Skill:
    """
    Rollback to a previous version of a skill.
    
    Args:
        name: Skill name
        version: Version to rollback to
    
    Returns:
        Skill object for the restored version
    
    Raises:
        KeyError: If skill or version not found
    """
    safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
    
    # Get versioned code
    versioned_path = _ROOT / f"{safe_name}_{version}.py"
    if not versioned_path.exists():
        raise KeyError(f"Version not found: {safe_name}@{version}")
    
    code = versioned_path.read_text()
    
    # Copy back to current version
    current_path = _ROOT / f"{safe_name}.py"
    current_path.write_text(code)
    
    # Get skill metadata from version history
    data = _load_manifest()
    skill_record = None
    
    for s in data.get("skills", []):
        if s.get("name") == safe_name and s.get("version") == version:
            skill_record = s
            break
    
    if not skill_record:
        raise KeyError(f"Skill metadata not found for {safe_name}@{version}")
    
    # Create new skill with same version (will be current)
    from datetime import datetime
    skill = Skill(
        name=safe_name,
        code_path=str(current_path),
        description=skill_record.get("description", ""),
        tags=skill_record.get("tags", []),
        metadata=skill_record.get("metadata", {}),
        dependencies=skill_record.get("dependencies", []),
        version=version,
        created_at=skill_record.get("created_at"),
        updated_at=datetime.now().isoformat()
    )
    
    # Update manifest
    skills = [s for s in data.get("skills", []) if s.get("name") != safe_name]
    skills.append(asdict(skill))
    data["skills"] = skills
    _save_manifest(data)
    
    # Update caches
    r = _get_redis()
    if r:
        try:
            cache_key = f"skill:{safe_name}"
            r.setex(cache_key, _CACHE_TTL, json.dumps(asdict(skill)))
        except Exception:
            pass
    
    return skill
