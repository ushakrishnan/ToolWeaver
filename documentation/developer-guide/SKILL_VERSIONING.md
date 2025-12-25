# Skill Versioning

Manage multiple versions of skills with automatic versioning, rollback, and history tracking.

## Overview

Every skill now has:
- **Semantic versioning** (e.g., 0.1.0, 0.2.0, 1.0.0)
- **Creation timestamp** (when first created)
- **Update timestamp** (when last modified)
- **Version history** (all previous versions archived)

Versioning enables:
- Multi-version deployments
- Easy rollback to previous versions
- Audit trails for compliance
- A/B testing of skill improvements

## Quick Start

### Create a Skill (v0.1.0 by default)

```python
from orchestrator.execution import save_skill

skill = save_skill(
    "validate_email",
    "def validate(email): return '@' in email",
    description="Email validation"
)
print(skill.version)  # "0.1.0"
```

### Update to Create New Version

```python
from orchestrator.execution import update_skill

# Patch version (0.1.0 → 0.1.1)
updated = update_skill(
    "validate_email",
    "def validate(email): return re.match(r'^[^@]+@[^@]+\.[^@]+$', email)",
    description="Email validation (fixed regex)",
    bump_type="patch"
)
print(updated.version)  # "0.1.1"

# Minor version (0.1.1 → 0.2.0)
updated = update_skill(
    "validate_email",
    "...",
    bump_type="minor"
)
print(updated.version)  # "0.2.0"

# Major version (0.2.0 → 1.0.0)
updated = update_skill(
    "validate_email",
    "...",
    bump_type="major"
)
print(updated.version)  # "1.0.0"
```

### View Version History

```python
from orchestrator.execution import get_skill_versions

versions = get_skill_versions("validate_email")
print(versions)  # ['1.0.0', '0.2.0', '0.1.1', '0.1.0']
```

### Get a Specific Version

```python
from orchestrator.execution import get_skill_version

old_skill = get_skill_version("validate_email", "0.1.0")
print(old_skill.description)
```

### Rollback to Previous Version

```python
from orchestrator.execution import rollback_skill

# Restore 0.1.0 as the current active version
restored = rollback_skill("validate_email", "0.1.0")
print(restored.version)  # "0.1.0"
```

---

## Semantic Versioning

Follow [semver.org](https://semver.org/) conventions:

### MAJOR.MINOR.PATCH

- **MAJOR** (e.g., 1.0.0): Breaking changes (API change, incompatible behavior)
- **MINOR** (e.g., 0.2.0): New functionality (backward compatible)
- **PATCH** (e.g., 0.1.1): Bug fixes (backward compatible)

### Examples

| Change | Bump | Reason |
|--------|------|--------|
| Fix regex bug | PATCH | Bug fix, backward compatible |
| Add optional param | MINOR | New feature, backward compatible |
| Remove required param | MAJOR | Breaking change |
| Improve performance | PATCH | Bug fix/optimization |
| Change output format | MAJOR | Breaking change |

---

## Storage Structure

All versions are stored on disk:

```
~/.toolweaver/skills/
├── manifest.json          # Current skill + version history
├── validate_email.py      # Current version (0.1.0)
├── validate_email_0.1.0.py
├── validate_email_0.1.1.py
├── validate_email_0.2.0.py
└── validate_email_1.0.0.py
```

`manifest.json` includes:

```json
{
  "skills": [
    {
      "name": "validate_email",
      "version": "1.0.0",
      "code_path": "...",
      "created_at": "2025-01-01T09:00:00",
      "updated_at": "2025-01-15T14:23:45"
    }
  ],
  "version_history": {
    "validate_email": ["1.0.0", "0.2.0", "0.1.1", "0.1.0"]
  }
}
```

---

## API Reference

### `update_skill(name, code, *, description=None, tags=None, bump_type="patch")`

Create a new version of a skill.

**Args:**
- `name`: Skill name
- `code`: New code
- `description`: Optional new description
- `tags`: Optional new tags
- `bump_type`: "major", "minor", or "patch"

**Returns:** New `Skill` object with incremented version

**Example:**
```python
v2 = update_skill("my_skill", new_code, bump_type="minor")
```

---

### `get_skill_versions(name)`

Get all versions of a skill.

**Args:**
- `name`: Skill name

**Returns:** List of version strings (newest first)

**Example:**
```python
versions = get_skill_versions("validate_email")
# ['1.0.0', '0.2.0', '0.1.1', '0.1.0']
```

---

### `get_skill_version(name, version)`

Get a specific version of a skill.

**Args:**
- `name`: Skill name
- `version`: Version string (e.g., "0.1.0")

**Returns:** `Skill` object or None if not found

**Example:**
```python
old_skill = get_skill_version("validate_email", "0.1.0")
if old_skill:
    print(old_skill.description)
```

---

### `rollback_skill(name, version)`

Restore a previous version as the current active version.

**Args:**
- `name`: Skill name
- `version`: Version to restore

**Returns:** `Skill` object for the restored version

**Raises:** `KeyError` if version not found

**Example:**
```python
restored = rollback_skill("validate_email", "0.1.0")
# validate_email is now at version 0.1.0
```

---

## Use Cases

### 1. Production Rollback

Quick recovery from a bad deployment:

```python
# Production is broken after deploying 1.5.0
# Quickly rollback to last known good version
rollback_skill("process_payment", "1.4.0")
```

### 2. A/B Testing

Compare two versions:

```python
v1 = get_skill_version("score_model", "1.0.0")
v2 = get_skill_version("score_model", "2.0.0")

# Run both on test data, compare results
```

### 3. Audit Trail

Track skill evolution for compliance:

```python
versions = get_skill_versions("audit_log_processor")
for version in versions:
    skill = get_skill_version("audit_log_processor", version)
    print(f"v{version}: {skill.description}")
```

### 4. Beta Testing

Deploy new features safely:

```python
# Current: 1.0.0 (stable)
# Add experimental feature
update_skill("feature", new_code, bump_type="minor")
# Result: 1.1.0 (beta)

# After validation, bump to minor
update_skill("feature", final_code, bump_type="minor")
# Result: 1.2.0 (stable)
```

---

## Best Practices

1. **Use Semantic Versioning**
   - MAJOR for breaking changes
   - MINOR for new features
   - PATCH for bug fixes

2. **Update Descriptions**
   - Explain what changed in each version
   - Help teams understand version differences

3. **Archive Regularly**
   - Periodically delete very old versions to save space
   - Implement retention policies (e.g., keep last 10 versions)

4. **Test Before Promotion**
   - Create new version locally first
   - Test thoroughly before promotion to production
   - Use `get_skill_version()` to validate before rollback

5. **Document Breaking Changes**
   - Always bump MAJOR when behavior changes
   - Add detailed notes in skill metadata
   - Update dependent skills accordingly

---

## Integration with Approval Workflow

Versioning works with the Git approval workflow:

```python
from orchestrator.execution import update_skill
from orchestrator.execution.skill_approval import promote_skill_to_git

# 1. Update skill (creates new version)
v2 = update_skill("process_order", new_code, bump_type="minor")

# 2. Review new version
review_pending_skills()  # Includes v2 in review

# 3. Promote to Git (includes version info)
promote_skill_to_git("process_order")  # Commits v2 with metadata
```

---

## Troubleshooting

**"Version not found" error**
- Check spelling of skill name and version
- Use `get_skill_versions(name)` to list available versions

**Can't rollback to old version**
- Version file may have been deleted
- Check `~/.toolweaver/skills/` directory for archived files

**Too many old versions**
- Implement cleanup: delete `<skill>_<old_version>.py` files manually
- Or implement archival policy (future enhancement)

---

## Future Enhancements

- Automatic cleanup of old versions (retention policies)
- Version comparison/diff viewer
- Batch versioning (update multiple skills)
- Version tagging (e.g., "production", "stable")
- Version promotion workflows
- Integration with CI/CD pipelines

---

## Related Documentation

- [Skill Library Reference](../reference/SKILL_LIBRARY.md)
- [Skill Approval Workflow](SKILL_APPROVAL.md)
- [Skill Metrics & Analytics](SKILL_METRICS.md)
