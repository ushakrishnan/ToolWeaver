# Skill Approval Workflow

This guide covers the Git-based approval flow for promoting skills from local development to version control.

## Overview

Skills go through three stages:
1. **Development**: Generated and saved locally (~/.toolweaver/skills)
2. **Approval**: Reviewed and validated by a human
3. **Promotion**: Committed to Git repository for team/production use

## Quick Start

### 1. Review Pending Skills

```powershell
python -m orchestrator.execution.skill_approval review
```

This interactive CLI shows:
- Skill metadata (name, description, tags)
- Validation results (syntax check)
- Code preview (first 10 lines)
- Approval prompt

Example session:
```
📋 Reviewing 2 pending skill(s)

============================================================
Skill: validate_email
Description: Validates email format using regex
Tags: validation, string
Code Path: C:\Users\...\validate_email.py

Validation: ✓ PASS

Code Preview:
   1 | import re
   2 | 
   3 | def validate(email: str) -> bool:
   4 |     """Validate email format."""
   5 |     pattern = r"^[^@]+@[^@]+\.[^@]+$"
   6 |     return bool(re.match(pattern, email))

============================================================
Approve 'validate_email'? [y/n/q(uit)]: y
Optional notes: Tested on 50+ examples
✓ Approved: validate_email
```

### 2. Promote to Git

```powershell
# Promote to current directory (must be a Git repo)
python -m orchestrator.execution.skill_approval promote validate_email

# Or specify Git repo path
python -m orchestrator.execution.skill_approval promote validate_email C:\path\to\repo
```

Output:
```
✓ Promoted 'validate_email' to Git
  Commit: a3f8d912
  File: skills\validate_email.py
```

## What Happens During Promotion

1. **Copy to Git repo**: Skill copied to `<repo>/skills/<name>.py`
2. **Add metadata header**: Approval details added as comments
3. **Git commit**: Automatic commit with skill metadata
4. **Track Git ref**: Commit hash saved in approval manifest

Example promoted file:
```python
# Skill: validate_email
# Description: Validates email format using regex
# Tags: validation, string
# Approved: 2025-01-15T14:23:45
# Approved by: ushak

import re

def validate(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[^@]+@[^@]+\.[^@]+$"
    return bool(re.match(pattern, email))
```

## Approval Manifest

Approvals tracked in `~/.toolweaver/skills/approved.json`:

```json
{
  "validate_email": {
    "skill_name": "validate_email",
    "approved_by": "ushak",
    "approved_at": "2025-01-15T14:23:45",
    "git_ref": "a3f8d9124c...",
    "validation_passed": true,
    "notes": "Tested on 50+ examples"
  }
}
```

## Validation Levels

By default, the review CLI runs **syntax validation** (AST parse). For stricter checks:

1. Edit `skill_approval.py` to use `validate_stub(code, level="full")`
2. This enables:
   - AST syntax check
   - Sandboxed execution
   - Optional mypy type checking

## Integration with CI/CD

You can automate promotion in CI pipelines:

```yaml
# Example GitHub Actions workflow
- name: Promote approved skills
  run: |
    python -m orchestrator.execution.skill_approval review --auto-approve
    python -m orchestrator.execution.skill_approval promote --all
```

*(Note: `--auto-approve` and `--all` flags are future enhancements)*

## Best Practices

1. **Review before approval**: Always inspect code and validation results
2. **Add notes**: Document test coverage, edge cases, known limitations
3. **Small skills**: Keep skills focused and single-purpose
4. **Tag consistently**: Use standard tags for discoverability
5. **Test in isolation**: Run the skill code independently before approval

## Troubleshooting

**"Skill is not approved"**
- Run `review` command first to approve the skill

**"Not a Git repository"**
- Ensure you're in a Git repo, or specify path with `promote <name> <path>`

**"Git operation failed"**
- Check Git credentials and working tree status
- Ensure no merge conflicts or uncommitted changes

## Future Enhancements

- Batch approval for multiple skills
- Approval rules (e.g., require tests, type hints)
- Rollback/revert promoted skills
- Remote approval via PR workflow
- Approval webhook notifications

## Related Documentation

- [Skill Library Reference](../reference/SKILL_LIBRARY.md)
- [Code Validation Guide](CODE_VALIDATION.md)
- [Executing Skills Guide](EXECUTING_SKILLS.md)
