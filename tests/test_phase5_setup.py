"""
Phase 5 Analytics Setup Verification Test

Tests SQLite database, SkillAnalytics, and Grafana integration.
Verifies end-to-end analytics pipeline before Phase 5.1 implementation.

Run with: python -m pytest tests/test_phase5_setup.py -v
Or directly: python tests/test_phase5_setup.py
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
import json

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator._internal.execution.analytics import (
    SkillAnalytics,
    SQLiteSchema,
    initialize_analytics_db,
    MetricType,
)


class Phase5TestRunner:
    """Comprehensive Phase 5 setup verification."""

    def __init__(self):
        self.db_path = Path.home() / ".toolweaver" / "analytics_test.db"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {"passed": 0, "failed": 0, "total": 0},
        }

    def log_test(self, name: str, passed: bool, message: str = ""):
        """Log test result."""
        self.results["tests"][name] = {
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        if passed:
            self.results["summary"]["passed"] += 1
            print(f"✅ {name}")
            if message:
                print(f"   └─ {message}")
        else:
            self.results["summary"]["failed"] += 1
            print(f"❌ {name}")
            if message:
                print(f"   └─ {message}")
        self.results["summary"]["total"] += 1

    def test_sqlite_schema_creation(self) -> bool:
        """Test SQLite schema initialization."""
        try:
            schema = SQLiteSchema(str(self.db_path))
            success = schema.initialize()

            if success and self.db_path.exists():
                self.log_test(
                    "SQLite Schema Creation",
                    True,
                    f"Database created at {self.db_path}",
                )
                return True
            else:
                self.log_test("SQLite Schema Creation", False, "Failed to create database")
                return False

        except Exception as e:
            self.log_test("SQLite Schema Creation", False, str(e))
            return False

    def test_sqlite_tables(self) -> bool:
        """Verify all required tables exist."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get all tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            required_tables = [
                "skill_usage",
                "skill_metrics",
                "leaderboard_cache",
                "recommendation_log",
                "adoption_metrics",
                "health_scores",
                "trend_data",
                "schema_version",
            ]

            missing = set(required_tables) - set(tables)
            if not missing:
                self.log_test(
                    "SQLite Table Verification",
                    True,
                    f"{len(tables)} tables created: {', '.join(tables[:3])}...",
                )
                return True
            else:
                self.log_test(
                    "SQLite Table Verification",
                    False,
                    f"Missing tables: {', '.join(missing)}",
                )
                return False

        except Exception as e:
            self.log_test("SQLite Table Verification", False, str(e))
            return False

    def test_skill_analytics_initialization(self) -> bool:
        """Test SkillAnalytics class initialization."""
        try:
            analytics = SkillAnalytics(str(self.db_path))
            self.analytics = analytics

            # Check schema object exists
            if analytics.schema and analytics.db_path:
                self.log_test(
                    "SkillAnalytics Initialization",
                    True,
                    f"Analytics engine ready at {analytics.db_path}",
                )
                return True
            else:
                self.log_test("SkillAnalytics Initialization", False, "Incomplete initialization")
                return False

        except Exception as e:
            self.log_test("SkillAnalytics Initialization", False, str(e))
            return False

    def test_record_skill_usage(self) -> bool:
        """Test recording skill usage metrics."""
        try:
            success = self.analytics.record_skill_usage(
                skill_id="test-skill",
                user_id="test-user-1",
                org_id="test-org",
                success=True,
                latency_ms=123.45,
            )

            if success:
                self.log_test(
                    "Record Skill Usage",
                    True,
                    "Recorded: test-skill by test-user-1 (latency: 123.45ms)",
                )
                return True
            else:
                self.log_test("Record Skill Usage", False, "Failed to record usage")
                return False

        except Exception as e:
            self.log_test("Record Skill Usage", False, str(e))
            return False

    def test_get_skill_usage(self) -> bool:
        """Test retrieving skill usage metrics."""
        try:
            usage = self.analytics.get_skill_usage("test-skill", days=30)

            if usage and usage.get("total_executions", 0) > 0:
                self.log_test(
                    "Get Skill Usage",
                    True,
                    f"Retrieved metrics: {usage['total_executions']} executions, "
                    f"{usage['success_rate']:.1%} success rate",
                )
                return True
            else:
                self.log_test("Get Skill Usage", False, "No usage data found")
                return False

        except Exception as e:
            self.log_test("Get Skill Usage", False, str(e))
            return False

    def test_rate_skill(self) -> bool:
        """Test skill rating functionality."""
        try:
            # Record ratings
            for rating in [5, 4, 5, 3]:
                self.analytics.rate_skill("test-skill", rating, org_id="test-org")

            # Verify rating aggregation
            metrics = self.analytics.get_skill_metrics("test-skill")
            if metrics and metrics.rating_count >= 4:
                self.log_test(
                    "Rate Skill",
                    True,
                    f"Recorded 4 ratings, avg: {metrics.rating_avg:.2f}/5",
                )
                return True
            else:
                self.log_test("Rate Skill", False, "Failed to record ratings")
                return False

        except Exception as e:
            self.log_test("Rate Skill", False, str(e))
            return False

    def test_leaderboard_computation(self) -> bool:
        """Test leaderboard ranking."""
        try:
            # Record more usage for different skills
            for i in range(3):
                self.analytics.record_skill_usage(
                    skill_id=f"skill-{i}",
                    user_id=f"user-{i}",
                    success=True,
                    latency_ms=100 + i * 50,
                )

            # Compute leaderboard
            leaderboard = self.analytics.compute_leaderboard(
                metric_type=MetricType.USAGE_COUNT, limit=5
            )

            if leaderboard and len(leaderboard) > 0:
                self.log_test(
                    "Leaderboard Computation",
                    True,
                    f"Generated {len(leaderboard)} rankings, top: {leaderboard[0]['skill_id']}",
                )
                return True
            else:
                self.log_test("Leaderboard Computation", False, "Empty leaderboard")
                return False

        except Exception as e:
            self.log_test("Leaderboard Computation", False, str(e))
            return False

    def test_recommendations(self) -> bool:
        """Test recommendation engine."""
        try:
            recs = self.analytics.recommend_skills("test-user-1", limit=3)

            if recs and len(recs) > 0:
                rec_types = [r.recommendation_type.value for r in recs]
                self.log_test(
                    "Recommendations",
                    True,
                    f"Generated {len(recs)} recommendations: {', '.join(rec_types[:2])}",
                )
                return True
            else:
                self.log_test("Recommendations", False, "No recommendations generated")
                return False

        except Exception as e:
            self.log_test("Recommendations", False, str(e))
            return False

    def test_health_scoring(self) -> bool:
        """Test health score calculation."""
        try:
            score = self.analytics.compute_health_score("test-skill")

            if 0 <= score <= 100:
                self.log_test(
                    "Health Scoring",
                    True,
                    f"Computed health score: {score:.1f}/100",
                )
                return True
            else:
                self.log_test("Health Scoring", False, f"Invalid score: {score}")
                return False

        except Exception as e:
            self.log_test("Health Scoring", False, str(e))
            return False

    def test_trends(self) -> bool:
        """Test trend analysis."""
        try:
            trends = self.analytics.get_usage_trends("test-skill", period_days=7)

            if trends and len(trends) > 0:
                self.log_test(
                    "Trend Analysis",
                    True,
                    f"Retrieved {len(trends)} data points",
                )
                return True
            else:
                self.log_test("Trend Analysis", False, "No trend data")
                return False

        except Exception as e:
            self.log_test("Trend Analysis", False, str(e))
            return False

    def test_database_stats(self) -> bool:
        """Test database statistics."""
        try:
            stats = self.analytics.get_db_stats()

            if stats and "tables" in stats:
                total_rows = sum(stats["tables"].values())
                self.log_test(
                    "Database Stats",
                    True,
                    f"Database has {total_rows} total rows across {len(stats['tables'])} tables",
                )
                return True
            else:
                self.log_test("Database Stats", False, "Could not retrieve stats")
                return False

        except Exception as e:
            self.log_test("Database Stats", False, str(e))
            return False

    def test_database_health(self) -> bool:
        """Test database integrity."""
        try:
            healthy = self.analytics.health_check()

            if healthy:
                self.log_test(
                    "Database Health",
                    True,
                    "Integrity check passed",
                )
                return True
            else:
                self.log_test("Database Health", False, "Integrity check failed")
                return False

        except Exception as e:
            self.log_test("Database Health", False, str(e))
            return False

    def test_grafana_environment(self) -> bool:
        """Test Grafana environment configuration."""
        try:
            grafana_url = os.getenv("GRAFANA_URL")
            grafana_key = os.getenv("GRAFANA_API_KEY")

            if grafana_url and grafana_key:
                # Mask API key for display
                masked_key = f"{grafana_key[:10]}...{grafana_key[-10:]}"
                self.log_test(
                    "Grafana Configuration",
                    True,
                    f"URL: {grafana_url} | Key: {masked_key}",
                )
                return True
            else:
                missing = []
                if not grafana_url:
                    missing.append("GRAFANA_URL")
                if not grafana_key:
                    missing.append("GRAFANA_API_KEY")
                self.log_test(
                    "Grafana Configuration",
                    False,
                    f"Missing: {', '.join(missing)}",
                )
                return False

        except Exception as e:
            self.log_test("Grafana Configuration", False, str(e))
            return False

    def test_grafana_connection(self) -> bool:
        """Test Grafana API connectivity."""
        try:
            from orchestrator._internal.execution.analytics.grafana_client import GrafanaClient, GrafanaConfig

            config = GrafanaConfig(
                url=os.getenv("GRAFANA_URL", ""),
                api_key=os.getenv("GRAFANA_API_KEY", ""),
            )
            client = GrafanaClient(config)
            
            if client.health_check():
                self.log_test(
                    "Grafana Connection",
                    True,
                    "Successfully connected to Grafana API",
                )
                return True
            else:
                self.log_test("Grafana Connection", False, "Health check failed")
                return False

        except Exception as e:
            self.log_test("Grafana Connection", False, str(e))
            return False

    def cleanup(self):
        """Clean up test database."""
        try:
            if self.db_path.exists():
                self.db_path.unlink()
                print(f"\n[CLEANUP] Cleaned up test database: {self.db_path}")
        except Exception as e:
            print(f"\n[WARNING] Could not clean up test database: {e}")

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("PHASE 5 ANALYTICS SETUP VERIFICATION")
        print("=" * 60)

        summary = self.results["summary"]
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]

        if failed == 0:
            status = "[SUCCESS] ALL TESTS PASSED"
            print(f"\n{status}")
            print(f"[PASS] {passed}/{total} tests passed")
            print("\n[READY] Phase 5 is ready to use!")
            print("\nNext steps:")
            print("1. Use SkillAnalytics to record metrics")
            print("2. View dashboards at your Grafana instance")
            print("3. Start Phase 5.1 implementation")
        else:
            status = "[WARNING] SOME TESTS FAILED"
            print(f"\n{status}")
            print(f"[PASS] {passed} passed, [FAIL] {failed} failed out of {total} total")
            print("\nFailed tests:")
            for name, result in self.results["tests"].items():
                if not result["passed"]:
                    print(f"  - {name}: {result['message']}")

        print("=" * 60 + "\n")

        # Save results to file
        results_file = Path(__file__).parent / "phase5_test_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"[RESULTS] Saved to: {results_file}\n")

    def run_all_tests(self):
        """Run all verification tests."""
        print("\n[TEST] Running Phase 5 Analytics Setup Verification...\n")

        # SQLite tests
        print("[SQLITE] SQLite Database Tests:")
        self.test_sqlite_schema_creation()
        self.test_sqlite_tables()

        # Analytics tests
        print("\n[ANALYTICS] Analytics Engine Tests:")
        if self.test_skill_analytics_initialization():
            self.test_record_skill_usage()
            self.test_get_skill_usage()
            self.test_rate_skill()
            self.test_leaderboard_computation()
            self.test_recommendations()
            self.test_health_scoring()
            self.test_trends()
            self.test_database_stats()
            self.test_database_health()

        # Grafana tests
        print("\n[GRAFANA] Grafana Integration Tests:")
        self.test_grafana_environment()
        self.test_grafana_connection()

        # Cleanup and summary
        self.cleanup()
        self.print_summary()

        return self.results["summary"]["failed"] == 0


def main():
    """Main entry point."""
    runner = Phase5TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
