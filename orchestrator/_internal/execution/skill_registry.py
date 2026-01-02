"""
Remote Skill Registry for ToolWeaver

Provides client-side access to a centralized skill repository:
- Upload approved skills to registry
- Download and install skills from registry
- Search registry by name, tags, ratings
- Marketplace features (ratings, reviews, popularity)
- Namespace/organization support
- Optional skill signing and verification

Registry API endpoints (default: https://registry.toolweaver.io):
  POST   /api/v1/skills           - Upload skill
  GET    /api/v1/skills/:id       - Get skill details
  GET    /api/v1/skills           - Search skills
  GET    /api/v1/skills/:id/download - Download skill package
  POST   /api/v1/skills/:id/rate  - Rate skill
  GET    /api/v1/skills/:id/ratings - Get skill ratings

Environment:
  REGISTRY_URL     - Registry base URL (default: https://registry.toolweaver.io)
  REGISTRY_TOKEN   - Auth token for uploads (optional)
  REGISTRY_ORG     - Default organization namespace (optional)
  REGISTRY_VERIFY_SIGNATURE - Verify skill signatures (default: false)
"""

import hashlib
import hmac
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from urllib.parse import urljoin

import requests

from .skill_library import Skill, save_skill

logger = logging.getLogger(__name__)

# Configuration
REGISTRY_URL = Path.home() / '.toolweaver' / 'registry_config.json'
_REGISTRY_CACHE_DIR = Path.home() / '.toolweaver' / 'registry_cache'
_REGISTRY_CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class RegistrySkill:
    """Published skill in remote registry."""
    id: str  # Unique skill ID (org/name)
    name: str
    org: str  # Organization namespace
    version: str
    description: str = ""
    code_hash: str = ""  # SHA256 of code for verification
    signature: str = ""  # Optional HMAC-SHA256 signature
    tags: list[str] = field(default_factory=list)
    rating: float = 0.0  # Average rating 0-5
    rating_count: int = 0
    install_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    author: str = ""
    license: str = "MIT"
    homepage: str | None = None
    repository: str | None = None

@dataclass
class RegistryConfig:
    """Registry connection configuration."""
    url: str = "https://registry.toolweaver.io"
    token: str | None = None  # Auth token for uploads
    org: str | None = None  # Default org namespace
    verify_signature: bool = False
    timeout: int = 30


def _load_registry_config() -> RegistryConfig:
    """Load registry configuration from disk or environment."""
    if REGISTRY_URL.exists():
        try:
            config_dict = json.loads(REGISTRY_URL.read_text())
            return RegistryConfig(**config_dict)
        except Exception as e:
            logger.warning(f"Failed to load registry config: {e}")

    # Fall back to environment variables
    import os
    return RegistryConfig(
        url=os.getenv('REGISTRY_URL', 'https://registry.toolweaver.io'),
        token=os.getenv('REGISTRY_TOKEN'),
        org=os.getenv('REGISTRY_ORG'),
        verify_signature=os.getenv('REGISTRY_VERIFY_SIGNATURE', 'false').lower() == 'true'
    )


def _save_registry_config(config: RegistryConfig) -> None:
    """Save registry configuration to disk."""
    REGISTRY_URL.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_URL.write_text(json.dumps(asdict(config), indent=2))


def configure_registry(url: str | None = None, token: str | None = None, org: str | None = None,
                       verify_signature: bool | None = None) -> RegistryConfig:
    """
    Configure registry connection.

    Args:
        url: Registry base URL
        token: Authentication token for uploads
        org: Default organization namespace
        verify_signature: Whether to verify skill signatures

    Returns:
        Updated RegistryConfig
    """
    config = _load_registry_config()

    if url:
        config.url = url
    if token:
        config.token = token
    if org:
        config.org = org
    if verify_signature is not None:
        config.verify_signature = verify_signature

    _save_registry_config(config)
    logger.info(f"Registry configured: {config.url}")
    return config


class SkillRegistry:
    """Client for remote skill registry."""

    def __init__(self, config: RegistryConfig | None = None):
        """Initialize registry client."""
        self.config = config or _load_registry_config()
        self.session = requests.Session()
        if self.config.token:
            self.session.headers['Authorization'] = f'Bearer {self.config.token}'

    def _api_url(self, path: str) -> str:
        """Build full API URL."""
        return urljoin(self.config.url, f'/api/v1{path}')

    def _compute_hash(self, code: str) -> str:
        """Compute SHA256 hash of code."""
        return hashlib.sha256(code.encode()).hexdigest()

    def _sign_skill(self, skill_id: str, code_hash: str, secret: str) -> str:
        """Create HMAC-SHA256 signature for skill."""
        message = f"{skill_id}:{code_hash}"
        return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    def _verify_signature(self, skill_id: str, code_hash: str, signature: str,
                         secret: str) -> bool:
        """Verify skill signature."""
        expected = self._sign_skill(skill_id, code_hash, secret)
        return hmac.compare_digest(signature, expected)

    def publish_skill(self, skill: Skill, org: str | None = None,
                     tags: list[str] | None = None, license: str = "MIT",
                     homepage: str | None = None,
                     repository: str | None = None,
                     secret: str | None = None) -> RegistrySkill:
        """
        Publish skill to remote registry.

        Args:
            skill: Skill to publish
            org: Organization namespace (uses config.org if not provided)
            tags: Topic tags for discovery
            license: Skill license
            homepage: Homepage URL
            repository: Repository URL
            secret: Secret for signing (optional)

        Returns:
            Published RegistrySkill with ID

        Raises:
            ValueError: If upload fails
            ConnectionError: If registry unreachable
        """
        if not self.config.token:
            raise ValueError("Registry token required for publishing. "
                           "Configure with configure_registry(token=...)")

        org = org or self.config.org or 'community'
        skill_id = f"{org}/{skill.name}"

        # Read skill code
        skill_code = skill.code_path
        if isinstance(skill_code, str):
            if Path(skill_code).exists():
                skill_code = Path(skill_code).read_text()

        # Compute hash and signature
        code_hash = self._compute_hash(skill_code)
        signature = self._sign_skill(skill_id, code_hash, secret) if secret else ""

        # Build payload
        resolved_tags: list[str] = tags or skill.tags or []

        payload = {
            'id': skill_id,
            'name': skill.name,
            'org': org,
            'version': skill.version,
            'description': skill.description,
            'code_hash': code_hash,
            'signature': signature,
            'tags': resolved_tags,
            'license': license,
            'homepage': homepage,
            'repository': repository,
            'code': skill_code,  # Registry will store encrypted
        }

        try:
            response = self.session.post(
                self._api_url('/skills'),
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Published skill {skill_id} to registry")

            return RegistrySkill(
                id=skill_id,
                name=skill.name,
                org=org,
                version=skill.version,
                description=skill.description,
                code_hash=code_hash,
                signature=signature,
                tags=resolved_tags,
                created_at=result.get('created_at', datetime.utcnow().isoformat()),
                updated_at=result.get('updated_at', datetime.utcnow().isoformat()),
            )

        except requests.RequestException as e:
            logger.error(f"Failed to publish skill {skill_id}: {e}")
            raise ConnectionError(f"Registry error: {e}") from e

    def search(self, query: str = "", tags: list[str] | None = None,
              org: str | None = None, min_rating: float = 0.0,
              limit: int = 50, offset: int = 0) -> list[RegistrySkill]:
        """
        Search registry for skills.

        Args:
            query: Search term (skill name, description)
            tags: Filter by tags
            org: Filter by organization
            min_rating: Minimum rating threshold (0-5)
            limit: Max results to return
            offset: Pagination offset

        Returns:
            List of matching RegistrySkill objects
        """
        params: dict[str, str | int | float] = {
            'q': query,
            'limit': limit,
            'offset': offset,
            'min_rating': min_rating,
        }
        if tags:
            params['tags'] = ','.join(tags)
        if org:
            params['org'] = org

        try:
            response = self.session.get(
                self._api_url('/skills'),
                params=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            results = response.json()
            skills = []
            for item in results.get('skills', []):
                skills.append(RegistrySkill(**item))

            logger.info(f"Search found {len(skills)} skills for '{query}'")
            return skills

        except requests.RequestException as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_skill(self, skill_id: str) -> RegistrySkill | None:
        """
        Get skill details from registry.

        Args:
            skill_id: Skill ID (org/name)

        Returns:
            RegistrySkill or None if not found
        """
        try:
            response = self.session.get(
                self._api_url(f'/skills/{skill_id}'),
                timeout=self.config.timeout
            )
            response.raise_for_status()

            data = response.json()
            return RegistrySkill(**data)

        except requests.RequestException as e:
            logger.error(f"Failed to fetch skill {skill_id}: {e}")
            return None

    def download_skill(self, skill_id: str, version: str | None = None) -> Skill:
        """
        Download skill from registry and install locally.

        Args:
            skill_id: Skill ID (org/name)
            version: Specific version (defaults to latest)

        Returns:
            Downloaded Skill object

        Raises:
            ConnectionError: If download fails
        """
        try:
            # Fetch skill metadata
            registry_skill = self.get_skill(skill_id)
            if not registry_skill:
                raise ValueError(f"Skill {skill_id} not found in registry")

            # Download skill package
            params: dict[str, str] = {}
            if version:
                params['version'] = version

            response = self.session.get(
                self._api_url(f'/skills/{skill_id}/download'),
                params=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            data = response.json()
            code = data['code']

            # Verify signature if enabled
            if self.config.verify_signature and registry_skill.signature:
                if 'secret' in data:  # Registry provides shared secret in response
                    if not self._verify_signature(skill_id, registry_skill.code_hash,
                                                 registry_skill.signature, data['secret']):
                        raise ValueError(f"Signature verification failed for {skill_id}")

            # Save skill locally
            skills_dir = Path.home() / '.toolweaver' / 'skills'
            skill = Skill(
                name=registry_skill.name,
                code_path=str(skills_dir / f"{skill_id.replace('/', '_')}.py"),
                description=registry_skill.description,
                version=registry_skill.version,
                tags=registry_skill.tags,
            )

            # Write code to file
            skill_file = Path(skill.code_path)
            skill_file.parent.mkdir(parents=True, exist_ok=True)
            skill_file.write_text(code)

            # Save to library
            save_skill(
                skill.name,
                code,
                description=skill.description,
                tags=skill.tags,
            )

            logger.info(f"Downloaded and installed skill {skill_id} v{registry_skill.version}")
            return skill

        except Exception as e:
            logger.error(f"Failed to download skill {skill_id}: {e}")
            raise ConnectionError(f"Download failed: {e}") from e

    def rate_skill(self, skill_id: str, rating: float,
                  review: str | None = None) -> bool:
        """
        Rate a skill in the registry.

        Args:
            skill_id: Skill ID (org/name)
            rating: Rating 1-5 stars
            review: Optional review text

        Returns:
            True if successful
        """
        if not 1.0 <= rating <= 5.0:
            raise ValueError("Rating must be between 1 and 5")

        try:
            payload: dict[str, Any] = {'rating': rating}
            if review:
                payload['review'] = review

            response = self.session.post(
                self._api_url(f'/skills/{skill_id}/rate'),
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            logger.info(f"Rated {skill_id}: {rating} stars")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to rate skill {skill_id}: {e}")
            return False

    def get_ratings(self, skill_id: str) -> dict[str, Any]:
        """
        Get ratings and reviews for a skill.

        Args:
            skill_id: Skill ID (org/name)

        Returns:
            Dict with average rating, count, and recent reviews
        """
        try:
            response = self.session.get(
                self._api_url(f'/skills/{skill_id}/ratings'),
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

        except requests.RequestException as e:
            logger.error(f"Failed to get ratings for {skill_id}: {e}")
            return {'average': 0.0, 'count': 0, 'reviews': []}

    def trending(self, limit: int = 10) -> list[RegistrySkill]:
        """Get trending skills by install count."""
        return self.search(limit=limit, offset=0)  # API would sort by popularity


# Module-level convenience functions

_registry_instance = None

def _get_registry(config: RegistryConfig | None = None) -> SkillRegistry:
    """Get or create registry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = SkillRegistry(config)
    return _registry_instance


def publish_skill(skill: Skill, org: str | None = None, tags: list[str] | None = None,
                 license: str = "MIT", homepage: str | None = None,
                 repository: str | None = None) -> RegistrySkill:
    """Publish skill to registry."""
    return _get_registry().publish_skill(skill, org, tags, license, homepage, repository)


def search_registry(query: str = "", tags: list[str] | None = None,
                   org: str | None = None, min_rating: float = 0.0) -> list[RegistrySkill]:
    """Search registry for skills."""
    return _get_registry().search(query, tags, org, min_rating)


def get_registry_skill(skill_id: str) -> RegistrySkill | None:
    """Get skill details from registry."""
    return _get_registry().get_skill(skill_id)


def download_registry_skill(skill_id: str, version: str | None = None) -> Skill:
    """Download skill from registry."""
    return _get_registry().download_skill(skill_id, version)


def rate_registry_skill(skill_id: str, rating: float, review: str | None = None) -> bool:
    """Rate skill in registry."""
    return _get_registry().rate_skill(skill_id, rating, review)


def get_registry_ratings(skill_id: str) -> dict[str, Any]:
    """Get skill ratings from registry."""
    return _get_registry().get_ratings(skill_id)


def trending_skills(limit: int = 10) -> list[RegistrySkill]:
    """Get trending skills."""
    return _get_registry().trending(limit)
