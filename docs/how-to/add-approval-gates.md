# How to Add Approval Gates

Step-by-step guide to implement human-in-the-loop approval workflows for AI-generated outputs.

## Prerequisites

- Working ToolWeaver project
- Basic understanding of [ToolWeaver orchestration](../get-started/quickstart.md)
- Familiarity with agent workflows

## What You'll Accomplish

By the end of this guide, you'll have:

✅ Draft → Review → Approve → Execute workflow  
✅ Approval interface (CLI, webhook, or API)  
✅ Approval state tracking (pending, approved, rejected)  
✅ Audit trail with timestamps and reviewers  
✅ Retry logic for rejected approvals  

**Estimated time:** 30 minutes

---

## Step 1: Design Approval Workflow

### 1.1 Four-Stage Pattern

```
1. DRAFT    → Agent generates proposal
2. VALIDATE → Agent checks quality
3. APPROVE  → Human reviews and approves
4. EXECUTE  → Apply changes
```

### 1.2 Approval States

```python
from enum import Enum

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
```

---

## Step 2: Create Approval Manager

### 2.1 Approval Request Model

**File:** `approval/models.py`

```python
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class ApprovalRequest:
    """Represents a pending approval request."""
    
    request_id: str
    title: str
    description: str
    proposed_action: dict
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer: str = None
    reviewed_at: datetime = None
    rejection_reason: str = None
    
    def __post_init__(self):
        # Default expiration: 24 hours
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(hours=24)
    
    def is_expired(self) -> bool:
        """Check if approval has expired."""
        return datetime.now() > self.expires_at
    
    def approve(self, reviewer: str):
        """Mark as approved."""
        self.status = ApprovalStatus.APPROVED
        self.reviewer = reviewer
        self.reviewed_at = datetime.now()
    
    def reject(self, reviewer: str, reason: str):
        """Mark as rejected."""
        self.status = ApprovalStatus.REJECTED
        self.reviewer = reviewer
        self.reviewed_at = datetime.now()
        self.rejection_reason = reason
```

### 2.2 Approval Manager

```python
from typing import Dict, Optional
import uuid

class ApprovalManager:
    """Manage approval requests."""
    
    def __init__(self):
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.audit_log = []
    
    def create_request(
        self,
        title: str,
        description: str,
        proposed_action: dict,
        expires_in_hours: int = 24
    ) -> ApprovalRequest:
        """Create new approval request."""
        
        request = ApprovalRequest(
            request_id=str(uuid.uuid4()),
            title=title,
            description=description,
            proposed_action=proposed_action,
            expires_at=datetime.now() + timedelta(hours=expires_in_hours)
        )
        
        self.pending_approvals[request.request_id] = request
        self._log("CREATED", request)
        
        return request
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get approval request by ID."""
        return self.pending_approvals.get(request_id)
    
    def approve(self, request_id: str, reviewer: str) -> ApprovalRequest:
        """Approve request."""
        
        request = self.get_request(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        if request.is_expired():
            request.status = ApprovalStatus.EXPIRED
            raise ValueError(f"Request {request_id} has expired")
        
        request.approve(reviewer)
        self._log("APPROVED", request, reviewer)
        
        return request
    
    def reject(self, request_id: str, reviewer: str, reason: str) -> ApprovalRequest:
        """Reject request."""
        
        request = self.get_request(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        request.reject(reviewer, reason)
        self._log("REJECTED", request, reviewer, reason)
        
        return request
    
    def list_pending(self) -> list[ApprovalRequest]:
        """List all pending requests."""
        return [
            r for r in self.pending_approvals.values()
            if r.status == ApprovalStatus.PENDING and not r.is_expired()
        ]
    
    def _log(self, action: str, request: ApprovalRequest, reviewer: str = None, reason: str = None):
        """Add entry to audit log."""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "request_id": request.request_id,
            "title": request.title,
            "reviewer": reviewer,
            "reason": reason
        })

# Global manager
approval_manager = ApprovalManager()
```

---

## Step 3: Implement Approval Interface

### 3.1 CLI Approval Interface

**File:** `approval/cli_interface.py`

```python
def request_cli_approval(request: ApprovalRequest) -> bool:
    """Request approval via CLI prompt."""
    
    print("\n" + "="*60)
    print("APPROVAL REQUIRED")
    print("="*60)
    print(f"Title: {request.title}")
    print(f"Description: {request.description}")
    print(f"\nProposed Action:")
    
    for key, value in request.proposed_action.items():
        print(f"  {key}: {value}")
    
    print(f"\nExpires: {request.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    while True:
        response = input("\nApprove this action? [y/n/details]: ").strip().lower()
        
        if response == 'y':
            reviewer = input("Your name: ").strip()
            approval_manager.approve(request.request_id, reviewer)
            print("✓ Approved")
            return True
        
        elif response == 'n':
            reviewer = input("Your name: ").strip()
            reason = input("Rejection reason: ").strip()
            approval_manager.reject(request.request_id, reviewer, reason)
            print("✗ Rejected")
            return False
        
        elif response == 'details':
            import json
            print("\nFull proposed action:")
            print(json.dumps(request.proposed_action, indent=2))
        
        else:
            print("Invalid input. Please enter 'y', 'n', or 'details'")
```

### 3.2 Webhook Approval Interface

**File:** `approval/webhook_interface.py`

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/approval/pending", methods=["GET"])
def list_pending_approvals():
    """List all pending approval requests."""
    
    pending = approval_manager.list_pending()
    
    return jsonify({
        "pending_count": len(pending),
        "requests": [
            {
                "request_id": r.request_id,
                "title": r.title,
                "description": r.description,
                "created_at": r.created_at.isoformat(),
                "expires_at": r.expires_at.isoformat()
            }
            for r in pending
        ]
    })

@app.route("/approval/<request_id>", methods=["GET"])
def get_approval_request(request_id: str):
    """Get specific approval request."""
    
    approval_request = approval_manager.get_request(request_id)
    
    if not approval_request:
        return jsonify({"error": "Request not found"}), 404
    
    return jsonify({
        "request_id": approval_request.request_id,
        "title": approval_request.title,
        "description": approval_request.description,
        "proposed_action": approval_request.proposed_action,
        "status": approval_request.status.value,
        "created_at": approval_request.created_at.isoformat(),
        "expires_at": approval_request.expires_at.isoformat()
    })

@app.route("/approval/<request_id>/approve", methods=["POST"])
def approve_request(request_id: str):
    """Approve a request."""
    
    data = request.json
    reviewer = data.get("reviewer", "unknown")
    
    try:
        approval_request = approval_manager.approve(request_id, reviewer)
        
        return jsonify({
            "status": "approved",
            "request_id": approval_request.request_id,
            "reviewer": reviewer,
            "approved_at": approval_request.reviewed_at.isoformat()
        })
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route("/approval/<request_id>/reject", methods=["POST"])
def reject_request(request_id: str):
    """Reject a request."""
    
    data = request.json
    reviewer = data.get("reviewer", "unknown")
    reason = data.get("reason", "No reason provided")
    
    try:
        approval_request = approval_manager.reject(request_id, reviewer, reason)
        
        return jsonify({
            "status": "rejected",
            "request_id": approval_request.request_id,
            "reviewer": reviewer,
            "reason": reason,
            "rejected_at": approval_request.reviewed_at.isoformat()
        })
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# Start webhook server
def start_approval_server(port: int = 5000):
    """Start approval webhook server."""
    print(f"Approval server running on http://localhost:{port}")
    app.run(port=port, debug=False)
```

---

## Step 4: Build Approval Workflow

### 4.1 Four-Stage Workflow

**File:** `workflows/approval_workflow.py`

```python
from orchestrator.a2a.client import A2AClient
from approval.models import ApprovalRequest, ApprovalStatus
from approval.manager import ApprovalManager
from approval.cli_interface import request_cli_approval

class ApprovalWorkflow:
    """Workflow with human approval gate."""
    
    def __init__(self):
        self.client = A2AClient(config_path="agents.yaml")
        self.approval_manager = ApprovalManager()
    
    async def execute_with_approval(self, task: dict):
        """Execute workflow with approval gate."""
        
        # Stage 1: DRAFT - Generate proposal
        print("Stage 1: Generating draft proposal...")
        
        draft = await self.client.delegate(
            agent_id="draft_agent",
            request=task
        )
        
        print(f"✓ Draft generated: {draft.get('title')}")
        
        # Stage 2: VALIDATE - Quality check
        print("\nStage 2: Validating draft...")
        
        validation = await self.client.delegate(
            agent_id="validator_agent",
            request={
                "draft": draft,
                "validation_type": "quality_check"
            }
        )
        
        if not validation.get("is_valid"):
            print(f"✗ Validation failed: {validation.get('issues')}")
            return {"status": "validation_failed", "issues": validation.get("issues")}
        
        print(f"✓ Validation passed (score: {validation.get('score')})")
        
        # Stage 3: APPROVE - Human review
        print("\nStage 3: Requesting human approval...")
        
        approval_request = self.approval_manager.create_request(
            title=draft.get("title", "Proposal"),
            description=f"Validation score: {validation.get('score')}",
            proposed_action=draft,
            expires_in_hours=24
        )
        
        # Request approval (blocking)
        approved = request_cli_approval(approval_request)
        
        if not approved:
            print("\n✗ Workflow cancelled by reviewer")
            return {
                "status": "rejected",
                "reason": approval_request.rejection_reason
            }
        
        # Stage 4: EXECUTE - Apply changes
        print("\nStage 4: Executing approved action...")
        
        result = await self._execute_action(draft)
        
        print("✓ Action executed successfully")
        
        return {
            "status": "completed",
            "draft": draft,
            "validation": validation,
            "approval": {
                "reviewer": approval_request.reviewer,
                "approved_at": approval_request.reviewed_at.isoformat()
            },
            "result": result
        }
    
    async def _execute_action(self, draft: dict):
        """Execute the approved action."""
        
        # Use deterministic MCP tool for execution
        result = await orchestrator.execute_tool(
            "apply_changes",
            {"changes": draft.get("changes")}
        )
        
        return result

# Usage
workflow = ApprovalWorkflow()
result = await workflow.execute_with_approval({
    "type": "policy_update",
    "scope": "company_wide"
})
```

---

## Step 5: Add Audit Trail

### 5.1 Log All Approvals

```python
import json
from pathlib import Path

class AuditLogger:
    """Log approval actions for compliance."""
    
    def __init__(self, log_file: str = "approvals.log"):
        self.log_file = Path(log_file)
    
    def log_approval(self, request: ApprovalRequest):
        """Log approval event."""
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "APPROVAL",
            "request_id": request.request_id,
            "title": request.title,
            "reviewer": request.reviewer,
            "proposed_action": request.proposed_action
        }
        
        self._write_log(entry)
    
    def log_rejection(self, request: ApprovalRequest):
        """Log rejection event."""
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": "REJECTION",
            "request_id": request.request_id,
            "title": request.title,
            "reviewer": request.reviewer,
            "reason": request.rejection_reason
        }
        
        self._write_log(entry)
    
    def _write_log(self, entry: dict):
        """Append entry to log file."""
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_audit_trail(self, request_id: str = None) -> list:
        """Get audit trail for request(s)."""
        
        if not self.log_file.exists():
            return []
        
        entries = []
        
        with open(self.log_file, "r") as f:
            for line in f:
                entry = json.loads(line)
                
                if request_id is None or entry["request_id"] == request_id:
                    entries.append(entry)
        
        return entries

# Usage
audit_logger = AuditLogger()

# Log approval
audit_logger.log_approval(approval_request)

# Get audit trail
trail = audit_logger.get_audit_trail(request_id="abc-123")
for entry in trail:
    print(f"{entry['timestamp']} - {entry['event']} by {entry['reviewer']}")
```

---

## Step 6: Handle Rejection with Retry

### 6.1 Retry on Rejection

```python
async def execute_with_retry_on_rejection(task: dict, max_retries: int = 2):
    """Retry draft generation if rejected."""
    
    workflow = ApprovalWorkflow()
    
    for attempt in range(max_retries + 1):
        print(f"\nAttempt {attempt + 1}/{max_retries + 1}")
        
        result = await workflow.execute_with_approval(task)
        
        if result["status"] == "completed":
            return result
        
        if result["status"] == "rejected":
            if attempt < max_retries:
                print(f"\n⟳ Retrying with feedback: {result['reason']}")
                
                # Add rejection feedback to task
                task["previous_rejection"] = result["reason"]
            else:
                print(f"\n✗ Max retries reached")
                return result
    
    return result

# Usage
result = await execute_with_retry_on_rejection(
    task={"type": "policy_update"},
    max_retries=2
)
```

---

## Step 7: Real-World Example

Complete approval workflow for policy updates.

**File:** `workflows/policy_update_workflow.py`

```python
from workflows.approval_workflow import ApprovalWorkflow
from approval.webhook_interface import start_approval_server
import threading

class PolicyUpdateWorkflow:
    """Policy update workflow with approval gates."""
    
    def __init__(self, use_webhook: bool = False):
        self.workflow = ApprovalWorkflow()
        self.use_webhook = use_webhook
        
        if use_webhook:
            # Start webhook server in background
            thread = threading.Thread(
                target=start_approval_server,
                args=(5000,),
                daemon=True
            )
            thread.start()
    
    async def update_policy(self, policy_name: str, changes: dict):
        """Update policy with approval workflow."""
        
        task = {
            "type": "policy_update",
            "policy_name": policy_name,
            "changes": changes
        }
        
        result = await self.workflow.execute_with_approval(task)
        
        return result

# Usage
workflow = PolicyUpdateWorkflow(use_webhook=True)

result = await workflow.update_policy(
    policy_name="Expense Approval Policy",
    changes={
        "max_amount_without_approval": 5000,
        "approval_chain": ["manager", "finance", "cfo"]
    }
)

print(f"Status: {result['status']}")
```

---

## Verification

Test your approval workflow:

```python
async def verify_approval_workflow():
    """Verify approval workflow is working."""
    
    print("Testing approval workflow...")
    
    # Test 1: Create approval request
    manager = ApprovalManager()
    request = manager.create_request(
        title="Test Approval",
        description="Test request",
        proposed_action={"action": "test"}
    )
    assert request.status == ApprovalStatus.PENDING
    print("✓ Approval request creation working")
    
    # Test 2: Approve request
    manager.approve(request.request_id, "test_reviewer")
    assert request.status == ApprovalStatus.APPROVED
    assert request.reviewer == "test_reviewer"
    print("✓ Approval working")
    
    # Test 3: Reject request
    request2 = manager.create_request(
        title="Test Rejection",
        description="Test",
        proposed_action={}
    )
    manager.reject(request2.request_id, "test_reviewer", "Not ready")
    assert request2.status == ApprovalStatus.REJECTED
    print("✓ Rejection working")
    
    # Test 4: Expiration
    request3 = manager.create_request(
        title="Test Expiration",
        description="Test",
        proposed_action={},
        expires_in_hours=0  # Expire immediately
    )
    assert request3.is_expired()
    print("✓ Expiration working")
    
    print("\n✅ All checks passed!")

await verify_approval_workflow()
```

---

## Common Issues

### Issue 1: Approval Request Hangs

**Symptom:** CLI prompt blocks indefinitely

**Solution:** Add timeout

```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Approval timeout")

# Set timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(300)  # 5 minutes

try:
    approved = request_cli_approval(approval_request)
except TimeoutError:
    print("✗ Approval timeout, rejecting")
    approved = False
finally:
    signal.alarm(0)
```

### Issue 2: Lost Approval Requests

**Symptom:** Pending approvals not persisted on restart

**Solution:** Store in database or file

```python
import pickle

def save_pending_approvals():
    with open("pending_approvals.pkl", "wb") as f:
        pickle.dump(approval_manager.pending_approvals, f)

def load_pending_approvals():
    try:
        with open("pending_approvals.pkl", "rb") as f:
            approval_manager.pending_approvals = pickle.load(f)
    except FileNotFoundError:
        pass
```

---

## Next Steps

- **Sample:** [20-approval-workflow](https://github.com/ushakrishnan/ToolWeaver/tree/main/samples/20-approval-workflow) - Complete example
- **Tutorial:** [Agent Delegation](../tutorials/agent-delegation.md) - Learn agent workflows
- **Deep Dive:** [Control Flow Patterns](../reference/deep-dives/control-flow-patterns.md) - Advanced patterns

## Related Guides

- [Configure A2A Agents](configure-a2a-agents.md) - Set up draft and validation agents
- [Monitor Performance](monitor-performance.md) - Track approval latency
- [Implement Retry Logic](implement-retry-logic.md) - Retry rejected drafts
