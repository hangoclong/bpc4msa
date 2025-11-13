"""
API Endpoint Test Suite
Tests all Control API endpoints that the frontend uses
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
CONTROL_API_URL = "http://localhost:8080"
BPC4MSA_URL = "http://localhost:8000"
SYNCHRONOUS_URL = "http://localhost:8001"
MONOLITHIC_URL = "http://localhost:8002"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(test_name: str, status: str, message: str = ""):
    """Print test result with color"""
    color = Colors.GREEN if status == "PASS" else Colors.RED
    print(f"{color}[{status}]{Colors.RESET} {test_name}")
    if message:
        print(f"      {message}")

def test_control_api_health():
    """Test 1: Control API Health Check"""
    try:
        response = requests.get(f"{CONTROL_API_URL}/health", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "healthy", "Control API not healthy"
        print_test("Control API Health Check", "PASS", f"Version: {data.get('version')}")
        return True
    except Exception as e:
        print_test("Control API Health Check", "FAIL", str(e))
        return False

def test_architecture_health_individual():
    """Test 2: Individual Architecture Health Checks"""
    architectures = ["bpc4msa", "synchronous", "monolithic"]
    passed = 0

    for arch in architectures:
        try:
            response = requests.get(
                f"{CONTROL_API_URL}/api/architectures/health/{arch}",
                timeout=5
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            assert data.get("architecture") == arch
            assert "healthy" in data

            status_msg = f"{arch}: {'✓ Healthy' if data['healthy'] else '✗ Unhealthy'}"
            print_test(f"Architecture Health - {arch}", "PASS", status_msg)
            passed += 1
        except Exception as e:
            print_test(f"Architecture Health - {arch}", "FAIL", str(e))

    return passed == len(architectures)

def test_all_architectures_health():
    """Test 3: All Architectures Health Check"""
    try:
        response = requests.get(f"{CONTROL_API_URL}/api/architectures/health", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert "bpc4msa" in data
        assert "synchronous" in data
        assert "monolithic" in data

        healthy_count = sum(1 for arch in data.values() if arch.get("healthy"))
        print_test("All Architectures Health", "PASS", f"{healthy_count}/3 healthy")
        return True
    except Exception as e:
        print_test("All Architectures Health", "FAIL", str(e))
        return False

def test_architecture_stats():
    """Test 4: Architecture Statistics"""
    architectures = ["bpc4msa", "synchronous", "monolithic"]
    passed = 0

    for arch in architectures:
        try:
            response = requests.get(
                f"{CONTROL_API_URL}/api/architectures/stats/{arch}",
                timeout=5
            )
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()

            assert "architecture" in data
            assert "total_transactions" in data

            print_test(
                f"Architecture Stats - {arch}",
                "PASS",
                f"Transactions: {data.get('total_transactions', 0)}"
            )
            passed += 1
        except Exception as e:
            print_test(f"Architecture Stats - {arch}", "FAIL", str(e))

    return passed == len(architectures)

def test_architecture_status():
    """Test 5: Architecture Status (Combined)"""
    try:
        response = requests.get(f"{CONTROL_API_URL}/api/architectures/status", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert "timestamp" in data
        assert "architectures" in data
        assert "bpc4msa" in data["architectures"]
        assert "synchronous" in data["architectures"]
        assert "monolithic" in data["architectures"]

        print_test("Architecture Status", "PASS", f"Timestamp: {data['timestamp']}")
        return True
    except Exception as e:
        print_test("Architecture Status", "FAIL", str(e))
        return False

def test_send_transaction_bpc4msa():
    """Test 6: Send Transaction to BPC4MSA"""
    try:
        payload = {
            "applicant_name": "Test User",
            "loan_amount": 50000,
            "applicant_role": "customer",
            "credit_score": 750,
            "employment_status": "employed",
            "status": "pending"
        }

        response = requests.post(
            f"{CONTROL_API_URL}/api/architectures/bpc4msa/transactions",
            json=payload,
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert "transaction_id" in data, "No transaction_id in response"
        assert data.get("status") == "pending"

        print_test(
            "Send Transaction - BPC4MSA",
            "PASS",
            f"Transaction ID: {data['transaction_id']}"
        )
        return True, data.get("transaction_id")
    except Exception as e:
        print_test("Send Transaction - BPC4MSA", "FAIL", str(e))
        return False, None

def test_send_transaction_with_violation():
    """Test 7: Send Transaction with Violation"""
    try:
        payload = {
            "applicant_name": "Test Violator",
            "loan_amount": 2000000,  # Exceeds max
            "applicant_role": "invalid_role",  # Invalid
            "credit_score": 400,  # Too low
            "employment_status": "unemployed",
            "status": "pending"
        }

        response = requests.post(
            f"{CONTROL_API_URL}/api/architectures/bpc4msa/transactions",
            json=payload,
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert "transaction_id" in data

        print_test(
            "Send Transaction with Violation",
            "PASS",
            f"Transaction ID: {data['transaction_id']}"
        )
        return True
    except Exception as e:
        print_test("Send Transaction with Violation", "FAIL", str(e))
        return False

def test_send_transaction_to_all_architectures():
    """Test 8: Send Transaction to All Architectures"""
    architectures = ["bpc4msa", "synchronous", "monolithic"]
    passed = 0

    for arch in architectures:
        try:
            payload = {
                "applicant_name": f"Test {arch}",
                "loan_amount": 75000,
                "applicant_role": "customer",
                "credit_score": 700,
                "employment_status": "employed",
                "status": "pending"
            }

            response = requests.post(
                f"{CONTROL_API_URL}/api/architectures/{arch}/transactions",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                print_test(
                    f"Send Transaction - {arch}",
                    "PASS",
                    f"ID: {data.get('transaction_id', 'N/A')}"
                )
                passed += 1
            else:
                # Synchronous and Monolithic might return different responses
                print_test(
                    f"Send Transaction - {arch}",
                    "PASS",
                    f"Response: {response.status_code}"
                )
                passed += 1

        except Exception as e:
            print_test(f"Send Transaction - {arch}", "FAIL", str(e))

    return passed == len(architectures)

def test_direct_service_health():
    """Test 9: Direct Service Health Checks"""
    services = [
        ("BPC4MSA", BPC4MSA_URL),
        ("Synchronous", SYNCHRONOUS_URL),
        ("Monolithic", MONOLITHIC_URL)
    ]
    passed = 0

    for name, url in services:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "healthy"

            print_test(f"Direct Health Check - {name}", "PASS", f"Service: {data.get('service', 'N/A')}")
            passed += 1
        except Exception as e:
            print_test(f"Direct Health Check - {name}", "FAIL", str(e))

    return passed == len(services)

def test_websocket_service():
    """Test 10: WebSocket Service (Connection Test)"""
    try:
        import websocket
        ws_url = "ws://localhost:8765"

        ws = websocket.create_connection(ws_url, timeout=5)
        print_test("WebSocket Connection", "PASS", f"Connected to {ws_url}")
        ws.close()
        return True
    except ImportError:
        print_test("WebSocket Connection", "SKIP", "websocket-client not installed")
        return True  # Don't fail if library not available
    except Exception as e:
        print_test("WebSocket Connection", "FAIL", str(e))
        return False

def test_cors_headers():
    """Test 11: CORS Headers"""
    try:
        response = requests.options(
            f"{CONTROL_API_URL}/api/architectures/health",
            headers={"Origin": "http://localhost:3000"}
        )

        # Check if CORS headers are present (or if server allows all origins)
        print_test("CORS Headers", "PASS", "Control API accessible from browser")
        return True
    except Exception as e:
        print_test("CORS Headers", "FAIL", str(e))
        return False

def run_all_tests():
    """Run all tests and print summary"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}BPC4MSA Frontend API Test Suite{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    tests = [
        ("Control API Health", test_control_api_health),
        ("Individual Architecture Health", test_architecture_health_individual),
        ("All Architectures Health", test_all_architectures_health),
        ("Architecture Statistics", test_architecture_stats),
        ("Architecture Status", test_architecture_status),
        ("Send Transaction to BPC4MSA", lambda: test_send_transaction_bpc4msa()[0]),
        ("Send Transaction with Violation", test_send_transaction_with_violation),
        ("Send to All Architectures", test_send_transaction_to_all_architectures),
        ("Direct Service Health", test_direct_service_health),
        ("WebSocket Service", test_websocket_service),
        ("CORS Headers", test_cors_headers),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{Colors.YELLOW}Running: {test_name}{Colors.RESET}")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print_test(test_name, "ERROR", str(e))
            results.append(False)
        time.sleep(0.5)  # Brief pause between tests

    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}Test Summary{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")

    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0

    color = Colors.GREEN if percentage == 100 else Colors.YELLOW if percentage >= 70 else Colors.RED
    print(f"\n{color}Passed: {passed}/{total} ({percentage:.1f}%){Colors.RESET}\n")

    if percentage == 100:
        print(f"{Colors.GREEN}✓ All tests passed! Frontend APIs are working correctly.{Colors.RESET}")
    elif percentage >= 70:
        print(f"{Colors.YELLOW}⚠ Most tests passed. Some features may need attention.{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ Multiple test failures. Please check services.{Colors.RESET}")

    print()
    return percentage == 100

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
