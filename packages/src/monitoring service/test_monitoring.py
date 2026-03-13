"""
Test script to verify monitoring service is working
"""
import requests
import json
import time
from datetime import datetime

MONITORING_URL = "http://localhost:8004"

def test_monitoring_service():
    """Test if monitoring service is accessible"""
    print("Testing Monitoring Service...")
    print("=" * 60)
    
    try:
        response = requests.get(f"{MONITORING_URL}/")
        print("✅ Monitoring service is running")
        print(f"   Response: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Monitoring service is not running")
        print("   Start it with: python main.py")
        return False

def test_send_log():
    """Test sending a log entry"""
    print("\nTesting Log Submission...")
    print("-" * 60)
    
    log_entry = {
        "service_name": "test_service",
        "level": "INFO",
        "message": "This is a test log message",
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "test": True,
            "user": "test_user"
        },
        "traceback": None,
        "correlation_id": "test-123"
    }
    
    try:
        response = requests.post(
            f"{MONITORING_URL}/api/logs",
            json=log_entry
        )
        if response.status_code == 200:
            print("✅ Log submitted successfully")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Failed to submit log: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error submitting log: {e}")
        return False

def test_send_error_log():
    """Test sending an error log with traceback"""
    print("\nTesting Error Log with Traceback...")
    print("-" * 60)
    
    log_entry = {
        "service_name": "test_service",
        "level": "ERROR",
        "message": "Test error message",
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {"error_code": "TEST_ERROR"},
        "traceback": "Traceback (most recent call last):\n  File 'test.py', line 10\n    raise ValueError('Test error')\nValueError: Test error",
        "correlation_id": "test-error-456"
    }
    
    try:
        response = requests.post(
            f"{MONITORING_URL}/api/logs",
            json=log_entry
        )
        if response.status_code == 200:
            print("✅ Error log submitted successfully")
            return True
        else:
            print(f"❌ Failed to submit error log: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error submitting error log: {e}")
        return False

def test_retrieve_logs():
    """Test retrieving logs"""
    print("\nTesting Log Retrieval...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{MONITORING_URL}/api/logs")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved logs successfully")
            print(f"   Total logs: {data['total']}")
            if data['logs']:
                print(f"   Latest log: {data['logs'][-1]['message']}")
            return True
        else:
            print(f"❌ Failed to retrieve logs: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error retrieving logs: {e}")
        return False

def test_retrieve_errors():
    """Test retrieving error logs"""
    print("\nTesting Error Log Retrieval...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{MONITORING_URL}/api/logs/errors")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved error logs successfully")
            print(f"   Total errors: {data['total']}")
            return True
        else:
            print(f"❌ Failed to retrieve error logs: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error retrieving error logs: {e}")
        return False

def test_retrieve_by_service():
    """Test retrieving logs by service name"""
    print("\nTesting Service-Specific Log Retrieval...")
    print("-" * 60)
    
    try:
        response = requests.get(f"{MONITORING_URL}/api/logs/service/test_service")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved service logs successfully")
            print(f"   Service: {data['service']}")
            print(f"   Total logs: {data['total']}")
            return True
        else:
            print(f"❌ Failed to retrieve service logs: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error retrieving service logs: {e}")
        return False

def test_filter_logs():
    """Test filtering logs"""
    print("\nTesting Log Filtering...")
    print("-" * 60)
    
    try:
        # Filter by service and level
        response = requests.get(
            f"{MONITORING_URL}/api/logs",
            params={
                "service_name": "test_service",
                "level": "ERROR",
                "limit": 10
            }
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Filtered logs successfully")
            print(f"   Total filtered logs: {data['total']}")
            return True
        else:
            print(f"❌ Failed to filter logs: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error filtering logs: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n")
    print("=" * 60)
    print("  MONITORING SERVICE TEST SUITE")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Service availability
    results.append(("Service Running", test_monitoring_service()))
    
    if results[0][1]:  # Only continue if service is running
        time.sleep(0.5)
        
        # Test 2: Send log
        results.append(("Send Log", test_send_log()))
        time.sleep(0.5)
        
        # Test 3: Send error log
        results.append(("Send Error Log", test_send_error_log()))
        time.sleep(0.5)
        
        # Test 4: Retrieve logs
        results.append(("Retrieve Logs", test_retrieve_logs()))
        time.sleep(0.5)
        
        # Test 5: Retrieve errors
        results.append(("Retrieve Errors", test_retrieve_errors()))
        time.sleep(0.5)
        
        # Test 6: Retrieve by service
        results.append(("Retrieve By Service", test_retrieve_by_service()))
        time.sleep(0.5)
        
        # Test 7: Filter logs
        results.append(("Filter Logs", test_filter_logs()))
    
    # Print summary
    print("\n")
    print("=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("-" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Monitoring service is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the monitoring service.")
    
    print("\nView all logs at: http://localhost:8004/api/logs")

if __name__ == "__main__":
    run_all_tests()
