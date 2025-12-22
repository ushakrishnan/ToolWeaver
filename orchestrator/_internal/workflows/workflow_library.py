"""
Workflow Library and Pattern Recognition (Phase 8)

Pre-built workflow templates and pattern detection from usage logs.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass
import json
from pathlib import Path

from .workflow import WorkflowTemplate, WorkflowStep
from ..observability.monitoring import ToolCallMetric

logger = logging.getLogger(__name__)


@dataclass
class ToolSequence:
    """A sequence of tool calls"""
    tools: List[str]
    frequency: int
    success_rate: float
    avg_duration_ms: float
    
    def __hash__(self) -> int:
        return hash(tuple(self.tools))
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, ToolSequence) and tuple(self.tools) == tuple(other.tools)


class PatternDetector:
    """
    Analyze tool usage patterns and suggest workflows.
    
    Features:
    - Sequence mining (find common tool chains)
    - Frequency analysis (identify popular patterns)
    - Success rate tracking
    - Automatic workflow generation
    """
    
    def __init__(self, min_frequency: int = 3, min_success_rate: float = 0.7):
        """
        Initialize pattern detector.
        
        Args:
            min_frequency: Minimum occurrences to consider a pattern
            min_success_rate: Minimum success rate to consider a pattern
        """
        self.min_frequency = min_frequency
        self.min_success_rate = min_success_rate
    
    def analyze_logs(
        self,
        logs: List[ToolCallMetric],
        max_sequence_length: int = 5
    ) -> List[ToolSequence]:
        """
        Find common patterns in tool usage logs.
        
        Algorithm:
        1. Group logs by session/request_id
        2. Extract tool sequences (A → B → C)
        3. Count frequency of sequences
        4. Calculate success rate
        5. Return patterns sorted by (frequency * success_rate)
        
        Args:
            logs: List of tool usage logs
            max_sequence_length: Maximum length of sequences to detect
        
        Returns:
            List of ToolSequence objects sorted by relevance
        """
        # Group logs by session
        sessions = self._group_by_session(logs)
        
        # Extract sequences from each session
        sequences = []
        for session_logs in sessions.values():
            session_sequences = self._extract_sequences(session_logs, max_sequence_length)
            sequences.extend(session_sequences)
        
        # Count frequency and calculate metrics
        pattern_stats = self._calculate_pattern_stats(sequences, logs)
        
        # Filter by frequency and success rate
        filtered_patterns = [
            pattern for pattern in pattern_stats
            if pattern.frequency >= self.min_frequency
            and pattern.success_rate >= self.min_success_rate
        ]
        
        # Sort by relevance (frequency * success_rate)
        filtered_patterns.sort(
            key=lambda p: p.frequency * p.success_rate,
            reverse=True
        )
        
        logger.info(f"Found {len(filtered_patterns)} common patterns from {len(logs)} logs")
        
        return filtered_patterns
    
    def _group_by_session(self, logs: List[ToolCallMetric]) -> Dict[str, List[ToolCallMetric]]:
        """Group logs by session/request ID"""
        sessions = defaultdict(list)
        
        for log in logs:
            # Use execution_id if available, otherwise create synthetic session
            session_id = log.execution_id
            if not session_id:
                # Group by timestamp proximity (within 1 minute)
                # Parse ISO timestamp to get epoch seconds
                from datetime import datetime
                ts = datetime.fromisoformat(log.timestamp.replace('Z', '+00:00'))
                session_id = f"auto_{int(ts.timestamp() / 60)}"
            
            sessions[session_id].append(log)
        
        return dict(sessions)
    
    def _extract_sequences(
        self,
        logs: List[ToolCallMetric],
        max_length: int
    ) -> List[Tuple[List[str], bool, float]]:
        """
        Extract tool sequences from session logs.
        
        Returns list of (tools, success, duration) tuples
        """
        # Sort logs by timestamp
        from datetime import datetime
        sorted_logs = sorted(logs, key=lambda x: datetime.fromisoformat(x.timestamp.replace('Z', '+00:00')))
        
        tool_names = [log.tool_name for log in sorted_logs]
        
        sequences = []
        
        # Extract sequences of various lengths
        for length in range(2, min(len(tool_names) + 1, max_length + 1)):
            for i in range(len(tool_names) - length + 1):
                sequence = tool_names[i:i+length]
                
                # Calculate if sequence was successful
                success = all(
                    sorted_logs[j].success
                    for j in range(i, i+length)
                )
                
                # Calculate total duration (latency is in seconds, convert to ms)
                duration = sum(
                    sorted_logs[j].latency * 1000
                    for j in range(i, i+length)
                )
                
                sequences.append((sequence, success, duration))
        
        return sequences
    
    def _calculate_pattern_stats(
        self,
        sequences: List[Tuple[List[str], bool, float]],
        logs: List[ToolCallMetric]
    ) -> List[ToolSequence]:
        """Calculate statistics for each pattern"""
        pattern_data: Dict[Tuple[str, ...], Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'successes': 0,
            'durations': []
        })
        
        for tools, success, duration in sequences:
            key = tuple(tools)
            pattern_data[key]['count'] += 1
            if success:
                pattern_data[key]['successes'] += 1
            pattern_data[key]['durations'].append(duration)
        
        patterns = []
        for tools_tuple, data in pattern_data.items():
            success_rate = data['successes'] / data['count'] if data['count'] > 0 else 0
            avg_duration = sum(data['durations']) / len(data['durations']) if data['durations'] else 0
            
            # Normalize tools to list for ToolSequence
            patterns.append(ToolSequence(
                tools=list(tools_tuple),
                frequency=data['count'],
                success_rate=success_rate,
                avg_duration_ms=avg_duration
            ))
        
        return patterns
    
    def suggest_workflow(
        self,
        tools: List[str],
        patterns: List[ToolSequence]
    ) -> Optional[WorkflowTemplate]:
        """
        Suggest a workflow based on tool names and detected patterns.
        
        Args:
            tools: List of tool names
            patterns: List of detected patterns
        
        Returns:
            WorkflowTemplate if a pattern matches, None otherwise
        """
        # Try to match exact sequence
        for pattern in patterns:
            if pattern.tools == tools:
                return self._create_workflow_from_pattern(pattern)
        
        # Try to match subset
        for pattern in patterns:
            if self._is_subset_sequence(tools, pattern.tools):
                return self._create_workflow_from_pattern(pattern)
        
        return None
    
    def _is_subset_sequence(self, tools: List[str], pattern: List[str]) -> bool:
        """Check if tools is a subset of pattern in order"""
        if len(tools) > len(pattern):
            return False
        
        pattern_idx = 0
        for tool in tools:
            found = False
            while pattern_idx < len(pattern):
                if pattern[pattern_idx] == tool:
                    pattern_idx += 1
                    found = True
                    break
                pattern_idx += 1
            
            if not found:
                return False
        
        return True
    
    def _create_workflow_from_pattern(self, pattern: ToolSequence) -> WorkflowTemplate:
        """Create a workflow template from a detected pattern"""
        steps = []
        
        for i, tool_name in enumerate(pattern.tools):
            step = WorkflowStep(
                step_id=f"step_{i+1}",
                tool_name=tool_name,
                parameters={},
                depends_on=[f"step_{i}"] if i > 0 else []
            )
            steps.append(step)
        
        workflow = WorkflowTemplate(
            name=f"pattern_{'_'.join(pattern.tools[:3])}",
            description=f"Auto-generated from pattern (freq: {pattern.frequency}, success: {pattern.success_rate:.1%})",
            steps=steps,
            metadata={
                'auto_generated': True,
                'frequency': pattern.frequency,
                'success_rate': pattern.success_rate,
                'avg_duration_ms': pattern.avg_duration_ms
            }
        )
        
        return workflow


class WorkflowLibrary:
    """
    Library of workflow templates.
    
    Features:
    - Pre-built workflow templates
    - Custom workflow registration
    - Workflow search and retrieval
    - Persistence to disk
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize workflow library.
        
        Args:
            storage_path: Path to store workflow templates (optional)
        """
        self.workflows: Dict[str, WorkflowTemplate] = {}
        self.storage_path = storage_path
        
        # Load built-in workflows
        self._load_builtin_workflows()
        
        # Load from disk if path provided
        if storage_path and storage_path.exists():
            self._load_from_disk()
    
    def _load_builtin_workflows(self) -> None:
        """Load pre-built workflow templates"""
        
        # GitHub PR workflow
        github_pr = WorkflowTemplate(
            name="github_pr_workflow",
            description="Create GitHub PR and notify team",
            steps=[
                WorkflowStep(
                    step_id="list_issues",
                    tool_name="github_list_issues",
                    parameters={"repo": "{{repo}}"}
                ),
                WorkflowStep(
                    step_id="create_pr",
                    tool_name="github_create_pr",
                    depends_on=["list_issues"],
                    parameters={
                        "repo": "{{repo}}",
                        "title": "{{pr_title}}",
                        "body": "Addresses issue {{list_issues.issues[0].number}}"
                    }
                ),
                WorkflowStep(
                    step_id="notify_slack",
                    tool_name="slack_send_message",
                    depends_on=["create_pr"],
                    parameters={
                        "channel": "{{slack_channel}}",
                        "message": "PR created: {{create_pr.url}}"
                    }
                )
            ],
            metadata={
                'category': 'github',
                'builtin': True
            }
        )
        self.register(github_pr)
        
        # Slack notification chain
        slack_chain = WorkflowTemplate(
            name="slack_notification_chain",
            description="Send notifications to multiple Slack channels",
            steps=[
                WorkflowStep(
                    step_id="notify_dev",
                    tool_name="slack_send_message",
                    parameters={
                        "channel": "#dev",
                        "message": "{{message}}"
                    }
                ),
                WorkflowStep(
                    step_id="notify_ops",
                    tool_name="slack_send_message",
                    parameters={
                        "channel": "#ops",
                        "message": "{{message}}"
                    }
                )
            ],
            metadata={
                'category': 'slack',
                'builtin': True
            }
        )
        self.register(slack_chain)
        
        logger.info(f"Loaded {len(self.workflows)} built-in workflows")
    
    def register(self, workflow: WorkflowTemplate) -> None:
        """
        Register a workflow template in the library.
        
        Args:
            workflow: Workflow template to register
        """
        self.workflows[workflow.name] = workflow
        logger.info(f"Registered workflow: {workflow.name}")
    
    def get(self, name: str) -> Optional[WorkflowTemplate]:
        """
        Retrieve a workflow by name.
        
        Args:
            name: Workflow name
        
        Returns:
            WorkflowTemplate if found, None otherwise
        """
        return self.workflows.get(name)
    
    def list_all(self) -> List[WorkflowTemplate]:
        """Get all workflows in the library"""
        return list(self.workflows.values())
    
    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tool_name: Optional[str] = None
    ) -> List[WorkflowTemplate]:
        """
        Search for workflows.
        
        Args:
            query: Search query (matches name or description)
            category: Filter by category
            tool_name: Filter by tool name used in workflow
        
        Returns:
            List of matching workflows
        """
        results: List[WorkflowTemplate] = list(self.workflows.values())
        
        # Filter by query
        if query:
            query_lower = query.lower()
            results = [
                w for w in results
                if query_lower in w.name.lower()
                or query_lower in w.description.lower()
            ]
        
        # Filter by category
        if category:
            results = [
                w for w in results
                if w.metadata.get('category') == category
            ]
        
        # Filter by tool name
        if tool_name:
            results = [
                w for w in results
                if any(step.tool_name == tool_name for step in w.steps)
            ]
        
        return results
    
    def suggest_for_tools(self, tool_names: List[str]) -> List[WorkflowTemplate]:
        """
        Suggest workflows that use the given tools.
        
        Args:
            tool_names: List of tool names
        
        Returns:
            List of workflows that use any of the tools
        """
        suggestions = []
        
        for workflow in self.workflows.values():
            workflow_tools = {step.tool_name for step in workflow.steps}
            
            # Check if workflow uses any of the requested tools
            if any(tool in workflow_tools for tool in tool_names):
                suggestions.append(workflow)
        
        # Sort by number of matching tools
        suggestions.sort(
            key=lambda w: len(set(step.tool_name for step in w.steps) & set(tool_names)),
            reverse=True
        )
        
        return suggestions
    
    def _load_from_disk(self) -> None:
        """Load workflows from disk storage"""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for workflow_data in data.get('workflows', []):
                workflow = self._deserialize_workflow(workflow_data)
                self.register(workflow)
            
            logger.info(f"Loaded {len(data.get('workflows', []))} workflows from disk")
        except Exception as e:
            logger.error(f"Failed to load workflows from disk: {e}")
    
    def save_to_disk(self) -> None:
        """Save workflows to disk storage"""
        if not self.storage_path:
            return
        
        try:
            # Only save custom workflows (not built-in)
            custom_workflows = [
                w for w in self.workflows.values()
                if not w.metadata.get('builtin', False)
            ]
            
            data = {
                'workflows': [
                    self._serialize_workflow(w)
                    for w in custom_workflows
                ]
            }
            
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(custom_workflows)} custom workflows to disk")
        except Exception as e:
            logger.error(f"Failed to save workflows to disk: {e}")
    
    def _serialize_workflow(self, workflow: WorkflowTemplate) -> Dict[str, Any]:
        """Serialize workflow to JSON-compatible dict"""
        return {
            'name': workflow.name,
            'description': workflow.description,
            'steps': [
                {
                    'step_id': step.step_id,
                    'tool_name': step.tool_name,
                    'parameters': step.parameters,
                    'depends_on': step.depends_on,
                    'condition': step.condition,
                    'retry_count': step.retry_count,
                    'timeout_seconds': step.timeout_seconds
                }
                for step in workflow.steps
            ],
            'metadata': workflow.metadata,
            'parallel_groups': workflow.parallel_groups
        }
    
    def _deserialize_workflow(self, data: Dict[str, Any]) -> WorkflowTemplate:
        """Deserialize workflow from JSON-compatible dict"""
        steps = [
            WorkflowStep(
                step_id=step_data['step_id'],
                tool_name=step_data['tool_name'],
                parameters=step_data['parameters'],
                depends_on=step_data.get('depends_on', []),
                condition=step_data.get('condition'),
                retry_count=step_data.get('retry_count', 0),
                timeout_seconds=step_data.get('timeout_seconds')
            )
            for step_data in data['steps']
        ]
        
        return WorkflowTemplate(
            name=data['name'],
            description=data['description'],
            steps=steps,
            metadata=data.get('metadata', {}),
            parallel_groups=data.get('parallel_groups')
        )


if __name__ == "__main__":
    # Example usage
    library = WorkflowLibrary()
    
    print(f"Available workflows: {len(library.list_all())}")
    
    for workflow in library.list_all():
        print(f"\n{workflow.name}:")
        print(f"  Description: {workflow.description}")
        print(f"  Steps: {len(workflow.steps)}")
        for step in workflow.steps:
            print(f"    - {step.step_id}: {step.tool_name}")
