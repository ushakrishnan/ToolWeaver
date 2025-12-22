"""
Skill Approval and Git Promotion

CLI workflow to review, approve, and promote skills to version control.

Usage:
    python -m orchestrator.execution.skill_approval review
    python -m orchestrator.execution.skill_approval promote <skill_name>
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import sys

from .skill_library import Skill, list_skills, get_skill
from .validation import validate_stub

logger = logging.getLogger(__name__)

_ROOT = Path.home() / ".toolweaver" / "skills"
_APPROVAL_MANIFEST = _ROOT / "approved.json"


@dataclass
class ApprovalRecord:
    """Tracks approval status and Git metadata for a skill."""
    skill_name: str
    approved_by: str
    approved_at: str
    git_ref: Optional[str] = None  # commit hash after promotion
    validation_passed: bool = False
    notes: str = ""


def _load_approvals() -> Dict[str, ApprovalRecord]:
    """Load approval manifest."""
    if not _APPROVAL_MANIFEST.exists():
        return {}
    try:
        data = json.loads(_APPROVAL_MANIFEST.read_text())
        return {
            name: ApprovalRecord(**record)
            for name, record in data.items()
        }
    except Exception:
        return {}


def _save_approvals(approvals: Dict[str, ApprovalRecord]) -> None:
    """Save approval manifest."""
    data = {name: asdict(record) for name, record in approvals.items()}
    _APPROVAL_MANIFEST.write_text(json.dumps(data, indent=2))


def review_pending_skills() -> None:
    """
    Interactive CLI to review unapproved skills.
    
    Shows skill details, validation results, and prompts for approval.
    """
    approvals = _load_approvals()
    all_skills = list_skills()
    
    pending = [s for s in all_skills if s.name not in approvals]
    
    if not pending:
        print("✓ No pending skills to review")
        return
    
    print(f"\n📋 Reviewing {len(pending)} pending skill(s)\n")
    
    for skill in pending:
        print(f"{'='*60}")
        print(f"Skill: {skill.name}")
        print(f"Description: {skill.description or '(none)'}")
        print(f"Tags: {', '.join(skill.tags or [])}")
        print(f"Code Path: {skill.code_path}")
        
        # Run validation
        code = Path(skill.code_path).read_text()
        validation = validate_stub(code, level="syntax")  # Quick syntax check
        
        print(f"\nValidation: {'✓ PASS' if validation['passed'] else '✗ FAIL'}")
        if not validation['passed']:
            print(f"  Error: {validation.get('syntax_error', 'Unknown error')}")
        
        # Preview code (first 10 lines)
        lines = code.split("\n")[:10]
        print(f"\nCode Preview:")
        for i, line in enumerate(lines, 1):
            print(f"  {i:2d} | {line}")
        if len(code.split("\n")) > 10:
            print(f"  ... ({len(code.split('\n')) - 10} more lines)")
        
        # Prompt for approval
        print(f"\n{'='*60}")
        action = input(f"Approve '{skill.name}'? [y/n/q(uit)]: ").strip().lower()
        
        if action == 'q':
            print("\nReview session ended")
            return
        elif action == 'y':
            # Create approval record
            import datetime
            import getpass
            
            record = ApprovalRecord(
                skill_name=skill.name,
                approved_by=getpass.getuser(),
                approved_at=datetime.datetime.now().isoformat(),
                validation_passed=validation['passed'],
                notes=input("Optional notes: ").strip()
            )
            
            approvals[skill.name] = record
            _save_approvals(approvals)
            print(f"✓ Approved: {skill.name}\n")
        else:
            print(f"⊗ Skipped: {skill.name}\n")


def promote_skill_to_git(skill_name: str, git_repo_path: Optional[str] = None) -> bool:
    """
    Promote an approved skill to a Git repository.
    
    Args:
        skill_name: Name of skill to promote
        git_repo_path: Path to Git repo (default: current directory)
    
    Returns:
        True if promotion succeeded
    """
    approvals = _load_approvals()
    
    if skill_name not in approvals:
        print(f"✗ Skill '{skill_name}' is not approved. Run 'review' first.")
        return False
    
    skill = get_skill(skill_name)
    if not skill:
        print(f"✗ Skill '{skill_name}' not found")
        return False
    
    # Determine Git repo path
    if git_repo_path is None:
        git_repo_path = Path.cwd()
    else:
        git_repo_path = Path(git_repo_path)
    
    if not (git_repo_path / ".git").exists():
        print(f"✗ Not a Git repository: {git_repo_path}")
        return False
    
    # Copy skill to Git repo
    dest_dir = git_repo_path / "skills"
    dest_dir.mkdir(exist_ok=True)
    
    dest_file = dest_dir / f"{skill.name}.py"
    code = Path(skill.code_path).read_text()
    
    # Add metadata header
    header = f"""# Skill: {skill.name}
# Description: {skill.description or '(none)'}
# Tags: {', '.join(skill.tags or [])}
# Approved: {approvals[skill_name].approved_at}
# Approved by: {approvals[skill_name].approved_by}

"""
    dest_file.write_text(header + code)
    
    # Git add and commit
    try:
        subprocess.run(
            ["git", "add", str(dest_file)],
            cwd=git_repo_path,
            check=True,
            capture_output=True
        )
        
        commit_msg = f"Add approved skill: {skill.name}\n\n{skill.description or ''}"
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=git_repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Extract commit hash
        git_ref = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=git_repo_path,
            check=True,
            capture_output=True,
            text=True
        ).stdout.strip()
        
        # Update approval record
        approvals[skill_name].git_ref = git_ref
        _save_approvals(approvals)
        
        print(f"✓ Promoted '{skill.name}' to Git")
        print(f"  Commit: {git_ref[:8]}")
        print(f"  File: {dest_file.relative_to(git_repo_path)}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Git operation failed: {e.stderr}")
        return False


def main():
    """CLI entrypoint."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m orchestrator.execution.skill_approval review")
        print("  python -m orchestrator.execution.skill_approval promote <skill_name> [repo_path]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "review":
        review_pending_skills()
    elif command == "promote":
        if len(sys.argv) < 3:
            print("Error: Missing skill name")
            sys.exit(1)
        skill_name = sys.argv[2]
        repo_path = sys.argv[3] if len(sys.argv) > 3 else None
        success = promote_skill_to_git(skill_name, repo_path)
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
