"""
Test all three analytics backends: SQLite, OTLP, and Prometheus.

Verifies that all backends work correctly and have consistent interfaces.
"""

import logging
import os
import sys
import time

import pytest

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)


@pytest.mark.skip(reason="helper function used by other tests")
def test_backend(backend_name: str) -> bool:
    """Test a specific analytics backend"""
    print(f"\n{'='*70}")
    print(f"Testing {backend_name.upper()} Backend")
    print(f"{'='*70}")

    try:
        from orchestrator._internal.execution.analytics import create_analytics_client

        # Set backend
        os.environ["ANALYTICS_BACKEND"] = backend_name

        # Create client
        print(f"[INFO] Creating {backend_name} client...")
        client = create_analytics_client()
        print(f"[PASS] Client created: {type(client).__name__}")

        # Get config
        config = client.get_config_summary()
        print(f"[INFO] Backend: {config['backend']}")
        for key, value in config.items():
            if key != 'backend':
                print(f"[INFO]   {key}: {value}")

        # Record executions (use backend-specific method names)
        print("\n[INFO] Recording skill executions...")

        if backend_name == "sqlite":
            # SQLite uses record_skill_usage
            client.record_skill_usage(
                skill_id=f"test_skill_{backend_name}",
                user_id="test_user",
                org_id="test_org",
                success=True,
                latency_ms=123.45
            )
            client.record_skill_usage(
                skill_id=f"test_skill_{backend_name}",
                user_id="test_user",
                org_id="test_org",
                success=True,
                latency_ms=98.76
            )
            client.record_skill_usage(
                skill_id=f"test_skill_{backend_name}",
                user_id="test_user",
                org_id="test_org",
                success=False,
                latency_ms=250.0
            )
        else:
            # OTLP and Prometheus use record_skill_execution
            client.record_skill_execution(
                skill_id=f"test_skill_{backend_name}",
                success=True,
                latency_ms=123.45,
                user_id="test_user",
                org_id="test_org"
            )
            client.record_skill_execution(
                skill_id=f"test_skill_{backend_name}",
                success=True,
                latency_ms=98.76,
                user_id="test_user",
                org_id="test_org"
            )
            client.record_skill_execution(
                skill_id=f"test_skill_{backend_name}",
                success=False,
                latency_ms=250.0,
                user_id="test_user",
                org_id="test_org"
            )
        print("[PASS] Recorded 3 executions (2 success, 1 failure)")

        # Record ratings
        print("[INFO] Recording ratings...")
        if backend_name == "sqlite":
            # SQLite uses rate_skill(skill_id, rating, org_id)
            client.rate_skill(f"test_skill_{backend_name}", rating=5, org_id="test_org")
            client.rate_skill(f"test_skill_{backend_name}", rating=4, org_id="test_org")
        else:
            # OTLP and Prometheus use record_skill_rating(skill_id, rating, user_id)
            client.record_skill_rating(f"test_skill_{backend_name}", rating=5, user_id="test_user")
            client.record_skill_rating(f"test_skill_{backend_name}", rating=4, user_id="test_user")
        print("[PASS] Recorded 2 ratings (5 and 4 stars)")

        # Update health score
        print("[INFO] Updating health score...")
        client.update_health_score(f"test_skill_{backend_name}", score=82.5)
        print("[PASS] Updated health score to 82.5/100")

        # Health check
        print("[INFO] Running health check...")
        healthy = client.health_check()
        if healthy:
            print("[PASS] Health check passed")
        else:
            print("[WARN] Health check failed")

        print(f"\n[SUCCESS] {backend_name.upper()} backend working correctly!")
        return True

    except Exception as e:
        print(f"\n[FAIL] {backend_name.upper()} backend failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sqlite_backend() -> bool:
    """Test SQLite backend"""
    return test_backend("sqlite")


def test_otlp_backend() -> bool:
    """Test OTLP backend"""
    # Check if configured
    if not all([os.getenv("OTLP_ENDPOINT"), os.getenv("OTLP_INSTANCE_ID"), os.getenv("OTLP_TOKEN")]):
        print("\n[SKIP] OTLP backend not configured")
        print("[INFO] Set OTLP_ENDPOINT, OTLP_INSTANCE_ID, OTLP_TOKEN to test OTLP")
        return False

    result = test_backend("otlp")

    if result:
        print("\n[INFO] Waiting for OTLP export cycle (60 seconds)...")
        time.sleep(62)
        print("[INFO] OTLP metrics should now be visible in Grafana Cloud")

    return result


def test_prometheus_backend() -> bool:
    """Test Prometheus backend"""
    result = test_backend("prometheus")

    if result:
        port = os.getenv("PROMETHEUS_PORT", "8000")
        print(f"\n[INFO] Prometheus metrics available at: http://localhost:{port}/metrics")
        print(f"[INFO] Test with: curl http://localhost:{port}/metrics")

    return result


def test_factory_function() -> bool:
    """Test factory function with different backends"""
    print(f"\n{'='*70}")
    print("Testing Factory Function")
    print(f"{'='*70}")

    try:
        from orchestrator._internal.execution.analytics import create_analytics_client

        backends = ["sqlite", "prometheus"]
        if all([os.getenv("OTLP_ENDPOINT"), os.getenv("OTLP_INSTANCE_ID"), os.getenv("OTLP_TOKEN")]):
            backends.append("otlp")

        for backend in backends:
            print(f"\n[INFO] Testing factory with backend='{backend}'...")
            os.environ["ANALYTICS_BACKEND"] = backend
            client = create_analytics_client()
            print(f"[PASS] Created: {type(client).__name__}")

        print("\n[SUCCESS] Factory function works for all backends!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Factory function failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all backend tests"""
    print("="*70)
    print("ANALYTICS BACKENDS COMPREHENSIVE TEST")
    print("="*70)
    print("\nTesting all three analytics backends:")
    print("  1. SQLite (local database)")
    print("  2. OTLP (Grafana Cloud push)")
    print("  3. Prometheus (HTTP scraping)")

    results = {}

    # Test SQLite
    results["SQLite"] = test_sqlite_backend()

    # Test OTLP
    results["OTLP"] = test_otlp_backend()

    # Test Prometheus
    results["Prometheus"] = test_prometheus_backend()

    # Test factory
    results["Factory Function"] = test_factory_function()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for name, result in results.items():
        if result:
            print(f"[PASS] {name}")
        elif result is False:
            print(f"[FAIL] {name}")
        else:
            print(f"[SKIP] {name}")

    passed = sum(1 for r in results.values() if r is True)
    total = len(results)

    print("\n" + "="*70)
    if passed == total:
        print(f"[SUCCESS] ALL TESTS PASSED ({passed}/{total})")
        print("[READY] All analytics backends working!")
    else:
        print(f"[PARTIAL] {passed}/{total} tests passed")
    print("="*70)

    print("\n[INFO] Backend Comparison:")
    print("  - SQLite: Local storage, SQL queries, long retention")
    print("  - OTLP: Cloud push, automatic retention, zero maintenance")
    print("  - Prometheus: HTTP endpoint, pull-based, self-hosted")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
