"""
Experiment 5: Dynamic Rule Adaptability
Goal: Demonstrate runtime rule updates without system restart (NQ3)
Method: Continuous load test while updating rules.json mid-test

Test Flow:
1. Start continuous load (2 minutes)
2. At 60 seconds, update rules.json (change loan threshold)
3. Continue load for another 60 seconds
4. Measure violation rate before and after rule change

Expected Result:
- Clear, immediate drop in violations per second when rule is updated
- Graph shows sharp transition at t=60s

Rule Changes:
- Initial: loan_threshold = 10000 (RULE002)
- Updated: loan_threshold = 15000 (relaxed rule)
- Effect: Loans 10000-15000 will stop being flagged as violations
"""

import random
import json
import time
import os
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import csv

# CSV file for detailed transaction logs
csv_file = None
csv_writer = None

# Test start time
test_start_time = None

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize CSV logging"""
    global csv_file, csv_writer, test_start_time

    test_start_time = time.time()

    if isinstance(environment.runner, MasterRunner):
        csv_file = open(f'/tmp/experiment5_adaptability_{int(time.time())}.csv', 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            'timestamp', 'elapsed_seconds', 'transaction_id', 'response_time_ms',
            'success', 'loan_amount', 'expected_violation_before_update',
            'expected_violation_after_update', 'detected_in_response'
        ])

@events.quitting.add_listener
def on_locust_quit(environment, **kwargs):
    """Close CSV file"""
    global csv_file
    if csv_file:
        csv_file.close()

    print("\n===== Experiment 5: Adaptability Test Complete =====")
    print("Rule Update Timeline:")
    print("  0-60s: Initial rules (threshold = 10000)")
    print("  60s: Rules updated (threshold = 15000)")
    print("  60-120s: Updated rules in effect")
    print("\nAnalysis:")
    print("  - Plot 'Violations per Second' over time")
    print("  - Expect sharp drop at t=60s")
    print("  - Demonstrates live rule adaptation (NQ3)")

class AdaptabilityTestUser(HttpUser):
    wait_time = between(0.5, 1.0)

    architecture = os.getenv("ARCHITECTURE", "bpc4msa")

    ports = {
        "bpc4msa": 8000,
        "synchronous": 8001,
        "monolithic": 8002
    }

    @property
    def host(self):
        return f"http://localhost:{self.ports[self.architecture]}"

    names = ["Alice", "Bob", "Carol", "David", "Emma", "Frank"]

    @task
    def apply_for_loan(self):
        """
        Submit loan applications targeting the threshold range.

        Strategy: Send 50% of loans in 10000-15000 range
        - Before update: These violate RULE002 (threshold 10000)
        - After update: These are valid (threshold 15000)
        """

        elapsed = time.time() - test_start_time

        # 50% in critical range (10000-15000), 25% below, 25% above
        choice = random.random()

        if choice < 0.5:
            # Critical range - will show adaptability
            loan_amount = random.randint(10000, 15000)
            expected_violation_before = True  # Violates old rule
            expected_violation_after = False  # Valid with new rule
        elif choice < 0.75:
            # Below threshold - always valid
            loan_amount = random.randint(1000, 9999)
            expected_violation_before = False
            expected_violation_after = False
        else:
            # Above new threshold - always violates
            loan_amount = random.randint(15001, 30000)
            expected_violation_before = True
            expected_violation_after = True

        payload = {
            "applicant_name": random.choice(self.names),
            "loan_amount": loan_amount,
            "applicant_role": "customer",  # Always valid role
            "credit_score": random.randint(600, 850),
            "employment_status": "employed",
            "status": "pending"
        }

        start_time = time.time()

        with self.client.post(
            "/api/loans/apply",
            json=payload,
            catch_response=True,
            name=f"POST /api/loans/apply ({self.architecture})"
        ) as response:

            response_time = (time.time() - start_time) * 1000

            try:
                if response.status_code == 200:
                    data = response.json()
                    transaction_id = data.get('transaction_id', 'UNKNOWN')

                    # Check if violation detected in response
                    detected_in_response = False
                    if 'violations' in data and len(data['violations']) > 0:
                        detected_in_response = True

                    if csv_writer:
                        csv_writer.writerow([
                            time.time(),
                            elapsed,
                            transaction_id,
                            response_time,
                            True,
                            loan_amount,
                            expected_violation_before,
                            expected_violation_after,
                            detected_in_response
                        ])

                    response.success()
                else:
                    response.failure(f"Status {response.status_code}")

            except Exception as e:
                response.failure(f"Error: {str(e)}")

# MANUAL TEST PROCEDURE:
#
# Terminal 1 - Start Load Test:
# ARCHITECTURE=synchronous locust -f locustfile_experiment5_adaptability.py --headless \
#    -u 20 -r 4 --run-time 2m \
#    --csv experiment5_adaptability --html experiment5_adaptability.html
#
# Terminal 2 - Update Rules at 60 seconds:
# sleep 60 && python update_rules.py --threshold 15000
#
# OR manually edit config/rules.json:
# {
#   "id": "RULE002",
#   "type": "field_range",
#   "description": "Transaction amount must be between 0 and 15000",
#   "field": "amount",
#   "min": 0,
#   "max": 15000  <-- Change from 10000 to 15000
# }
#
# The compliance-service reads rules.json every 10 seconds (RULES_CHECK_INTERVAL=10)
# So the change will be picked up within 10 seconds of file modification
#
# ANALYSIS:
# - Load CSV into analysis script
# - Group by 10-second windows
# - Count violations per window
# - Plot time-series graph showing sharp drop at t=60-70s
