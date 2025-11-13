"""
Experiment 1: Baseline Performance
Goal: Establish baseline performance WITHOUT compliance checking
Method: Load test against business-logic service only (port 8000)
        Compliance service will be stopped for this test

Load Pattern: Fixed load of 500 transactions over 5 minutes
Expected TPS: ~1.67 TPS sustained load

Note: This test includes a ramp-up phase. Consider excluding the first
60 seconds from steady-state metrics to ensure accurate measurements.
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
        csv_file = open(f'/tmp/experiment1_baseline_{int(time.time())}.csv', 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            'timestamp', 'transaction_id', 'response_time_ms',
            'success', 'loan_amount', 'applicant_role', 'status_code'
        ])

@events.quitting.add_listener
def on_locust_quit(environment, **kwargs):
    """Close CSV file"""
    global csv_file
    if csv_file:
        csv_file.close()

class LoanApplicationUser(HttpUser):
    wait_time = between(0.5, 1.5)  # Wait 0.5-1.5s between requests
    host = "http://localhost:8000"

    # Applicant names for variety
    names = ["Alice Johnson", "Bob Smith", "Carol Williams", "David Brown",
             "Emma Davis", "Frank Miller", "Grace Wilson", "Henry Moore"]

    @task
    def apply_for_loan(self):
        """Submit a valid loan application (no violations)"""

        # Generate valid transaction data
        payload = {
            "applicant_name": random.choice(self.names),
            "loan_amount": random.randint(1000, 9000),  # Within limit (0-10000)
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
            name="POST /api/loans/apply (Baseline)"
        ) as response:

            response_time = (time.time() - start_time) * 1000  # Convert to ms

            try:
                if response.status_code == 200:
                    data = response.json()
                    transaction_id = data.get('transaction_id', 'UNKNOWN')

                    # Log to CSV
                    if csv_writer:
                        csv_writer.writerow([
                            time.time(),
                            transaction_id,
                            response_time,
                            True,
                            payload['loan_amount'],
                            payload['applicant_role'],
                            response.status_code
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
                            response.status_code
                        ])
            except Exception as e:
                response.failure(f"Error: {str(e)}")

# Run configuration (for command-line):
# locust -f locustfile_experiment1_baseline.py --headless \
#        -u 10 -r 2 --run-time 5m \
#        --csv experiment1_baseline \
#        --html experiment1_baseline_report.html
