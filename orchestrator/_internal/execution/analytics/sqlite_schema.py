"""
SQLite schema initialization for ToolWeaver Phase 5 Analytics.

Creates and maintains the database schema for storing metrics, usage trends,
leaderboards, and recommendation logs.

Auto-creates tables on first run with proper indexes and constraints.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class SQLiteSchema:
    """Manages SQLite database schema for analytics."""

    # SQL Schema Definitions
    SCHEMA_VERSION = 1

    TABLES = {
        "skill_usage": """
            CREATE TABLE IF NOT EXISTS skill_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                org_id TEXT,
                execution_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                avg_latency_ms REAL DEFAULT 0.0,
                min_latency_ms REAL DEFAULT 0.0,
                max_latency_ms REAL DEFAULT 0.0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "skill_metrics": """
            CREATE TABLE IF NOT EXISTS skill_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT UNIQUE NOT NULL,
                org_id TEXT,
                rating_avg REAL DEFAULT 0.0,
                rating_count INTEGER DEFAULT 0,
                rating_1_count INTEGER DEFAULT 0,
                rating_2_count INTEGER DEFAULT 0,
                rating_3_count INTEGER DEFAULT 0,
                rating_4_count INTEGER DEFAULT 0,
                rating_5_count INTEGER DEFAULT 0,
                install_count INTEGER DEFAULT 0,
                download_count INTEGER DEFAULT 0,
                last_used DATETIME,
                last_rated DATETIME,
                health_score REAL DEFAULT 100.0,
                deprecation_status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "leaderboard_cache": """
            CREATE TABLE IF NOT EXISTS leaderboard_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                org_id TEXT,
                rank INTEGER,
                score REAL,
                metric_type TEXT NOT NULL,
                period TEXT DEFAULT 'daily',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(skill_id, org_id, metric_type, period)
            )
        """,
        "recommendation_log": """
            CREATE TABLE IF NOT EXISTS recommendation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                org_id TEXT,
                recommended_skill_id TEXT NOT NULL,
                recommendation_type TEXT,
                score REAL,
                clicked BOOLEAN DEFAULT 0,
                installed BOOLEAN DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME
            )
        """,
        "adoption_metrics": """
            CREATE TABLE IF NOT EXISTS adoption_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id TEXT NOT NULL,
                skill_id TEXT NOT NULL,
                user_count INTEGER DEFAULT 0,
                adoption_percentage REAL DEFAULT 0.0,
                growth_rate_daily REAL DEFAULT 0.0,
                growth_rate_weekly REAL DEFAULT 0.0,
                retention_rate REAL DEFAULT 0.0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(org_id, skill_id)
            )
        """,
        "health_scores": """
            CREATE TABLE IF NOT EXISTS health_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                org_id TEXT,
                overall_score REAL,
                functionality_score REAL,
                reliability_score REAL,
                performance_score REAL,
                maintenance_score REAL,
                security_score REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "trend_data": """
            CREATE TABLE IF NOT EXISTS trend_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                org_id TEXT,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                period TEXT DEFAULT 'daily'
            )
        """,
        "version": """
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY,
                version INTEGER NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
    }

    INDEXES = {
        "skill_usage_indexes": [
            "CREATE INDEX IF NOT EXISTS idx_skill_usage_skill_id ON skill_usage(skill_id)",
            "CREATE INDEX IF NOT EXISTS idx_skill_usage_user_id ON skill_usage(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_skill_usage_org_id ON skill_usage(org_id)",
            "CREATE INDEX IF NOT EXISTS idx_skill_usage_timestamp ON skill_usage(timestamp DESC)",
        ],
        "skill_metrics_indexes": [
            "CREATE INDEX IF NOT EXISTS idx_skill_metrics_skill_id ON skill_metrics(skill_id)",
            "CREATE INDEX IF NOT EXISTS idx_skill_metrics_org_id ON skill_metrics(org_id)",
            "CREATE INDEX IF NOT EXISTS idx_skill_metrics_rating_avg ON skill_metrics(rating_avg DESC)",
            "CREATE INDEX IF NOT EXISTS idx_skill_metrics_health_score ON skill_metrics(health_score)",
        ],
        "leaderboard_indexes": [
            "CREATE INDEX IF NOT EXISTS idx_leaderboard_metric ON leaderboard_cache(metric_type, period)",
            "CREATE INDEX IF NOT EXISTS idx_leaderboard_org_metric ON leaderboard_cache(org_id, metric_type)",
            "CREATE INDEX IF NOT EXISTS idx_leaderboard_rank ON leaderboard_cache(rank)",
        ],
        "recommendation_indexes": [
            "CREATE INDEX IF NOT EXISTS idx_recommendation_user ON recommendation_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_recommendation_skill ON recommendation_log(recommended_skill_id)",
            "CREATE INDEX IF NOT EXISTS idx_recommendation_timestamp ON recommendation_log(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_recommendation_type ON recommendation_log(recommendation_type)",
        ],
        "adoption_indexes": [
            "CREATE INDEX IF NOT EXISTS idx_adoption_org ON adoption_metrics(org_id)",
            "CREATE INDEX IF NOT EXISTS idx_adoption_skill ON adoption_metrics(skill_id)",
            "CREATE INDEX IF NOT EXISTS idx_adoption_growth ON adoption_metrics(growth_rate_daily DESC)",
        ],
        "health_indexes": [
            "CREATE INDEX IF NOT EXISTS idx_health_skill ON health_scores(skill_id)",
            "CREATE INDEX IF NOT EXISTS idx_health_overall ON health_scores(overall_score)",
        ],
        "trend_indexes": [
            "CREATE INDEX IF NOT EXISTS idx_trend_skill ON trend_data(skill_id)",
            "CREATE INDEX IF NOT EXISTS idx_trend_metric ON trend_data(metric_name)",
            "CREATE INDEX IF NOT EXISTS idx_trend_timestamp ON trend_data(timestamp DESC)",
        ],
    }

    def __init__(self, db_path: Optional[str] = None):
        """Initialize SQLite schema manager.

        Args:
            db_path: Path to SQLite database file. Uses default if not provided.
        """
        if db_path is None:
            home = Path.home()
            path = home / ".toolweaver" / "analytics.db"
        else:
            path = Path(db_path).expanduser()

        self.db_path = path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Enable WAL mode for better concurrency
        self.pragmas = {
            "journal_mode": "WAL",
            "synchronous": "NORMAL",
            "cache_size": "-64000",  # 64MB cache
            "foreign_keys": "ON",
            "temp_store": "MEMORY",
        }

    def connect(self) -> sqlite3.Connection:
        """Create database connection with proper configuration.

        Returns:
            SQLite connection object.
        """
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False,
        )

        # Enable row factory for dict-like access
        conn.row_factory = sqlite3.Row

        # Set pragmas
        cursor = conn.cursor()
        for key, value in self.pragmas.items():
            cursor.execute(f"PRAGMA {key}={value}")
        cursor.close()

        return conn

    def initialize(self) -> bool:
        """Initialize database schema. Safe to call multiple times.

        Returns:
            True if initialization was successful.
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            # Create all tables
            for table_name, sql in self.TABLES.items():
                logger.debug(f"Creating table: {table_name}")
                cursor.execute(sql)

            # Create all indexes
            for index_group, index_sqls in self.INDEXES.items():
                for sql in index_sqls:
                    logger.debug(f"Creating index from group: {index_group}")
                    cursor.execute(sql)

            # Initialize schema version
            cursor.execute("INSERT OR IGNORE INTO schema_version (id, version) VALUES (1, ?)", (self.SCHEMA_VERSION,))

            conn.commit()
            logger.info(f"Database initialized: {self.db_path}")
            logger.info(f"Schema version: {self.SCHEMA_VERSION}")

            conn.close()
            return True

        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            return False

    def get_schema_version(self) -> int:
        """Get current schema version.

        Returns:
            Schema version number.
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT version FROM schema_version WHERE id=1")
            row = cursor.fetchone()
            conn.close()

            return row[0] if row else 0

        except sqlite3.Error as e:
            logger.error(f"Error reading schema version: {e}")
            return 0

    def cleanup_old_data(self, retention_days: int) -> int:
        """Delete data older than retention period.

        Args:
            retention_days: Number of days to retain data. 0 = keep all.

        Returns:
            Number of rows deleted.
        """
        if retention_days <= 0:
            logger.info("Data retention disabled (retention_days=0)")
            return 0

        try:
            conn = self.connect()
            cursor = conn.cursor()

            # Calculate cutoff date
            cutoff_date = datetime.fromtimestamp(
                datetime.now().timestamp() - (retention_days * 86400)
            ).isoformat()

            # Delete old data from each table
            tables_to_clean = [
                "skill_usage",
                "recommendation_log",
                "trend_data",
                "leaderboard_cache",
            ]

            total_deleted = 0
            for table in tables_to_clean:
                cursor.execute(f"DELETE FROM {table} WHERE timestamp < ?", (cutoff_date,))
                deleted = cursor.rowcount
                total_deleted += deleted
                logger.info(f"Deleted {deleted} old records from {table}")

            conn.commit()
            conn.close()

            logger.info(f"Data cleanup complete: {total_deleted} rows deleted (retention: {retention_days} days)")
            return total_deleted

        except sqlite3.Error as e:
            logger.error(f"Error during cleanup: {e}")
            return 0

    def vacuum(self) -> bool:
        """Optimize database file size.

        Returns:
            True if successful.
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            conn.close()
            logger.info("Database vacuumed successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error during vacuum: {e}")
            return False

    def get_db_stats(self) -> dict:
        """Get database statistics.

        Returns:
            Dictionary with table counts and sizes.
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            tables: dict[str, int] = {}
            stats = {
                "timestamp": datetime.now().isoformat(),
                "tables": tables,
            }

            # Get row counts for each table (skip schema_version)
            for table_name in self.TABLES.keys():
                if table_name == "version":  # Skip internal schema version table
                    continue
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                tables[table_name] = count

            conn.close()
            return stats

        except sqlite3.Error as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

    def health_check(self) -> bool:
        """Check database integrity.

        Returns:
            True if database is healthy.
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()

            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]

            conn.close()

            if result == "ok":
                logger.info("Database integrity check passed")
                return True
            else:
                logger.error(f"Database integrity issue: {result}")
                return False

        except sqlite3.Error as e:
            logger.error(f"Error during health check: {e}")
            return False


def initialize_analytics_db(
    db_path: Optional[str] = None, retention_days: int = 365, cleanup: bool = False
) -> bool:
    """Convenience function to initialize analytics database.

    Args:
        db_path: Path to SQLite database file.
        retention_days: Data retention period in days.
        cleanup: Whether to run cleanup on old data.

    Returns:
        True if initialization was successful.
    """
    schema = SQLiteSchema(db_path)

    # Initialize schema
    if not schema.initialize():
        return False

    # Run cleanup if requested
    if cleanup:
        schema.cleanup_old_data(retention_days)

    # Verify database health
    if not schema.health_check():
        logger.warning("Database health check failed, but initialization continued")

    logger.info("Analytics database ready")
    return True
