"""
Skill Metrics and Analytics

Track usage patterns, success rates, and user feedback for skills.

Metrics tracked:
- Usage count (how often executed)
- Success rate (% executions without errors)
- Average latency (execution time)
- User ratings (1-5 stars)
- Last used timestamp
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Literal
import logging

logger = logging.getLogger(__name__)

_ROOT = Path.home() / ".toolweaver" / "skills"
_METRICS_FILE = _ROOT / "metrics.json"


@dataclass
class SkillMetrics:
    """Aggregated metrics for a skill."""
    skill_name: str
    usage_count: int = 0
    success_count: int = 0
    total_latency_ms: float = 0.0
    ratings: List[int] = field(default_factory=list)  # User ratings (1-5)
    last_used: Optional[str] = None  # ISO timestamp
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage (0-100)."""
        if self.usage_count == 0:
            return 0.0
        return (self.success_count / self.usage_count) * 100
    
    @property
    def avg_latency_ms(self) -> float:
        """Average execution latency in milliseconds."""
        if self.success_count == 0:
            return 0.0
        return self.total_latency_ms / self.success_count
    
    @property
    def avg_rating(self) -> float:
        """Average user rating (1-5 scale)."""
        if not self.ratings:
            return 0.0
        return sum(self.ratings) / len(self.ratings)


def _load_metrics() -> Dict[str, SkillMetrics]:
    """Load metrics from disk."""
    if not _METRICS_FILE.exists():
        return {}
    
    try:
        data = json.loads(_METRICS_FILE.read_text())
        metrics = {}
        for name, m in data.items():
            # Convert dict to SkillMetrics
            metrics[name] = SkillMetrics(**m)
        return metrics
    except Exception as e:
        logger.error(f"Failed to load metrics: {e}")
        return {}


def _save_metrics(metrics: Dict[str, SkillMetrics]) -> None:
    """Save metrics to disk."""
    try:
        data = {name: asdict(m) for name, m in metrics.items()}
        _METRICS_FILE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")


def record_skill_execution(
    skill_name: str,
    success: bool,
    latency_ms: float
) -> None:
    """
    Record a skill execution event.
    
    Args:
        skill_name: Name of executed skill
        success: Whether execution succeeded
        latency_ms: Execution time in milliseconds
    """
    metrics = _load_metrics()
    
    if skill_name not in metrics:
        metrics[skill_name] = SkillMetrics(
            skill_name=skill_name,
            created_at=datetime.now().isoformat(),
            ratings=[]
        )
    
    m = metrics[skill_name]
    m.usage_count += 1
    m.last_used = datetime.now().isoformat()
    
    if success:
        m.success_count += 1
        m.total_latency_ms += latency_ms
    
    _save_metrics(metrics)


def rate_skill(skill_name: str, rating: int) -> None:
    """
    Add a user rating for a skill.
    
    Args:
        skill_name: Name of skill to rate
        rating: Rating (1-5 stars)
    """
    if not (1 <= rating <= 5):
        raise ValueError("Rating must be between 1 and 5")
    
    metrics = _load_metrics()
    
    if skill_name not in metrics:
        metrics[skill_name] = SkillMetrics(
            skill_name=skill_name,
            created_at=datetime.now().isoformat(),
            ratings=[]
        )
    
    if metrics[skill_name].ratings is None:
        metrics[skill_name].ratings = []
    
    metrics[skill_name].ratings.append(rating)
    _save_metrics(metrics)


def get_skill_metrics(skill_name: str) -> Optional[SkillMetrics]:
    """
    Get metrics for a specific skill.
    
    Args:
        skill_name: Name of skill
    
    Returns:
        SkillMetrics or None if no data
    """
    metrics = _load_metrics()
    return metrics.get(skill_name)


def get_all_metrics() -> Dict[str, SkillMetrics]:
    """
    Get metrics for all skills.
    
    Returns:
        Dict mapping skill names to their metrics
    """
    return _load_metrics()


def get_top_skills(metric: str = "usage", limit: int = 10) -> List[SkillMetrics]:
    """
    Get top-performing skills by a metric.
    
    Args:
        metric: One of "usage", "success_rate", "rating", "latency"
        limit: Max number of skills to return
    
    Returns:
        List of SkillMetrics sorted by the specified metric
    """
    metrics = _load_metrics()
    skills = list(metrics.values())
    
    if metric == "usage":
        skills.sort(key=lambda s: s.usage_count, reverse=True)
    elif metric == "success_rate":
        skills.sort(key=lambda s: s.success_rate, reverse=True)
    elif metric == "rating":
        skills.sort(key=lambda s: s.avg_rating, reverse=True)
    elif metric == "latency":
        # Lower is better for latency
        skills.sort(key=lambda s: s.avg_latency_ms if s.success_count > 0 else float('inf'))
    else:
        raise ValueError(f"Unknown metric: {metric}")
    
    return skills[:limit]


def print_metrics_report(skill_name: Optional[str] = None) -> None:
    """
    Print a formatted metrics report.
    
    Args:
        skill_name: If provided, show metrics for this skill only.
                   Otherwise show summary for all skills.
    """
    if skill_name:
        # Single skill report
        m = get_skill_metrics(skill_name)
        if not m:
            print(f"No metrics for skill: {skill_name}")
            return
        
        print(f"\n{'='*60}")
        print(f"Metrics for: {skill_name}")
        print(f"{'='*60}")
        print(f"Usage Count:    {m.usage_count}")
        print(f"Success Rate:   {m.success_rate:.1f}%")
        print(f"Avg Latency:    {m.avg_latency_ms:.1f} ms")
        print(f"Avg Rating:     {m.avg_rating:.2f}/5.0 ({len(m.ratings or [])} ratings)")
        print(f"Last Used:      {m.last_used or 'Never'}")
        print(f"Created:        {m.created_at or 'Unknown'}")
    
    else:
        # Summary report
        all_metrics = get_all_metrics()
        
        if not all_metrics:
            print("No metrics available")
            return
        
        print(f"\n{'='*80}")
        print(f"Skill Library Metrics Summary ({len(all_metrics)} skills)")
        print(f"{'='*80}\n")
        
        # Top by usage
        print("📊 Most Used Skills:")
        for i, m in enumerate(get_top_skills("usage", limit=5), 1):
            print(f"  {i}. {m.skill_name:<30} {m.usage_count:>4} uses")
        
        # Top by rating
        print("\n⭐ Highest Rated Skills:")
        rated = [m for m in get_top_skills("rating", limit=5) if m.ratings]
        if rated:
            for i, m in enumerate(rated, 1):
                print(f"  {i}. {m.skill_name:<30} {m.avg_rating:.2f}/5.0 ({len(m.ratings)} ratings)")
        else:
            print("  (no ratings yet)")
        
        # Fastest skills
        print("\n⚡ Fastest Skills (avg latency):")
        fast = [m for m in get_top_skills("latency", limit=5) if m.success_count > 0]
        if fast:
            for i, m in enumerate(fast, 1):
                print(f"  {i}. {m.skill_name:<30} {m.avg_latency_ms:>6.1f} ms")
        else:
            print("  (no execution data)")
        
        # Success rates
        print("\n✅ Most Reliable Skills (success rate):")
        reliable = [m for m in get_top_skills("success_rate", limit=5) if m.usage_count > 0]
        if reliable:
            for i, m in enumerate(reliable, 1):
                print(f"  {i}. {m.skill_name:<30} {m.success_rate:>5.1f}%")
        else:
            print("  (no execution data)")
        
        print()


class SkillExecutionTimer:
    """Context manager for timing skill executions."""
    
    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        self.start_time = 0.0
        self.success = False
    
    def __enter__(self) -> "SkillExecutionTimer":
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        self.success = (exc_type is None)
        record_skill_execution(self.skill_name, self.success, elapsed_ms)
        return False  # Don't suppress exceptions
