<!-- Registry Docs -->
# Remote Skill Registry Guide

## Overview

The Remote Skill Registry enables teams to **publish, discover, and share** approved skills across organizations. It's built on top of the semantic versioning system (Phase 4.1) and integrates with workflow templates (Phase 4.2) for enterprise skill management.

### Key Features

- **Publish Skills**: Upload approved skills with versioning and optional signatures
- **Marketplace**: Discover skills by name, tags, organization, and ratings
- **Ratings System**: Rate and review skills; see community feedback
- **Namespace Support**: Organize skills by organization (e.g., `acme/email-validator`)
- **Signature Verification**: Optional HMAC-SHA256 signing for trusted skills
- **Cross-Team Sharing**: Install registry skills directly into your local library
- **Integration**: Works with workflows, versioning, and metrics

---

## Quick Start

### 1. Configure Registry

```python
from orchestrator.execution import configure_registry

# Set registry URL and authentication
configure_registry(
    url="https://registry.your-company.com",
    token="your_auth_token",
    org="acme",  # Default namespace
    verify_signature=False  # Enable for production
)
```

Or use environment variables:
```bash
export REGISTRY_URL=https://registry.your-company.com
export REGISTRY_TOKEN=your_auth_token
export REGISTRY_ORG=acme
export REGISTRY_VERIFY_SIGNATURE=false
```

### 2. Publish a Skill

```python
from orchestrator.execution import Skill, publish_skill

# Create and publish skill
skill = Skill(
    name='email_validator',
    code_path='/path/to/validate_email.py',
    version='1.0.0',
    description='Validates email addresses'
)

result = publish_skill(
    skill,
    org='acme',
    tags=['email', 'validation', 'utility'],
    license='MIT',
    homepage='https://github.com/acme/email-validator',
    repository='https://github.com/acme/email-validator.git'
)

print(f"Published: {result.id}")  # acme/email_validator
```

### 3. Search Registry

```python
from orchestrator.execution import search_registry

# Search by name/description
skills = search_registry(
    query='email',
    tags=['utility'],
    org='acme',
    min_rating=3.5
)

for skill in skills:
    print(f"{skill.id} v{skill.version} - {skill.rating:.1f}/5 ({skill.rating_count} reviews)")
```

### 4. Download and Install Skill

```python
from orchestrator.execution import download_registry_skill

# Download skill from registry and install locally
skill = download_registry_skill('acme/email_validator', version='1.0.0')

# Now use it in a workflow
from orchestrator.execution import create_workflow, add_step

w = create_workflow('validate_emails', 'Email validation workflow')
add_step(w, 'validate', 'email_validator', {'email': '${email_input}'})
```

### 5. Rate a Skill

```python
from orchestrator.execution import rate_registry_skill

# Rate skill 1-5 stars
rate_registry_skill(
    'acme/email_validator',
    rating=4.5,
    review='Works great, fast validation'
)
```

---

## API Reference

### Functions

#### `configure_registry(url, token, org, verify_signature)`

Configure registry connection.

**Parameters:**
- `url` (str): Registry base URL (default: https://registry.toolweaver.io)
- `token` (str): Auth token for uploads (required to publish)
- `org` (str): Default organization namespace
- `verify_signature` (bool): Enable skill signature verification

**Returns:** Updated `RegistryConfig`

**Example:**
```python
config = configure_registry(token='secret_token', org='myorg')
```

---

#### `publish_skill(skill, org, tags, license, homepage, repository, secret)`

Publish skill to registry.

**Parameters:**
- `skill` (Skill): Skill object with code_path and metadata
- `org` (str): Organization namespace (e.g., 'acme')
- `tags` (list): Topic tags for discovery (e.g., ['email', 'validation'])
- `license` (str): License type (default: 'MIT')
- `homepage` (str): Project homepage URL
- `repository` (str): Git repository URL
- `secret` (str): Secret for HMAC-SHA256 signing (optional)

**Returns:** `RegistrySkill` with published metadata

**Raises:**
- `ValueError`: If no auth token configured
- `ConnectionError`: If registry unreachable

**Example:**
```python
from orchestrator.execution import publish_skill, Skill

skill = Skill(name='calculator', code_path='/skills/calc.py')
result = publish_skill(skill, org='utils', tags=['math'])
print(result.id)  # utils/calculator
```

---

#### `search_registry(query, tags, org, min_rating, limit, offset)`

Search registry for skills.

**Parameters:**
- `query` (str): Search term (name, description keywords)
- `tags` (list): Filter by tags (e.g., ['email', 'validation'])
- `org` (str): Filter by organization (e.g., 'acme')
- `min_rating` (float): Minimum rating threshold (0-5)
- `limit` (int): Max results (default: 50)
- `offset` (int): Pagination offset (default: 0)

**Returns:** List of `RegistrySkill` objects

**Example:**
```python
# Find highly-rated email skills
skills = search_registry(
    query='email',
    tags=['email'],
    min_rating=4.0,
    limit=10
)

for s in skills:
    print(f"{s.id}: {s.rating}/5 ({s.install_count} installs)")
```

---

#### `get_registry_skill(skill_id)`

Get skill details from registry.

**Parameters:**
- `skill_id` (str): Skill ID (org/name format)

**Returns:** `RegistrySkill` or None

**Example:**
```python
skill = get_registry_skill('acme/email_validator')
print(f"{skill.name} v{skill.version}")
print(f"Rating: {skill.rating}/5 ({skill.rating_count})")
print(f"Installs: {skill.install_count}")
```

---

#### `download_registry_skill(skill_id, version)`

Download skill from registry and install locally.

**Parameters:**
- `skill_id` (str): Skill ID to download (org/name)
- `version` (str): Specific version (default: latest)

**Returns:** Installed `Skill` object (saved to local library)

**Raises:**
- `ValueError`: If skill not found
- `ConnectionError`: If download fails

**Example:**
```python
skill = download_registry_skill('acme/email_validator', version='1.0.0')

# Use in workflow immediately
from orchestrator.execution import get_skill
loaded = get_skill('email_validator')  # Now available locally
```

---

#### `rate_registry_skill(skill_id, rating, review)`

Rate skill in registry.

**Parameters:**
- `skill_id` (str): Skill ID (org/name)
- `rating` (float): Rating 1-5 stars
- `review` (str): Optional review text

**Returns:** True if successful, False if failed

**Example:**
```python
success = rate_registry_skill(
    'acme/email_validator',
    rating=4.5,
    review='Excellent email validation library!'
)
```

---

#### `get_registry_ratings(skill_id)`

Get ratings and reviews for a skill.

**Parameters:**
- `skill_id` (str): Skill ID (org/name)

**Returns:** Dict with:
- `average` (float): Average rating 0-5
- `count` (int): Number of ratings
- `reviews` (list): Recent reviews with text and author

**Example:**
```python
ratings = get_registry_ratings('acme/email_validator')
print(f"Average: {ratings['average']}/5 ({ratings['count']} reviews)")
for review in ratings['reviews']:
    print(f"  {review['author']}: {review['text']}")
```

---

#### `trending_skills(limit)`

Get trending/popular skills by install count.

**Parameters:**
- `limit` (int): Max results (default: 10)

**Returns:** List of `RegistrySkill` objects (sorted by popularity)

**Example:**
```python
popular = trending_skills(limit=5)
for skill in popular:
    print(f"{skill.id}: {skill.install_count} installs")
```

---

### Classes

#### `RegistryConfig`

Configuration for registry connection.

**Attributes:**
- `url` (str): Registry base URL
- `token` (Optional[str]): Auth token for uploads
- `org` (Optional[str]): Default organization namespace
- `verify_signature` (bool): Whether to verify signatures
- `timeout` (int): Request timeout in seconds (default: 30)

**Example:**
```python
config = RegistryConfig(
    url='https://registry.company.com',
    token='token123',
    org='myorg',
    verify_signature=True
)
```

---

#### `RegistrySkill`

Published skill metadata in registry.

**Attributes:**
- `id` (str): Unique skill ID (org/name)
- `name` (str): Skill name
- `org` (str): Organization namespace
- `version` (str): Semantic version (e.g., 1.0.0)
- `description` (str): Skill description
- `code_hash` (str): SHA256 hash of code
- `signature` (str): Optional HMAC-SHA256 signature
- `tags` (list): Topic tags for discovery
- `rating` (float): Average rating 0-5
- `rating_count` (int): Number of ratings
- `install_count` (int): Total installations
- `created_at` (str): ISO timestamp
- `updated_at` (str): ISO timestamp
- `author` (str): Original author/org
- `license` (str): License type (e.g., 'MIT')
- `homepage` (str): Homepage URL
- `repository` (str): Repository URL

**Example:**
```python
skill = get_registry_skill('acme/email_validator')
print(f"ID: {skill.id}")
print(f"Version: {skill.version}")
print(f"Rating: {skill.rating}/5 from {skill.rating_count} users")
print(f"Installs: {skill.install_count}")
```

---

#### `SkillRegistry`

Client for registry operations (used internally by convenience functions).

**Methods:**
- `publish_skill()` - Publish skill to registry
- `search()` - Search skills
- `get_skill()` - Get skill details
- `download_skill()` - Download and install skill
- `rate_skill()` - Rate skill
- `get_ratings()` - Get skill ratings
- `trending()` - Get trending skills

**Example:**
```python
from orchestrator.execution.skill_registry import SkillRegistry, RegistryConfig

config = RegistryConfig(
    url='https://registry.company.com',
    token='mytoken',
    org='acme'
)

registry = SkillRegistry(config)
results = registry.search(query='email')
```

---

## Advanced Usage

### Signing Skills with HMAC-SHA256

For security-sensitive environments, sign skills to prevent tampering:

```python
# Publish with signature
result = publish_skill(
    skill,
    secret='my_signing_secret_key'
)

# Registry computes HMAC-SHA256(skill_id:code_hash, secret)
# And stores signature for verification
```

**Verification:**

```python
# When downloading
configure_registry(verify_signature=True, token='...')

# Download automatically verifies signature
skill = download_registry_skill('acme/email_validator')
# Raises ValueError if signature invalid
```

---

### Namespace Organization

Use namespaces to organize skills by team/function:

```python
# Publish with different namespaces
publish_skill(skill, org='acme/email')      # acme/email/validator
publish_skill(skill, org='acme/payments')   # acme/payments/processor
publish_skill(skill, org='community')       # community/helper
```

**Search by namespace:**

```python
email_skills = search_registry(org='acme/email')
```

---

### Skill Distribution Workflow

**Typical enterprise flow:**

1. **Develop**: Create and test skill locally
2. **Version**: Tag skill with semantic version (e.g., 1.0.0)
3. **Test**: Run through approval gates (see Phase 4.4)
4. **Publish**: Push approved skill to registry
5. **Discover**: Teams search and find skilled needed
6. **Install**: Download and use in workflows
7. **Rate**: Provide feedback to improve marketplace

---

### Integration with Workflows

Published skills work seamlessly in workflows:

```python
from orchestrator.execution import (
    download_registry_skill,
    create_workflow,
    add_step,
    execute_workflow
)

# Install skill from registry
download_registry_skill('acme/email_validator')

# Use in workflow
w = create_workflow('email_validation', 'Validate incoming emails')
add_step(w, 'validate', 'email_validator', {'email': '${input}'})

# Execute workflow - uses downloaded skill
import asyncio
results = asyncio.run(execute_workflow(w, {'input': 'test@example.com'}))
```

---

## Registry API Specification

The registry implements a RESTful API for client access.

### Base URL
```
https://registry.your-company.com/api/v1
```

### Endpoints

#### `POST /skills` - Publish Skill

**Request:**
```json
{
  "id": "acme/email_validator",
  "name": "email_validator",
  "org": "acme",
  "version": "1.0.0",
  "description": "Validates email addresses",
  "code_hash": "sha256_hash_of_code",
  "signature": "optional_hmac_signature",
  "tags": ["email", "validation"],
  "license": "MIT",
  "code": "def validate(email): ..."
}
```

**Response:**
```json
{
  "id": "acme/email_validator",
  "created_at": "2025-12-18T10:30:00Z",
  "updated_at": "2025-12-18T10:30:00Z"
}
```

---

#### `GET /skills` - Search Skills

**Query Parameters:**
- `q` - Search query
- `tags` - Comma-separated tags
- `org` - Organization filter
- `min_rating` - Minimum rating (0-5)
- `limit` - Max results (default: 50)
- `offset` - Pagination offset

**Response:**
```json
{
  "total": 42,
  "skills": [
    {
      "id": "acme/email_validator",
      "name": "email_validator",
      "version": "1.0.0",
      "rating": 4.5,
      "rating_count": 23,
      "install_count": 156
    }
  ]
}
```

---

#### `GET /skills/:id` - Get Skill Details

**Response:**
```json
{
  "id": "acme/email_validator",
  "name": "email_validator",
  "org": "acme",
  "version": "1.0.0",
  "description": "Validates email addresses",
  "rating": 4.5,
  "rating_count": 23,
  "install_count": 156,
  "created_at": "2025-12-18T10:30:00Z",
  "updated_at": "2025-12-18T10:30:00Z"
}
```

---

#### `GET /skills/:id/download` - Download Skill

**Response:**
```json
{
  "code": "def validate(email): ...",
  "version": "1.0.0",
  "secret": "shared_secret_for_signature_verification"
}
```

---

#### `POST /skills/:id/rate` - Rate Skill

**Request:**
```json
{
  "rating": 4.5,
  "review": "Excellent library!"
}
```

**Response:**
```json
{
  "success": true,
  "average_rating": 4.3,
  "rating_count": 24
}
```

---

## Troubleshooting

### "Registry token required for publishing"
**Fix**: Configure auth token before publishing
```python
configure_registry(token='your_token')
```

### "Signature verification failed"
**Fix**: Ensure `REGISTRY_VERIFY_SIGNATURE=true` and secret matches
```python
configure_registry(verify_signature=False)  # Disable for testing
```

### "Skill not found in registry"
**Fix**: Check skill ID format (should be `org/name`)
```python
# Correct
skill = get_registry_skill('acme/email_validator')

# Incorrect - missing org
skill = get_registry_skill('email_validator')
```

### Connection timeout
**Fix**: Increase timeout or check registry URL
```python
config = configure_registry(timeout=60)  # Increase to 60 seconds
```

---

## What's Next?

**Phase 4.4: Team Collaboration**
- Multi-person approval chains for registry submissions
- Comments and feedback on skills
- Audit logs and change tracking
- Notifications for rating updates

**Phase 5: Advanced Analytics**
- Skill usage metrics and trends
- Author/team leaderboards
- Dependency analysis
- Performance benchmarks
