"""
Experiment 4: Effectiveness Validation
Goal: Prove 100% violation detection accuracy
Method: Send transactions with KNOWN violations, verify ALL are detected

Load Pattern: 100 transactions over 2 minutes
- 30 transactions with known violations (tracked by UUID)
- 70 valid transactions

Success Criteria:
- Detection Accuracy = 100% (all 30 violations must be detected)
- Zero false positives (0 valid transactions flagged as violations)

Post-Test Verification:
- Query database to count violations
- Match transaction IDs with injected violations
"""

import random
import json
import uuid
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import csv
import time

# CSV file for detailed transaction logs
csv_file = None
csv_writer = None

# Track injected violations for verification
injected_violations = set()
injected_violations_lock = None

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize CSV logging and violation tracking"""
    global csv_file, csv_writer, injected_violations_lock
    import threading
    injected_violations_lock = threading.Lock()

    if isinstance(environment.runner, MasterRunner):
        csv_file = open(f'/tmp/experiment4_effectiveness_{int(time.time())}.csv', 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            'timestamp', 'architecture', 'transaction_id', 'response_time_ms',
            'success', 'injected_violation', 'violation_type', 'expected_detection',
            'detected_in_response', 'loan_amount', 'applicant_role', 'status'
        ])

@events.quitting.add_listener
def on_locust_quit(environment, **kwargs):
    """Close CSV and save violation list"""
    global csv_file, injected_violations

    if csv_file:
        csv_file.close()

    # Save list of injected violations for post-test verification
    with open(f'/tmp/injected_violations_{int(time.time())}.json', 'w') as f:
        json.dump({
            'total_injected': len(injected_violations),
            'transaction_ids': list(injected_violations)
        }, f, indent=2)

    print(f"\n===== Experiment 4 Summary =====")
    print(f"Total Violations Injected: {len(injected_violations)}")
    print(f"Violation IDs saved to: /tmp/injected_violations_*.json")
    print(f"Run post-test verification script to validate 100% detection")

class EffectivenessTestUser(HttpUser):
    wait_time = between(1.0, 2.0)

    import os
    architecture = os.getenv("ARCHITECTURE", "bpc4msa")

    ports = {
        "bpc4msa": 8000,
        "synchronous": 8001,
        "monolithic": 8002
    }

    @property
    def host(self):
        return f"http://localhost:{self.ports[self.architecture]}"

    names = ["Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace", "Henry"]

    # Counter to maintain 30% violation rate
    transaction_count = 0
    violation_count = 0

    @task
    def apply_for_loan(self):
        """Submit loan application with controlled violation rate"""

        self.transaction_count += 1

        # Ensure 30% violation rate: inject violation if we're below target
        target_violations = int(self.transaction_count * 0.3)
        should_violate = self.violation_count < target_violations

        violation_type = None
        expected_detection = False

        if should_violate:
            self.violation_count += 1
            expected_detection = True

            # Randomly choose violation type
            violation_choice = random.choice(['amount', 'role', 'both'])

            if violation_choice == 'amount':
                violation_type = 'amount_exceeds_limit'
                payload = {
                    "applicant_name": random.choice(self.names),
                    "loan_amount": random.randint(15000, 50000),  # Exceeds 10000 limit
                    "applicant_role": "customer",  # Valid
                    "credit_score": random.randint(600, 850),
                    "employment_status": "employed",
                    "status": "pending"
                }
            elif violation_choice == 'role':
                violation_type = 'forbidden_role'
                payload = {
                    "applicant_name": random.choice(self.names),
                    "loan_amount": random.randint(1000, 9000),  # Valid
                    "applicant_role": random.choice(["admin", "superuser"]),  # Forbidden
                    "credit_score": random.randint(600, 850),
                    "employment_status": "employed",
                    "status": "pending"
                }
            else:  # both
                violation_type = 'amount_and_role'
                payload = {
                    "applicant_name": random.choice(self.names),
                    "loan_amount": random.randint(15000, 50000),  # Exceeds limit
                    "applicant_role": random.choice(["admin", "superuser"]),  # Forbidden
                    "credit_score": random.randint(400, 600),
                    "employment_status": random.choice(["employed", "unemployed"]),
                    "status": "pending"
                }
        else:
            # Valid transaction (no violations)
            violation_type = 'none'
            payload = {
                "applicant_name": random.choice(self.names),
                "loan_amount": random.randint(1000, 9000),
                "applicant_role": "customer",
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

                    # Track injected violations globally
                    if expected_detection:
                        with injected_violations_lock:
                            injected_violations.add(transaction_id)

                    # Check if violation was detected in response
                    # (Only applicable to Synchronous SOA and Monolithic)
                    detected_in_response = False
                    if 'violations' in data and len(data['violations']) > 0:
                        detected_in_response = True

                    if csv_writer:
                        csv_writer.writerow([
                            time.time(),
                            self.architecture,
                            transaction_id,
                            response_time,
                            True,
                            expected_detection,
                            violation_type,
                            expected_detection,
                            detected_in_response,
                            payload['loan_amount'],
                            payload['applicant_role'],
                            payload['status']
                        ])

                    response.success()
                else:
                    response.failure(f"Status {response.status_code}")

            except Exception as e:
                response.failure(f"Error: {str(e)}")

# Run configuration:
#
# BPC4MSA (async detection):
# ARCHITECTURE=bpc4msa locust -f locustfile_experiment4_effectiveness.py --headless \
#    -u 10 -r 2 --run-time 2m \
#    --csv experiment4_effectiveness_bpc4msa --html experiment4_effectiveness_bpc4msa.html
#
# Synchronous SOA (immediate detection):
# ARCHITECTURE=synchronous locust -f locustfile_experiment4_effectiveness.py --headless \
#    -u 10 -r 2 --run-time 2m \
#    --csv experiment4_effectiveness_synchronous --html experiment4_effectiveness_synchronous.html
#
# Monolithic (immediate detection):
# ARCHITECTURE=monolithic locust -f locustfile_experiment4_effectiveness.py --headless \
#    -u 10 -r 2 --run-time 2m \
#    --csv experiment4_effectiveness_monolithic --html experiment4_effectiveness_monolithic.html
#
# POST-TEST VERIFICATION:
# Run verification script to query database and confirm 100% detection rate
