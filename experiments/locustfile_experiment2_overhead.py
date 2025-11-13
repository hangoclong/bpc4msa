"""
Experiment 2: Compliance Overhead
Goal: Quantify performance cost of BPC4MSA compliance checking
Method: Run IDENTICAL load as Experiment 1, but with compliance-service ACTIVE

Load Pattern: Fixed load of 500 transactions over 5 minutes (same as Experiment 1)
Metrics: Compare throughput and latency against Experiment 1 baseline
Expected: Small overhead (< 10%) due to async event processing
"""

import random
import json
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import csv
import time

# CSV file for detailed transaction logs
csv_file = None
csv_writer = None

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize CSV logging"""
    global csv_file, csv_writer
    if isinstance(environment.runner, MasterRunner):
        csv_file = open(f'/tmp/experiment2_overhead_{int(time.time())}.csv', 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            'timestamp', 'transaction_id', 'response_time_ms',
            'success', 'loan_amount', 'applicant_role', 'status_code',
            'has_violations'  # Track if violations were detected
        ])

@events.quitting.add_listener
def on_locust_quit(environment, **kwargs):
    """Close CSV file"""
    global csv_file
    if csv_file:
        csv_file.close()

class LoanApplicationUser(HttpUser):
    wait_time = between(0.5, 1.5)
    host = "http://localhost:8000"

    names = ["Alice Johnson", "Bob Smith", "Carol Williams", "David Brown",
             "Emma Davis", "Frank Miller", "Grace Wilson", "Henry Moore"]

    @task
    def apply_for_loan(self):
        """Submit a valid loan application (same as Experiment 1)"""

        # Generate valid transaction data (identical to Experiment 1)
        payload = {
            "applicant_name": random.choice(self.names),
            "loan_amount": random.randint(1000, 9000),  # Within limit
            "applicant_role": "customer",  # Valid role
            "credit_score": random.randint(600, 850),
            "employment_status": random.choice(["employed", "self-employed"]),
            "status": "pending"  # Valid status
        }

        start_time = time.time()

        with self.client.post(
            "/api/loans/apply",
            json=payload,
            catch_response=True,
            name="POST /api/loans/apply (With Compliance)"
        ) as response:

            response_time = (time.time() - start_time) * 1000

            try:
                if response.status_code == 200:
                    data = response.json()
                    transaction_id = data.get('transaction_id', 'UNKNOWN')

                    # Note: BPC4MSA returns immediately, violations are checked async
                    # So we won't see violations in the response, but they'll be logged

                    if csv_writer:
                        csv_writer.writerow([
                            time.time(),
                            transaction_id,
                            response_time,
                            True,
                            payload['loan_amount'],
                            payload['applicant_role'],
                            response.status_code,
                            False  # No immediate violation info in BPC4MSA response
                        ])

                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")

                    if csv_writer:
                        csv_writer.writerow([
                            time.time(),
                            'FAILED',
                            response_time,
                            False,
                            payload['loan_amount'],
                            payload['applicant_role'],
                            response.status_code,
                            False
                        ])
            except Exception as e:
                response.failure(f"Error: {str(e)}")

# Run configuration:
# 1. Ensure compliance-service is RUNNING
# 2. locust -f locustfile_experiment2_overhead.py --headless \
#           -u 10 -r 2 --run-time 5m \
#           --csv experiment2_overhead \
#           --html experiment2_overhead_report.html
#
# Analysis:
# Overhead % = ((Exp1_TPS - Exp2_TPS) / Exp1_TPS) * 100
# Latency Increase = Exp2_P95_Latency - Exp1_P95_Latency
