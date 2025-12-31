"""
ToolWeaver Phase 5: Advanced Analytics Backend.

Provides comprehensive metrics aggregation, usage trends, leaderboards,
recommendations, and health scoring for skills.

Features:
- Real-time metrics collection and aggregation
- Trend analysis and forecasting
- Leaderboard computation and ranking
- Smart recommendation engine
- Health scoring system
- Grafana dashboard integration
"""

import logging
import os
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from .sqlite_schema import SQLiteSchema

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Metric types for leaderboards and trends."""

    USAGE_COUNT = "usage_count"
    SUCCESS_RATE = "success_rate"
    RATING = "rating"
    ADOPTION = "adoption"
    PERFORMANCE = "performance"


class RecommendationType(str, Enum):
    """Types of recommendations."""

    COLLABORATIVE = "collaborative"  # Similar to what others use
    CONTENT_BASED = "content_based"  # Similar features
    TRENDING = "trending"  # Popular right now
    PERSONALIZED = "personalized"  # Based on user history
    NEW_SKILL = "new_skill"  # Recently added


@dataclass
class SkillUsage:
    """Skill usage record."""

    skill_id: str
    user_id: str
    org_id: str | None = None
    execution_count: int = 1
    success_count: int = 1
    failure_count: int = 0
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SkillMetrics:
    """Aggregated skill metrics."""

    skill_id: str
    rating_avg: float = 0.0
    rating_count: int = 0
    install_count: int = 0
    download_count: int = 0
    health_score: float = 100.0
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0
    last_used: str | None = None
    deprecation_status: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SkillRecommendation:
    """Skill recommendation."""

    user_id: str
    recommended_skill_id: str
    recommendation_type: RecommendationType
    score: float
    reason: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data["recommendation_type"] = self.recommendation_type.value
        return data


class SkillAnalytics:
    """Main analytics backend for Phase 5."""

    def __init__(self, db_path: str | None = None):
        """Initialize analytics backend.

        Args:
            db_path: Path to SQLite database. Uses default if not provided.
        """
        self.schema = SQLiteSchema(db_path)
        self.db_path = self.schema.db_path

        # Initialize database on first use
        self.schema.initialize()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return self.schema.connect()

    # ========================================================================
    # Usage Tracking Methods
    # ========================================================================

    def record_skill_usage(
        self,
        skill_id: str,
        user_id: str,
        org_id: str | None = None,
        success: bool = True,
        latency_ms: float = 0.0,
    ) -> bool:
        """Record skill execution usage.

        Args:
            skill_id: ID of the skill executed.
            user_id: ID of user executing skill.
            org_id: Optional organization ID.
            success: Whether execution was successful.
            latency_ms: Execution latency in milliseconds.

        Returns:
            True if record was saved successfully.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            success_count = 1 if success else 0
            failure_count = 0 if success else 1

            cursor.execute(
                """
                INSERT INTO skill_usage
                (skill_id, user_id, org_id, execution_count, success_count, 
                 failure_count, avg_latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (skill_id, user_id, org_id, 1, success_count, failure_count, latency_ms),
            )

            conn.commit()
            conn.close()
            logger.debug(f"Recorded usage: {skill_id} by {user_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error recording usage: {e}")
            return False

    def get_skill_usage(
        self, skill_id: str, days: int = 30, org_id: str | None = None
    ) -> dict[str, Any]:
        """Get usage statistics for a skill.

        Args:
            skill_id: ID of skill to get usage for.
            days: Number of days of history to retrieve.
            org_id: Optional organization ID to filter by.

        Returns:
            Dictionary with usage statistics.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            query = """
                SELECT
                    COUNT(DISTINCT user_id) as unique_users,
                    SUM(execution_count) as total_executions,
                    SUM(success_count) as successful_executions,
                    SUM(failure_count) as failed_executions,
                    AVG(avg_latency_ms) as avg_latency,
                    MAX(avg_latency_ms) as max_latency,
                    MIN(avg_latency_ms) as min_latency,
                    MAX(timestamp) as last_used
                FROM skill_usage
                WHERE skill_id = ? AND timestamp >= ?
            """
            params = [skill_id, cutoff_date]

            if org_id:
                query += " AND org_id = ?"
                params.append(org_id)

            cursor.execute(query, params)
            row = cursor.fetchone()
            conn.close()

            if row:
                result = {
                    "skill_id": skill_id,
                    "unique_users": row[0] or 0,
                    "total_executions": row[1] or 0,
                    "successful_executions": row[2] or 0,
                    "failed_executions": row[3] or 0,
                    "avg_latency_ms": row[4] or 0.0,
                    "max_latency_ms": row[5] or 0.0,
                    "min_latency_ms": row[6] or 0.0,
                    "last_used": row[7],
                    "success_rate": (
                        (row[2] or 0) / (row[1] or 1) if row[1] else 0
                    ),
                    "period_days": days,
                }
                return result
            return {}

        except sqlite3.Error as e:
            logger.error(f"Error getting usage: {e}")
            return {}

    # ========================================================================
    # Metrics and Ratings Methods
    # ========================================================================

    def rate_skill(
        self, skill_id: str, rating: int, org_id: str | None = None
    ) -> bool:
        """Record a skill rating.

        Args:
            skill_id: ID of skill being rated.
            rating: Rating value (1-5).
            org_id: Optional organization ID.

        Returns:
            True if rating was saved.
        """
        if not 1 <= rating <= 5:
            logger.warning(f"Invalid rating {rating}, must be 1-5")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if skill exists in metrics table
            cursor.execute(
                "SELECT id FROM skill_metrics WHERE skill_id = ?", (skill_id,)
            )
            exists = cursor.fetchone()

            if exists:
                # Update existing record
                cursor.execute(
                    f"""
                    UPDATE skill_metrics
                    SET rating_{rating}_count = rating_{rating}_count + 1,
                        rating_count = rating_count + 1,
                        last_rated = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE skill_id = ?
                    """,
                    (skill_id,),
                )
            else:
                # Create new record
                values = {
                    "skill_id": skill_id,
                    "org_id": org_id,
                    "rating_count": 1,
                    f"rating_{rating}_count": 1,
                    "last_rated": datetime.now().isoformat(),
                }
                placeholders = ", ".join(f":{k}" for k in values)
                columns = ", ".join(values.keys())
                cursor.execute(
                    f"INSERT INTO skill_metrics ({columns}) VALUES ({placeholders})",
                    values,
                )

            # Update average rating
            cursor.execute(
                """
                UPDATE skill_metrics
                SET rating_avg = (
                    (rating_1_count * 1 +
                     rating_2_count * 2 +
                     rating_3_count * 3 +
                     rating_4_count * 4 +
                     rating_5_count * 5) / 
                    CAST(rating_count AS FLOAT)
                )
                WHERE skill_id = ?
                """,
                (skill_id,),
            )

            conn.commit()
            conn.close()
            logger.debug(f"Recorded rating {rating} for {skill_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Error recording rating: {e}")
            return False

    def get_skill_metrics(self, skill_id: str) -> SkillMetrics | None:
        """Get comprehensive metrics for a skill.

        Args:
            skill_id: ID of skill to get metrics for.

        Returns:
            SkillMetrics object or None if not found.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    skill_id,
                    rating_avg,
                    rating_count,
                    install_count,
                    download_count,
                    health_score,
                    last_used,
                    deprecation_status
                FROM skill_metrics
                WHERE skill_id = ?
                """,
                (skill_id,),
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return SkillMetrics(
                    skill_id=row[0],
                    rating_avg=row[1] or 0.0,
                    rating_count=row[2] or 0,
                    install_count=row[3] or 0,
                    download_count=row[4] or 0,
                    health_score=row[5] or 100.0,
                    last_used=row[6],
                    deprecation_status=row[7],
                )
            return None

        except sqlite3.Error as e:
            logger.error(f"Error getting metrics: {e}")
            return None

    # ========================================================================
    # Leaderboard Methods
    # ========================================================================

    def compute_leaderboard(
        self,
        metric_type: MetricType = MetricType.USAGE_COUNT,
        period: str = "daily",
        limit: int = 10,
        org_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Compute leaderboard rankings.

        Args:
            metric_type: Type of metric for ranking.
            period: Time period ('daily', 'weekly', 'monthly').
            limit: Number of top skills to return.
            org_id: Optional organization filter.

        Returns:
            List of ranked skills.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if metric_type == MetricType.USAGE_COUNT:
                query = """
                    SELECT
                        skill_id,
                        SUM(execution_count) as score,
                        COUNT(DISTINCT user_id) as unique_users
                    FROM skill_usage
                    GROUP BY skill_id
                    ORDER BY score DESC
                    LIMIT ?
                """
                params = [limit]

            elif metric_type == MetricType.SUCCESS_RATE:
                query = """
                    SELECT
                        skill_id,
                        (SUM(success_count) * 100.0 / SUM(execution_count)) as score,
                        SUM(execution_count) as executions
                    FROM skill_usage
                    WHERE execution_count > 0
                    GROUP BY skill_id
                    ORDER BY score DESC
                    LIMIT ?
                """
                params = [limit]

            elif metric_type == MetricType.RATING:
                query = """
                    SELECT
                        skill_id,
                        rating_avg as score,
                        rating_count as count
                    FROM skill_metrics
                    WHERE rating_count > 0
                    ORDER BY score DESC, rating_count DESC
                    LIMIT ?
                """
                params = [limit]

            else:
                logger.warning(f"Unknown metric type: {metric_type}")
                return []

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            leaderboard = []
            for rank, row in enumerate(rows, 1):
                leaderboard.append(
                    {
                        "rank": rank,
                        "skill_id": row[0],
                        "score": row[1],
                        "metric_type": metric_type.value,
                        "period": period,
                    }
                )

            return leaderboard

        except sqlite3.Error as e:
            logger.error(f"Error computing leaderboard: {e}")
            return []

    def get_top_skills(
        self,
        limit: int = 10,
        org_id: str | None = None,
        period_days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get top skills by usage.

        Args:
            limit: Number of top skills to return.
            org_id: Optional organization filter.
            period_days: Number of days to consider.

        Returns:
            List of top skills with metrics.
        """
        leaderboard = self.compute_leaderboard(
            MetricType.USAGE_COUNT, limit=limit, org_id=org_id
        )
        return leaderboard

    # ========================================================================
    # Recommendation Methods
    # ========================================================================

    def recommend_skills(
        self,
        user_id: str,
        limit: int = 5,
        org_id: str | None = None,
    ) -> list[SkillRecommendation]:
        """Generate recommendations for a user.

        Args:
            user_id: ID of user to generate recommendations for.
            limit: Maximum number of recommendations.
            org_id: Optional organization ID.

        Returns:
            List of recommended skills.
        """
        recommendations = []

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get user's previously used skills
            cursor.execute(
                """
                SELECT DISTINCT skill_id
                FROM skill_usage
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 10
                """,
                (user_id,),
            )
            user_skills = [row[0] for row in cursor.fetchall()]

            # If user has history, use collaborative filtering
            if user_skills:
                # Find users with similar skill usage
                placeholders = ",".join("?" * len(user_skills))
                cursor.execute(
                    f"""
                    SELECT DISTINCT su.skill_id
                    FROM skill_usage su
                    WHERE skill_id IN ({placeholders})
                    AND user_id != ?
                    AND skill_id NOT IN (
                        SELECT skill_id FROM skill_usage WHERE user_id = ?
                    )
                    ORDER BY RANDOM()
                    LIMIT ?
                    """,
                    user_skills + [user_id, user_id, limit],
                )
                similar_skills = [row[0] for row in cursor.fetchall()]

                for i, skill_id in enumerate(similar_skills):
                    # Get metrics for recommendation score
                    metrics = self.get_skill_metrics(skill_id)
                    score = metrics.rating_avg if metrics else 0.0
                    score += 50  # Base score for collaborative match

                    rec = SkillRecommendation(
                        user_id=user_id,
                        recommended_skill_id=skill_id,
                        recommendation_type=RecommendationType.COLLABORATIVE,
                        score=min(100.0, score),
                        reason=f"Used by similar users, rated {score:.1f}/100",
                    )
                    recommendations.append(rec)

            # Add trending skills if needed
            if len(recommendations) < limit:
                trending = self.compute_leaderboard(
                    MetricType.USAGE_COUNT, limit=limit - len(recommendations)
                )
                for item in trending:
                    if item["skill_id"] not in user_skills:
                        rec = SkillRecommendation(
                            user_id=user_id,
                            recommended_skill_id=item["skill_id"],
                            recommendation_type=RecommendationType.TRENDING,
                            score=75.0,
                            reason="Currently trending",
                        )
                        recommendations.append(rec)

            conn.close()

            # Log recommendations
            for rec in recommendations:
                self._log_recommendation(rec, org_id)

            return recommendations[:limit]

        except sqlite3.Error as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    def _log_recommendation(
        self, recommendation: SkillRecommendation, org_id: str | None = None
    ) -> None:
        """Log a recommendation to the database.

        Args:
            recommendation: Recommendation to log.
            org_id: Optional organization ID.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO recommendation_log
                (user_id, org_id, recommended_skill_id, recommendation_type, score)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    recommendation.user_id,
                    org_id,
                    recommendation.recommended_skill_id,
                    recommendation.recommendation_type.value,
                    recommendation.score,
                ),
            )

            conn.commit()
            conn.close()

        except sqlite3.Error as e:
            logger.error(f"Error logging recommendation: {e}")

    # ========================================================================
    # Health Scoring Methods
    # ========================================================================

    def compute_health_score(self, skill_id: str) -> float:
        """Compute health score for a skill (0-100).

        Score factors:
        - Success rate (40%)
        - Rating (30%)
        - Recent usage (20%)
        - Latency (10%)

        Args:
            skill_id: ID of skill to score.

        Returns:
            Health score (0-100).
        """
        try:
            usage = self.get_skill_usage(skill_id, days=30)
            metrics = self.get_skill_metrics(skill_id)

            if not usage or not metrics:
                return 50.0  # Default score

            # Calculate components
            success_score = usage.get("success_rate", 0) * 100  # 0-100
            rating_score = metrics.rating_avg * 20 if metrics.rating_count > 0 else 50  # 0-100
            usage_score = min(100, usage.get("total_executions", 0) * 10)  # Recency
            latency_score = max(0, 100 - (usage.get("avg_latency_ms", 0) / 10))  # Lower is better

            # Weighted score
            health = (
                success_score * 0.40
                + rating_score * 0.30
                + usage_score * 0.20
                + latency_score * 0.10
            )

            return float(max(0, min(100, health)))

        except Exception as e:
            logger.error(f"Error computing health score: {e}")
            return 50.0

    def update_health_scores(self) -> int:
        """Update health scores for all skills.

        Returns:
            Number of scores updated.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get all skills
            cursor.execute("SELECT DISTINCT skill_id FROM skill_metrics")
            skills = [row[0] for row in cursor.fetchall()]

            updated = 0
            for skill_id in skills:
                health_score = self.compute_health_score(skill_id)
                cursor.execute(
                    """
                    UPDATE skill_metrics
                    SET health_score = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE skill_id = ?
                    """,
                    (health_score, skill_id),
                )
                updated += 1

            conn.commit()
            conn.close()
            logger.info(f"Updated health scores for {updated} skills")
            return updated

        except sqlite3.Error as e:
            logger.error(f"Error updating health scores: {e}")
            return 0

    def update_health_score(self, skill_id: str, score: float) -> None:
        """Adapter method for interface compatibility with OTLP and Prometheus backends.
        
        Sets health score for a specific skill (SQLite-specific).
        
        Args:
            skill_id: The skill ID
            score: Health score (0-100)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE skill_metrics
                SET health_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE skill_id = ?
                """,
                (score, skill_id),
            )
            conn.commit()
            conn.close()
            logger.info(f"Updated health score for {skill_id}: {score}/100")
        except sqlite3.Error as e:
            logger.error(f"Error updating health score: {e}")

    # ========================================================================
    # Trend Analysis Methods
    # ========================================================================

    def get_usage_trends(
        self,
        skill_id: str,
        period_days: int = 30,
        org_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get usage trends for a skill.

        Args:
            skill_id: ID of skill to get trends for.
            period_days: Number of days of history.
            org_id: Optional organization filter.

        Returns:
            List of daily usage data points.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=period_days)).isoformat()

            query = """
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as usage_count,
                    COUNT(DISTINCT user_id) as unique_users,
                    SUM(execution_count) as executions,
                    AVG(avg_latency_ms) as avg_latency
                FROM skill_usage
                WHERE skill_id = ? AND timestamp >= ?
            """
            params = [skill_id, cutoff_date]

            if org_id:
                query += " AND org_id = ?"
                params.append(org_id)

            query += " GROUP BY DATE(timestamp) ORDER BY date DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            trends = [
                {
                    "date": row[0],
                    "usage_count": row[1],
                    "unique_users": row[2],
                    "executions": row[3],
                    "avg_latency_ms": row[4],
                }
                for row in rows
            ]

            return trends

        except sqlite3.Error as e:
            logger.error(f"Error getting trends: {e}")
            return []

    # ========================================================================
    # Adoption Tracking Methods
    # ========================================================================

    def get_adoption_metrics(
        self,
        skill_id: str,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        """Get adoption metrics for a skill.

        Args:
            skill_id: ID of skill.
            org_id: Optional organization ID.

        Returns:
            Dictionary with adoption metrics.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM adoption_metrics WHERE skill_id = ?"
            params = [skill_id]

            if org_id:
                query += " AND org_id = ?"
                params.append(org_id)

            cursor.execute(query, params)
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "skill_id": row[1],
                    "user_count": row[3],
                    "adoption_percentage": row[4],
                    "growth_rate_daily": row[5],
                    "growth_rate_weekly": row[6],
                    "retention_rate": row[7],
                }
            return {}

        except sqlite3.Error as e:
            logger.error(f"Error getting adoption metrics: {e}")
            return {}

    # ========================================================================
    # Database Maintenance Methods
    # ========================================================================

    def cleanup_old_data(self, retention_days: int) -> int:
        """Clean up data older than retention period.

        Args:
            retention_days: Days to retain.

        Returns:
            Number of rows deleted.
        """
        return self.schema.cleanup_old_data(retention_days)

    def get_db_stats(self) -> dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with stats.
        """
        return self.schema.get_db_stats()

    def health_check(self) -> bool:
        """Check database health.

        Returns:
            True if healthy.
        """
        return self.schema.health_check()

    def get_config_summary(self) -> dict[str, Any]:
        """Get configuration summary for debugging.
        
        Returns:
            Dictionary with backend info and config.
        """
        return {
            "backend": "sqlite",
            "db_path": str(self.db_path),
            "exists": os.path.exists(self.db_path),
            "size_bytes": os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
            "healthy": self.health_check(),
        }
