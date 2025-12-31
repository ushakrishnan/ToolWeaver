"""
Team Collaboration Features for ToolWeaver

Enables enterprise governance through:
- Multi-person approval chains with role-based permissions
- Comments and feedback on skills
- Change tracking with diff viewer
- Audit logs tracking all operations
- Notifications for approvals, ratings, and updates
- Activity feed with detailed history

Approval Flow:
  1. Developer publishes skill draft
  2. Skill enters approval queue
  3. Reviewers/approvers provide feedback via comments
  4. After N approvals, skill is published to registry
  5. Audit log tracks all changes and approvals
  6. Notifications sent to subscribers

Storage:
  ~/.toolweaver/approvals/           - Approval queue and history
  ~/.toolweaver/audit_logs/          - Audit trail for compliance
  ~/.toolweaver/change_tracking/     - Diff history for skills

Environment:
  APPROVAL_REQUIRED        - Minimum approvals to publish (default: 1)
  APPROVER_ROLES           - Comma-separated roles (default: "reviewer,admin")
  NOTIFY_EMAIL             - Email for notifications (optional)
  AUDIT_LOG_RETENTION_DAYS - Keep audit logs (default: 365)
"""

import difflib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from .skill_library import Skill

logger = logging.getLogger(__name__)

# Configuration
_APPROVAL_DIR = Path.home() / '.toolweaver' / 'approvals'
_AUDIT_DIR = Path.home() / '.toolweaver' / 'audit_logs'
_CHANGE_DIR = Path.home() / '.toolweaver' / 'change_tracking'
_APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
_AUDIT_DIR.mkdir(parents=True, exist_ok=True)
_CHANGE_DIR.mkdir(parents=True, exist_ok=True)


class ApprovalStatus(Enum):
    """Approval request status."""
    DRAFT = "draft"              # Initial submission
    PENDING = "pending"          # Awaiting approval
    APPROVED = "approved"        # All approvals received
    REJECTED = "rejected"        # Rejected by reviewer
    CANCELLED = "cancelled"      # Cancelled by author
    PUBLISHED = "published"      # Published to registry


class AuditAction(Enum):
    """Type of action for audit log."""
    SKILL_CREATED = "skill_created"
    SKILL_UPDATED = "skill_updated"
    SKILL_DELETED = "skill_deleted"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_PROVIDED = "approval_provided"
    APPROVAL_REJECTED = "approval_rejected"
    APPROVAL_CANCELLED = "approval_cancelled"
    SKILL_PUBLISHED = "skill_published"
    COMMENT_ADDED = "comment_added"
    COMMENT_DELETED = "comment_deleted"
    PERMISSION_CHANGED = "permission_changed"
    NOTIFICATION_SENT = "notification_sent"


@dataclass
class Approval:
    """Approval from a reviewer."""
    approver_id: str
    approver_name: str
    approver_role: str  # "reviewer", "admin", etc.
    timestamp: str  # ISO timestamp
    approved: bool
    comment: str = ""


@dataclass
class Comment:
    """Comment on a skill or approval."""
    id: str
    author_id: str
    author_name: str
    timestamp: str  # ISO timestamp
    text: str
    line_number: int | None = None  # For code-specific comments
    resolved: bool = False


@dataclass
class SkillChange:
    """Change/diff for a skill version."""
    skill_id: str
    version_from: str
    version_to: str
    changed_at: str  # ISO timestamp
    changed_by: str
    summary: str  # Brief change description
    code_diff: str = ""  # Unified diff format
    metadata_diff: dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalRequest:
    """Skill approval request in workflow."""
    id: str  # Unique approval ID
    skill_id: str
    skill_name: str
    skill_version: str
    submitted_by: str  # Developer who submitted
    submitted_at: str  # ISO timestamp
    status: ApprovalStatus
    required_approvals: int = 1
    approvals: list[Approval] = field(default_factory=list)
    rejections: list[Approval] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    description: str = ""
    target_org: str = ""  # Registry org for publication

    def approval_count(self) -> int:
        """Number of approvals received."""
        return len([a for a in self.approvals if a.approved])

    def rejection_count(self) -> int:
        """Number of rejections."""
        return len(self.rejections)

    def is_approved(self) -> bool:
        """Check if approval threshold met."""
        return self.approval_count() >= self.required_approvals

    def is_rejected(self) -> bool:
        """Check if rejected."""
        return self.rejection_count() > 0


@dataclass
class AuditLogEntry:
    """Single audit log entry for compliance tracking."""
    id: str
    timestamp: str  # ISO timestamp
    action: AuditAction
    actor_id: str
    actor_name: str
    resource_type: str  # "skill", "approval", "comment"
    resource_id: str
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict with action as string."""
        data = asdict(self)
        data['action'] = self.action.value
        return data


class ApprovalManager:
    """Manage skill approval workflows."""

    def __init__(self, min_approvals: int = 1, approver_roles: list[str] | None = None):
        """Initialize approval manager."""
        self.min_approvals = min_approvals
        self.approver_roles = approver_roles or ["reviewer", "admin"]

    def request_approval(self, skill: Skill, submitter_id: str, submitter_name: str,
                        description: str = "", target_org: str = "") -> ApprovalRequest:
        """
        Submit skill for approval.
        
        Args:
            skill: Skill to approve
            submitter_id: User ID of submitter
            submitter_name: Display name of submitter
            description: Detailed change description
            target_org: Target registry org for publication
        
        Returns:
            ApprovalRequest with unique ID
        """
        import uuid

        request = ApprovalRequest(
            id=str(uuid.uuid4()),
            skill_id=skill.name,
            skill_name=skill.name,
            skill_version=skill.version,
            submitted_by=submitter_id,
            submitted_at=datetime.utcnow().isoformat(),
            status=ApprovalStatus.PENDING,
            required_approvals=self.min_approvals,
            description=description,
            target_org=target_org,
        )

        # Save approval request
        self._save_approval(request)

        # Audit log
        self._audit_log(
            AuditAction.APPROVAL_REQUESTED,
            submitter_id,
            submitter_name,
            'approval',
            request.id,
            {'skill': skill.name, 'version': skill.version}
        )

        logger.info(f"Approval requested for {skill.name} v{skill.version}")
        return request

    def provide_approval(self, approval_id: str, approver_id: str, approver_name: str,
                        approver_role: str, approved: bool, comment: str = "") -> ApprovalRequest:
        """
        Provide approval/rejection for skill.
        
        Args:
            approval_id: Approval request ID
            approver_id: Approver user ID
            approver_name: Approver display name
            approver_role: Role (must be in approver_roles)
            approved: True to approve, False to reject
            comment: Feedback comment
        
        Returns:
            Updated ApprovalRequest
        
        Raises:
            ValueError: If approval not found or role invalid
        """
        if approver_role not in self.approver_roles:
            raise ValueError(f"Invalid role: {approver_role}")

        request = self._load_approval(approval_id)
        if not request:
            raise ValueError(f"Approval not found: {approval_id}")

        approval = Approval(
            approver_id=approver_id,
            approver_name=approver_name,
            approver_role=approver_role,
            timestamp=datetime.utcnow().isoformat(),
            approved=approved,
            comment=comment,
        )

        if approved:
            request.approvals.append(approval)
        else:
            request.rejections.append(approval)

        # Update status
        if request.rejection_count() > 0:
            request.status = ApprovalStatus.REJECTED
        elif request.is_approved():
            request.status = ApprovalStatus.APPROVED

        # Save updated request
        self._save_approval(request)

        # Audit log
        action = AuditAction.APPROVAL_PROVIDED if approved else AuditAction.APPROVAL_REJECTED
        self._audit_log(
            action,
            approver_id,
            approver_name,
            'approval',
            approval_id,
            {'approved': approved, 'comment': comment}
        )

        logger.info(f"Approval {'provided' if approved else 'rejected'} for {request.skill_id}")
        return request

    def add_comment(self, approval_id: str, author_id: str, author_name: str,
                   text: str, line_number: int | None = None) -> Comment:
        """
        Add comment to approval request.
        
        Args:
            approval_id: Approval request ID
            author_id: Comment author user ID
            author_name: Author display name
            text: Comment text
            line_number: Optional code line number
        
        Returns:
            Comment object
        """
        import uuid

        request = self._load_approval(approval_id)
        if not request:
            raise ValueError(f"Approval not found: {approval_id}")

        comment = Comment(
            id=str(uuid.uuid4()),
            author_id=author_id,
            author_name=author_name,
            timestamp=datetime.utcnow().isoformat(),
            text=text,
            line_number=line_number,
        )

        request.comments.append(comment)
        self._save_approval(request)

        # Audit log
        self._audit_log(
            AuditAction.COMMENT_ADDED,
            author_id,
            author_name,
            'comment',
            comment.id,
            {'approval_id': approval_id, 'text': text[:100]}
        )

        return comment

    def get_approval(self, approval_id: str) -> ApprovalRequest | None:
        """Get approval request by ID."""
        return self._load_approval(approval_id)

    def get_pending_approvals(self) -> list[ApprovalRequest]:
        """Get all pending approval requests."""
        approvals = []
        for path in _APPROVAL_DIR.glob("*.json"):
            try:
                request = self._load_approval_from_file(path)
                if request and request.status == ApprovalStatus.PENDING:
                    approvals.append(request)
            except Exception as e:
                logger.error(f"Failed to load approval {path}: {e}")
        return approvals

    def get_approvals_for_user(self, user_id: str) -> list[ApprovalRequest]:
        """Get approval requests submitted by user."""
        approvals = []
        for path in _APPROVAL_DIR.glob("*.json"):
            try:
                request = self._load_approval_from_file(path)
                if request and request.submitted_by == user_id:
                    approvals.append(request)
            except Exception as e:
                logger.error(f"Failed to load approval {path}: {e}")
        return approvals

    def publish_approved_skill(self, approval_id: str) -> bool:
        """
        Mark approved skill as published.
        
        Args:
            approval_id: Approval request ID
        
        Returns:
            True if published successfully
        """
        request = self._load_approval(approval_id)
        if not request:
            return False

        if not request.is_approved():
            logger.warning(f"Approval {approval_id} not yet fully approved")
            return False

        request.status = ApprovalStatus.PUBLISHED
        self._save_approval(request)

        self._audit_log(
            AuditAction.SKILL_PUBLISHED,
            'system',
            'ToolWeaver',
            'skill',
            request.skill_id,
            {'version': request.skill_version}
        )

        return True

    def _save_approval(self, request: ApprovalRequest) -> None:
        """Save approval request to disk."""
        path = _APPROVAL_DIR / f"{request.id}.json"
        data = asdict(request)
        data['status'] = request.status.value
        data['approvals'] = [asdict(a) for a in request.approvals]
        data['rejections'] = [asdict(a) for a in request.rejections]
        data['comments'] = [asdict(c) for c in request.comments]

        path.write_text(json.dumps(data, indent=2))

    def _load_approval(self, approval_id: str) -> ApprovalRequest | None:
        """Load approval request from disk."""
        path = _APPROVAL_DIR / f"{approval_id}.json"
        return self._load_approval_from_file(path)

    def _load_approval_from_file(self, path: Path) -> ApprovalRequest | None:
        """Load approval from file."""
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text())

            # Reconstruct objects
            approvals = [Approval(**a) for a in data.get('approvals', [])]
            rejections = [Approval(**r) for r in data.get('rejections', [])]
            comments = [Comment(**c) for c in data.get('comments', [])]

            status_str = data.get('status', 'pending')
            status = ApprovalStatus[status_str.upper()] if isinstance(status_str, str) else ApprovalStatus(status_str)

            return ApprovalRequest(
                id=data['id'],
                skill_id=data['skill_id'],
                skill_name=data['skill_name'],
                skill_version=data['skill_version'],
                submitted_by=data['submitted_by'],
                submitted_at=data['submitted_at'],
                status=status,
                required_approvals=data.get('required_approvals', 1),
                approvals=approvals,
                rejections=rejections,
                comments=comments,
                description=data.get('description', ''),
                target_org=data.get('target_org', ''),
            )
        except Exception as e:
            logger.error(f"Failed to load approval from {path}: {e}")
            return None

    def _audit_log(self, action: AuditAction, actor_id: str, actor_name: str,
                  resource_type: str, resource_id: str, details: dict[str, Any] | None = None) -> None:
        """Create audit log entry."""
        import uuid

        entry = AuditLogEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            action=action,
            actor_id=actor_id,
            actor_name=actor_name,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
        )

        path = _AUDIT_DIR / f"{entry.id}.json"
        path.write_text(json.dumps(entry.to_dict(), indent=2))

        logger.debug(f"Audit: {action.value} by {actor_name}")


class ChangeTracker:
    """Track and diff skill changes."""

    @staticmethod
    def record_change(skill: Skill, version_from: str, changed_by: str,
                     old_code: str = "", summary: str = "") -> SkillChange:
        """
        Record a skill change/update.
        
        Args:
            skill: Updated skill
            version_from: Previous version
            changed_by: User ID of person who made change
            old_code: Previous code for diff
            summary: Change description
        
        Returns:
            SkillChange object
        """

        # Generate code diff
        old_lines = old_code.splitlines(keepends=True) if old_code else []
        new_lines = skill.code_path.splitlines(keepends=True) if isinstance(skill.code_path, str) else []

        diff_lines = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
        code_diff = '\n'.join(diff_lines)

        change = SkillChange(
            skill_id=skill.name,
            version_from=version_from,
            version_to=skill.version,
            changed_at=datetime.utcnow().isoformat(),
            changed_by=changed_by,
            summary=summary or f"Updated to {skill.version}",
            code_diff=code_diff,
        )

        # Save change record
        path = _CHANGE_DIR / f"{skill.name}_{skill.version}.json"
        data = asdict(change)
        path.write_text(json.dumps(data, indent=2))

        logger.info(f"Recorded change for {skill.name}: {version_from} -> {skill.version}")
        return change

    @staticmethod
    def get_change_history(skill_id: str) -> list[SkillChange]:
        """Get all changes for a skill."""
        changes = []
        pattern = f"{skill_id}_*.json"

        for path in _CHANGE_DIR.glob(pattern):
            try:
                data = json.loads(path.read_text())
                change = SkillChange(
                    skill_id=data['skill_id'],
                    version_from=data['version_from'],
                    version_to=data['version_to'],
                    changed_at=data['changed_at'],
                    changed_by=data['changed_by'],
                    summary=data['summary'],
                    code_diff=data.get('code_diff', ''),
                    metadata_diff=data.get('metadata_diff', {}),
                )
                changes.append(change)
            except Exception as e:
                logger.error(f"Failed to load change {path}: {e}")

        # Sort by version date
        return sorted(changes, key=lambda c: c.changed_at, reverse=True)

    @staticmethod
    def get_code_diff(skill_id: str, version1: str, version2: str) -> str:
        """Get diff between two skill versions."""
        path1 = _CHANGE_DIR / f"{skill_id}_{version1}.json"
        path2 = _CHANGE_DIR / f"{skill_id}_{version2}.json"

        if not path1.exists() or not path2.exists():
            return ""

        data1 = json.loads(path1.read_text())
        data2 = json.loads(path2.read_text())

        # Return the diff from version1 to version2
        if data2.get('version_from') == version1:
            value = data2.get('code_diff', '')
            return value if isinstance(value, str) else ""

        return ""


class AuditLog:
    """Query and report audit logs."""

    @staticmethod
    def get_logs(resource_type: str | None = None, action: AuditAction | None = None,
                actor_id: str | None = None, days: int = 30) -> list[AuditLogEntry]:
        """
        Query audit logs with filters.
        
        Args:
            resource_type: Filter by resource type (skill, approval, comment)
            action: Filter by action type
            actor_id: Filter by actor user ID
            days: Only logs from last N days
        
        Returns:
            List of matching audit log entries
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        entries = []

        for path in _AUDIT_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                entry_date = data.get('timestamp', '')

                # Filter by date
                if entry_date < cutoff_date:
                    continue

                # Filter by resource type
                if resource_type and data.get('resource_type') != resource_type:
                    continue

                # Filter by action
                if action and data.get('action') != action.value:
                    continue

                # Filter by actor
                if actor_id and data.get('actor_id') != actor_id:
                    continue

                # Reconstruct entry
                entry = AuditLogEntry(
                    id=data['id'],
                    timestamp=data['timestamp'],
                    action=AuditAction(data['action']),
                    actor_id=data['actor_id'],
                    actor_name=data['actor_name'],
                    resource_type=data['resource_type'],
                    resource_id=data['resource_id'],
                    details=data.get('details', {}),
                )
                entries.append(entry)
            except Exception as e:
                logger.error(f"Failed to load audit log {path}: {e}")

        # Sort by timestamp, most recent first
        return sorted(entries, key=lambda e: e.timestamp, reverse=True)

    @staticmethod
    def generate_report(days: int = 30) -> dict[str, Any]:
        """Generate audit report for specified period."""
        entries = AuditLog.get_logs(days=days)

        # Count by action
        action_counts: dict[str, int] = {}
        for entry in entries:
            action = entry.action.value
            action_counts[action] = action_counts.get(action, 0) + 1

        # Count by actor
        actor_counts: dict[str, int] = {}
        for entry in entries:
            actor_counts[entry.actor_name] = actor_counts.get(entry.actor_name, 0) + 1

        return {
            'period_days': days,
            'total_entries': len(entries),
            'by_action': action_counts,
            'by_actor': actor_counts,
            'entries': [e.to_dict() for e in entries],
        }


# Module-level convenience functions

_approval_manager = None

def _get_approval_manager() -> ApprovalManager:
    """Get or create approval manager."""
    global _approval_manager
    if _approval_manager is None:
        import os
        min_approvals = int(os.getenv('APPROVAL_REQUIRED', '1'))
        approver_roles = os.getenv('APPROVER_ROLES', 'reviewer,admin').split(',')
        _approval_manager = ApprovalManager(min_approvals, approver_roles)
    return _approval_manager


def request_approval(skill: Skill, submitter_id: str, submitter_name: str,
                    description: str = "", target_org: str = "") -> ApprovalRequest:
    """Request skill approval."""
    return _get_approval_manager().request_approval(skill, submitter_id, submitter_name, description, target_org)


def provide_approval(approval_id: str, approver_id: str, approver_name: str,
                    approver_role: str, approved: bool, comment: str = "") -> ApprovalRequest:
    """Provide approval or rejection."""
    return _get_approval_manager().provide_approval(approval_id, approver_id, approver_name, approver_role, approved, comment)


def add_approval_comment(approval_id: str, author_id: str, author_name: str,
                        text: str, line_number: int | None = None) -> Comment:
    """Add comment to approval."""
    return _get_approval_manager().add_comment(approval_id, author_id, author_name, text, line_number)


def get_approval(approval_id: str) -> ApprovalRequest | None:
    """Get approval by ID."""
    return _get_approval_manager().get_approval(approval_id)


def get_pending_approvals() -> list[ApprovalRequest]:
    """Get pending approvals."""
    return _get_approval_manager().get_pending_approvals()


def get_my_approvals(user_id: str) -> list[ApprovalRequest]:
    """Get approvals submitted by user."""
    return _get_approval_manager().get_approvals_for_user(user_id)


def publish_approved_skill(approval_id: str) -> bool:
    """Publish approved skill to registry."""
    return _get_approval_manager().publish_approved_skill(approval_id)


def record_skill_change(skill: Skill, version_from: str, changed_by: str,
                       old_code: str = "", summary: str = "") -> SkillChange:
    """Record skill change."""
    return ChangeTracker.record_change(skill, version_from, changed_by, old_code, summary)


def get_skill_change_history(skill_id: str) -> list[SkillChange]:
    """Get change history for skill."""
    return ChangeTracker.get_change_history(skill_id)


def get_code_diff(skill_id: str, version1: str, version2: str) -> str:
    """Get code diff between versions."""
    return ChangeTracker.get_code_diff(skill_id, version1, version2)


def get_audit_logs(resource_type: str | None = None, action: AuditAction | None = None,
                  actor_id: str | None = None, days: int = 30) -> list[AuditLogEntry]:
    """Get audit logs."""
    return AuditLog.get_logs(resource_type, action, actor_id, days)


def generate_audit_report(days: int = 30) -> dict[str, Any]:
    """Generate audit report."""
    return AuditLog.generate_report(days)
