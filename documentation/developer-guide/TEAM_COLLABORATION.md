<!-- Team Collaboration Docs -->
# Team Collaboration & Governance Guide

## Overview

Team Collaboration features enable **enterprise governance** for skill management with multi-person approvals, comments, change tracking, and audit logs. Essential for regulated environments and large organizations.

### Key Features

- **Approval Workflows**: Multi-person approval chains with configurable role-based access
- **Comments & Feedback**: Skill-level and line-specific code reviews
- **Change Tracking**: Unified diff viewer showing all skill modifications
- **Audit Logs**: Complete audit trail for compliance and security
- **Activity Feed**: Detailed history of all operations
- **Notifications**: Real-time alerts for approvals, ratings, and updates

---

## Quick Start

### 1. Configure Approval Settings

```python
from orchestrator.execution import ApprovalManager

# Set minimum approvals and allowed roles
manager = ApprovalManager(
    min_approvals=2,  # Require 2 approvals
    approver_roles=['reviewer', 'lead', 'admin']
)
```

Or use environment variables:
```bash
export APPROVAL_REQUIRED=2
export APPROVER_ROLES=reviewer,lead,admin
```

### 2. Request Skill Approval

```python
from orchestrator.execution import request_approval, Skill

skill = Skill(
    name='email_validator',
    code_path='/path/to/validate_email.py',
    version='1.0.0'
)

approval = request_approval(
    skill,
    submitter_id='user123',
    submitter_name='Alice Chen',
    description='Added regex validation for RFC 5322',
    target_org='acme'
)

print(f"Approval ID: {approval.id}")
```

### 3. Provide Approval

```python
from orchestrator.execution import provide_approval

# Approve the skill
updated = provide_approval(
    approval_id=approval.id,
    approver_id='reviewer1',
    approver_name='Bob Smith',
    approver_role='reviewer',
    approved=True,
    comment='Looks good, implementation is clean'
)

print(f"Status: {updated.status.value}")
print(f"Approvals: {updated.approval_count()}/{updated.required_approvals}")
```

### 4. Add Comments

```python
from orchestrator.execution import add_approval_comment

comment = add_approval_comment(
    approval_id=approval.id,
    author_id='reviewer2',
    author_name='Carol Davis',
    text='Consider adding internationalization support',
    line_number=45  # Specific code line
)
```

### 5. View and Publish

```python
from orchestrator.execution import (
    get_approval,
    get_pending_approvals,
    publish_approved_skill
)

# Check approval status
req = get_approval(approval.id)
if req.is_approved():
    publish_approved_skill(approval.id)
    print(f"Skill {req.skill_id} v{req.skill_version} published!")

# Get all pending approvals
pending = get_pending_approvals()
print(f"{len(pending)} skills awaiting approval")
```

---

## API Reference

### Approval Management

#### `request_approval(skill, submitter_id, submitter_name, description, target_org)`

Submit skill for approval.

**Parameters:**
- `skill` (Skill): Skill object with code and metadata
- `submitter_id` (str): User ID of submitter
- `submitter_name` (str): Display name (e.g., "Alice Chen")
- `description` (str): Detailed change description
- `target_org` (str): Target org for registry publication

**Returns:** `ApprovalRequest` with status PENDING

**Example:**
```python
approval = request_approval(
    skill,
    submitter_id='alice123',
    submitter_name='Alice Chen',
    description='Bug fix: handle malformed emails',
    target_org='acme'
)
```

---

#### `provide_approval(approval_id, approver_id, approver_name, approver_role, approved, comment)`

Provide approval or rejection.

**Parameters:**
- `approval_id` (str): Approval request ID
- `approver_id` (str): Approver user ID
- `approver_name` (str): Approver display name
- `approver_role` (str): Role (must be in APPROVER_ROLES)
- `approved` (bool): True to approve, False to reject
- `comment` (str): Optional feedback

**Returns:** Updated `ApprovalRequest`

**Raises:** ValueError if role invalid or approval not found

**Example:**
```python
# Approve
result = provide_approval(
    approval_id='req123',
    approver_id='bob456',
    approver_name='Bob Smith',
    approver_role='reviewer',
    approved=True,
    comment='Approved! Code quality is good.'
)

# Reject
result = provide_approval(
    approval_id='req123',
    approver_id='carol789',
    approver_name='Carol Davis',
    approver_role='lead',
    approved=False,
    comment='Needs more test coverage (< 80%)'
)
```

---

#### `add_approval_comment(approval_id, author_id, author_name, text, line_number)`

Add comment to approval request.

**Parameters:**
- `approval_id` (str): Approval request ID
- `author_id` (str): Comment author user ID
- `author_name` (str): Author display name
- `text` (str): Comment text
- `line_number` (int): Optional code line number

**Returns:** `Comment` object

**Example:**
```python
comment = add_approval_comment(
    approval_id='req123',
    author_id='alice123',
    author_name='Alice Chen',
    text='Fixed this in latest commit',
    line_number=42
)
```

---

#### `get_approval(approval_id)`

Retrieve approval request details.

**Parameters:**
- `approval_id` (str): Approval request ID

**Returns:** `ApprovalRequest` or None

**Example:**
```python
req = get_approval('req123')
print(f"Status: {req.status.value}")
print(f"Approvals: {req.approval_count()}/{req.required_approvals}")
print(f"Rejected: {req.rejection_count() > 0}")
```

---

#### `get_pending_approvals()`

Get all pending approval requests.

**Returns:** List of `ApprovalRequest` with status PENDING

**Example:**
```python
pending = get_pending_approvals()
for req in pending:
    print(f"{req.skill_id} - {req.approval_count()} approvals needed")
```

---

#### `get_my_approvals(user_id)`

Get approval requests submitted by user.

**Parameters:**
- `user_id` (str): User ID

**Returns:** List of `ApprovalRequest` submitted by user

**Example:**
```python
my_requests = get_my_approvals('alice123')
print(f"You have {len(my_requests)} pending requests")
```

---

#### `publish_approved_skill(approval_id)`

Publish approved skill to registry.

**Parameters:**
- `approval_id` (str): Approved approval request ID

**Returns:** True if successful, False if not fully approved

**Example:**
```python
if publish_approved_skill('req123'):
    print("Skill published to registry!")
else:
    print("Skill not yet fully approved")
```

---

### Change Tracking

#### `record_skill_change(skill, version_from, changed_by, old_code, summary)`

Record skill change for history and diff tracking.

**Parameters:**
- `skill` (Skill): Updated skill
- `version_from` (str): Previous version
- `changed_by` (str): User ID who made change
- `old_code` (str): Previous code (optional)
- `summary` (str): Change description

**Returns:** `SkillChange` object

**Example:**
```python
change = record_skill_change(
    skill=updated_skill,
    version_from='1.0.0',
    changed_by='alice123',
    old_code=previous_code,
    summary='Added regex validation support'
)
```

---

#### `get_skill_change_history(skill_id)`

Get all changes for a skill.

**Parameters:**
- `skill_id` (str): Skill name

**Returns:** List of `SkillChange` objects (newest first)

**Example:**
```python
history = get_skill_change_history('email_validator')
for change in history:
    print(f"{change.version_from} -> {change.version_to}")
    print(f"  Changed by: {change.changed_by}")
    print(f"  Summary: {change.summary}")
```

---

#### `get_code_diff(skill_id, version1, version2)`

Get unified diff between skill versions.

**Parameters:**
- `skill_id` (str): Skill name
- `version1` (str): First version
- `version2` (str): Second version

**Returns:** Unified diff string (can be empty if not found)

**Example:**
```python
diff = get_code_diff('email_validator', '1.0.0', '1.1.0')
print(diff)  # Unified diff format with +/- lines
```

---

### Audit Logging

#### `get_audit_logs(resource_type, action, actor_id, days)`

Query audit logs with filters.

**Parameters:**
- `resource_type` (str): Filter by type (skill, approval, comment)
- `action` (AuditAction): Filter by action type
- `actor_id` (str): Filter by user ID
- `days` (int): Only logs from last N days (default: 30)

**Returns:** List of `AuditLogEntry` (newest first)

**Example:**
```python
# Get all approval activities
approvals = get_audit_logs(
    resource_type='approval',
    days=30
)

# Get changes by specific user
user_changes = get_audit_logs(
    resource_type='skill',
    action=AuditAction.SKILL_UPDATED,
    actor_id='alice123',
    days=90
)

for entry in user_changes:
    print(f"{entry.timestamp}: {entry.action.value}")
    print(f"  Resource: {entry.resource_id}")
    print(f"  Details: {entry.details}")
```

---

#### `generate_audit_report(days)`

Generate audit report for compliance/security review.

**Parameters:**
- `days` (int): Report period in days (default: 30)

**Returns:** Dict with:
- `period_days` - Report period
- `total_entries` - Total audit entries
- `by_action` - Count by action type
- `by_actor` - Count by user
- `entries` - Full entry list

**Example:**
```python
report = generate_audit_report(days=90)
print(f"Report: {report['period_days']} days")
print(f"Total actions: {report['total_entries']}")
print(f"By action: {report['by_action']}")
print(f"By actor: {report['by_actor']}")

# Export to JSON for compliance
import json
with open('audit_report.json', 'w') as f:
    json.dump(report, f)
```

---

### Data Classes

#### `ApprovalRequest`

Skill approval request.

**Key Attributes:**
- `id` (str): Unique approval ID (UUID)
- `skill_id` (str): Skill name
- `skill_name` (str): Display name
- `skill_version` (str): Semantic version
- `submitted_by` (str): Submitter user ID
- `submitted_at` (str): ISO timestamp
- `status` (ApprovalStatus): Current status
- `required_approvals` (int): Min approvals needed
- `approvals` (list): List of Approval objects
- `rejections` (list): List of rejections
- `comments` (list): List of Comment objects
- `description` (str): Change description
- `target_org` (str): Target organization

**Methods:**
- `approval_count()` - Number of approvals
- `rejection_count()` - Number of rejections
- `is_approved()` - Whether threshold met
- `is_rejected()` - Whether any rejections

**Example:**
```python
req = get_approval('req123')
print(f"Skill: {req.skill_id} v{req.skill_version}")
print(f"Status: {req.status.value}")
print(f"Approvals: {req.approval_count()}/{req.required_approvals}")

if req.is_approved():
    print("Ready to publish!")
elif req.is_rejected():
    print("Needs rework")
else:
    print(f"Waiting for {req.required_approvals - req.approval_count()} more approvals")
```

---

#### `Comment`

Comment on approval request.

**Attributes:**
- `id` (str): Unique comment ID
- `author_id` (str): Author user ID
- `author_name` (str): Author display name
- `timestamp` (str): ISO timestamp
- `text` (str): Comment text
- `line_number` (int): Optional code line number
- `resolved` (bool): Whether resolved/addressed

---

#### `AuditLogEntry`

Single audit log entry.

**Attributes:**
- `id` (str): Entry ID (UUID)
- `timestamp` (str): ISO timestamp
- `action` (AuditAction): Action type enum
- `actor_id` (str): User ID who performed action
- `actor_name` (str): User display name
- `resource_type` (str): Resource type
- `resource_id` (str): Resource identifier
- `details` (dict): Additional details
- `ip_address` (str): Optional IP address

**Available Actions:**
- `SKILL_CREATED` - Skill created
- `SKILL_UPDATED` - Skill updated
- `SKILL_DELETED` - Skill deleted
- `APPROVAL_REQUESTED` - Approval request submitted
- `APPROVAL_PROVIDED` - Approval provided
- `APPROVAL_REJECTED` - Approval rejected
- `SKILL_PUBLISHED` - Skill published to registry
- `COMMENT_ADDED` - Comment added
- `COMMENT_DELETED` - Comment deleted

---

## Workflow Examples

### Complete Approval Workflow

```python
from orchestrator.execution import (
    request_approval,
    provide_approval,
    add_approval_comment,
    get_pending_approvals,
    publish_approved_skill,
    Skill
)

# 1. Developer submits skill for approval
skill = Skill(
    name='payment_processor',
    code_path='/path/to/payment.py',
    version='2.0.0',
    description='Processes payment transactions'
)

approval = request_approval(
    skill,
    submitter_id='alice123',
    submitter_name='Alice Chen',
    description='Upgraded to v2.0 with PCI-DSS compliance',
    target_org='acme/payments'
)

# 2. First reviewer provides feedback
comment = add_approval_comment(
    approval_id=approval.id,
    author_id='bob456',
    author_name='Bob Smith',
    text='Please add encryption for card numbers',
    line_number=42
)

# 3. Developer makes changes and resubmits
# (In real flow, would update skill and create new approval)

# 4. Both reviewers approve
provide_approval(
    approval_id=approval.id,
    approver_id='bob456',
    approver_name='Bob Smith',
    approver_role='reviewer',
    approved=True,
    comment='Looks good now!'
)

provide_approval(
    approval_id=approval.id,
    approver_id='carol789',
    approver_name='Carol Davis',
    approver_role='lead',
    approved=True,
    comment='Approved for production'
)

# 5. Publish to registry
if publish_approved_skill(approval.id):
    print("Skill published to registry!")
```

---

### View Change History

```python
from orchestrator.execution import (
    record_skill_change,
    get_skill_change_history,
    get_code_diff
)

# Record change when updating skill
change = record_skill_change(
    skill=updated_skill,
    version_from='1.0.0',
    changed_by='alice123',
    old_code=prev_code,
    summary='Fixed email validation regex'
)

# View history
history = get_skill_change_history('email_validator')
print(f"Total versions: {len(history)}")

for change in history:
    print(f"\n{change.version_from} -> {change.version_to}")
    print(f"  By: {change.changed_by}")
    print(f"  Date: {change.changed_at}")
    print(f"  Summary: {change.summary}")

# View code diff
diff = get_code_diff('email_validator', '1.0.0', '1.1.0')
print("\n=== Code Changes ===")
print(diff)
```

---

### Audit Report for Compliance

```python
from orchestrator.execution import (
    get_audit_logs,
    generate_audit_report,
    AuditAction
)

# Generate 90-day compliance report
report = generate_audit_report(days=90)

print(f"Audit Report: {report['period_days']} days")
print(f"Total entries: {report['total_entries']}")

print("\nBy Action:")
for action, count in report['by_action'].items():
    print(f"  {action}: {count}")

print("\nBy Actor (top 5):")
sorted_actors = sorted(
    report['by_actor'].items(),
    key=lambda x: x[1],
    reverse=True
)[:5]
for actor, count in sorted_actors:
    print(f"  {actor}: {count}")

# Save for auditor review
import json
with open('compliance_audit.json', 'w') as f:
    json.dump(report, f, indent=2)
print("\nReport saved to compliance_audit.json")
```

---

## Configuration

### Environment Variables

```bash
# Minimum approvals required to publish
export APPROVAL_REQUIRED=2

# Comma-separated list of valid approver roles
export APPROVER_ROLES=reviewer,lead,admin

# Email for approval notifications (optional)
export NOTIFY_EMAIL=approvals@company.com

# Audit log retention (days)
export AUDIT_LOG_RETENTION_DAYS=365
```

### File Locations

Collaboration data stored in:
```
~/.toolweaver/
  approvals/              # Approval requests
  audit_logs/            # Audit trail
  change_tracking/       # Change diffs
```

---

## Security Considerations

- **Role-Based Access**: Only designated approvers can approve skills
- **Audit Trail**: All operations logged immutably
- **Change Tracking**: Complete version history with diffs
- **Comments**: Feedback preserved for compliance
- **Timestamps**: All entries timestamped (ISO format)
- **IP Tracking**: Optional IP address logging (enterprise deployments)

---

## Integration with Other Features

**Phase 4.1 - Versioning**
- Approval records version changes
- Change tracking integrates with version history

**Phase 4.2 - Workflows**
- Approved skills can be used in workflows
- Workflow execution creates audit entries

**Phase 4.3 - Registry**
- Registry publication requires approval
- Registry ratings tracked in audit logs

**Phase 3.3 - Git Approval**
- Git approval and team approval can work together
- Use both for maximum governance

---

## What's Next?

**Phase 5: Advanced Analytics**
- Skill usage metrics and trends
- Author/team leaderboards
- Dependency analysis
- Performance benchmarks
- Skill recommendation engine

**Phase 6: Workflow Orchestration**
- Multi-skill workflow optimization
- Error recovery and retry policies
- Distributed execution
- Resource scheduling
