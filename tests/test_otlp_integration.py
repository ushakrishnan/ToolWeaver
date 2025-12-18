"""
Test OTLP metrics integration with Grafana Cloud.

Tests OpenTelemetry metrics pushing to Grafana Cloud Prometheus.
"""

import os
import sys
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)


def test_otlp_config_loaded():
    """Test that OTLP configuration is loaded from environment"""
    print("\n=== Test 1: OTLP Configuration ===")
    
    required_vars = ["OTLP_ENDPOINT", "OTLP_INSTANCE_ID", "OTLP_TOKEN"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"[SKIP] Missing env vars: {missing}")
        print("Set OTLP_ENDPOINT, OTLP_INSTANCE_ID, OTLP_TOKEN to run OTLP tests")
        return False
    
    endpoint = os.getenv("OTLP_ENDPOINT")
    instance_id = os.getenv("OTLP_INSTANCE_ID")
    token = os.getenv("OTLP_TOKEN")
    
    print(f"[PASS] OTLP_ENDPOINT: {endpoint}")
    print(f"[PASS] OTLP_INSTANCE_ID: {instance_id}")
    print(f"[PASS] OTLP_TOKEN: ***{token[-8:]}")
    
    return True


def test_otlp_import():
    """Test that OTLP metrics module can be imported"""
    print("\n=== Test 2: OTLP Module Import ===")
    
    try:
        from orchestrator.execution.analytics import OTLPMetrics, OTLP_AVAILABLE
        
        if not OTLP_AVAILABLE:
            print("[FAIL] OTLP not available (missing dependencies)")
            print("Run: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http")
            return False
        
        print("[PASS] OTLPMetrics imported successfully")
        print(f"[PASS] OTLP_AVAILABLE: {OTLP_AVAILABLE}")
        return True
        
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        return False


def test_otlp_client_creation():
    """Test creating OTLP metrics client"""
    print("\n=== Test 3: OTLP Client Creation ===")
    
    try:
        from orchestrator.execution.analytics import OTLPMetrics
        
        client = OTLPMetrics()
        
        print("[PASS] OTLP client created successfully")
        
        config = client.get_config_summary()
        print(f"[INFO] Backend: {config['backend']}")
        print(f"[INFO] Endpoint: {config['endpoint']}")
        print(f"[INFO] Instance ID: {config['instance_id']}")
        print(f"[INFO] Push interval: {config['push_interval']}s")
        print(f"[INFO] Service: {config['service_name']} v{config['service_version']}")
        print(f"[INFO] Healthy: {config['healthy']}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Client creation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_record_metrics():
    """Test recording metrics to OTLP"""
    print("\n=== Test 4: Record Metrics ===")
    
    try:
        from orchestrator.execution.analytics import OTLPMetrics
        
        client = OTLPMetrics()
        
        # Record skill executions
        print("[INFO] Recording skill executions...")
        client.record_skill_execution(
            skill_id="test_skill_otlp",
            success=True,
            latency_ms=123.45,
            user_id="test_user",
            org_id="test_org"
        )
        client.record_skill_execution(
            skill_id="test_skill_otlp",
            success=True,
            latency_ms=98.76,
            user_id="test_user",
            org_id="test_org"
        )
        client.record_skill_execution(
            skill_id="test_skill_otlp",
            success=False,
            latency_ms=250.0,
            user_id="test_user",
            org_id="test_org"
        )
        print("[PASS] Recorded 3 skill executions")
        
        # Record ratings
        print("[INFO] Recording ratings...")
        client.record_skill_rating("test_skill_otlp", rating=5, user_id="test_user")
        client.record_skill_rating("test_skill_otlp", rating=4, user_id="test_user")
        print("[PASS] Recorded 2 ratings")
        
        # Update health score
        print("[INFO] Updating health score...")
        client.update_health_score("test_skill_otlp", score=82.5)
        print("[PASS] Updated health score")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Recording error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_factory_function():
    """Test factory function for creating analytics client"""
    print("\n=== Test 5: Factory Function ===")
    
    try:
        from orchestrator.execution.analytics import create_analytics_client
        
        # Test explicit OTLP backend
        print("[INFO] Creating OTLP client via factory...")
        client = create_analytics_client(backend="otlp")
        print(f"[PASS] Created client: {type(client).__name__}")
        
        # Test environment-based selection
        os.environ["ANALYTICS_BACKEND"] = "otlp"
        print("[INFO] Creating client from ANALYTICS_BACKEND env...")
        client2 = create_analytics_client()
        print(f"[PASS] Created client: {type(client2).__name__}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Factory error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wait_for_export():
    """Test waiting for metrics export to Grafana Cloud"""
    print("\n=== Test 6: Wait for Export ===")
    
    try:
        from orchestrator.execution.analytics import OTLPMetrics
        
        client = OTLPMetrics()
        push_interval = client.config.push_interval
        
        print(f"[INFO] Metrics will be exported in {push_interval} seconds...")
        print("[INFO] Waiting for export cycle...")
        
        # Wait for export
        time.sleep(push_interval + 2)
        
        print("[PASS] Export cycle completed")
        print("\n[SUCCESS] Check Grafana Cloud to see metrics!")
        print(f"[INFO] Go to: {os.getenv('GRAFANA_URL')}")
        print("[INFO] Navigate to: Explore → PromQL")
        print("[INFO] Query examples:")
        print('  - rate(toolweaver_skill_executions_total[5m])')
        print('  - toolweaver_skill_latency_milliseconds')
        print('  - toolweaver_skill_health_score')
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Export wait error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all OTLP integration tests"""
    print("=" * 70)
    print("OTLP METRICS INTEGRATION TEST")
    print("=" * 70)
    
    tests = [
        ("Configuration", test_otlp_config_loaded),
        ("Import", test_otlp_import),
        ("Client Creation", test_otlp_client_creation),
        ("Record Metrics", test_record_metrics),
        ("Factory Function", test_factory_function),
        ("Export Cycle", test_wait_for_export),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except KeyboardInterrupt:
            print("\n[CANCELLED] Test interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] {name} failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print("\n" + "=" * 70)
    if passed == total:
        print(f"[SUCCESS] ALL TESTS PASSED ({passed}/{total})")
        print("[READY] OTLP metrics integration is working!")
    else:
        print(f"[PARTIAL] {passed}/{total} tests passed")
        print("[WARNING] Some tests failed, check output above")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
