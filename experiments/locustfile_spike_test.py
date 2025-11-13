"""
Scenario B: High-Concurrency Spike Test
From Future_Experiment_Design_Plan.md

Goal: Test BPC4MSA's advantage in handling traffic spikes
Hypothesis: BPC4MSA will gracefully queue requests in Kafka, maintaining low latency
           Monolithic will be overwhelmed with blocked worker threads

Configuration:
- 150 concurrent users
- 30-second duration
- High spawn rate (immediate spike)
- 10% violation rate
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
        csv_file = open(f'/tmp/spike_test_{int(time.time())}.csv', 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            'timestamp', 'transaction_id', 'response_time_ms',
            'success', 'loan_amount', 'applicant_role', 'status_code',
            'queue_depth'
        ])

@events.quitting.add_listener
def on_locust_quit(environment, **kwargs):
    """Close CSV file"""
    global csv_file
    if csv_file:
        csv_file.close()

class ConcurrencySpikeUser(HttpUser):
    wait_time = between(0.1, 0.3)  # Very short wait time for spike
    host = "http://localhost:8000"  # Change based on architecture being tested

    # Applicant names for variety
    names = ["Spike User " + str(i) for i in range(1, 151)]

    @task
    def apply_for_loan(self):
        """Submit loan application during concurrency spike"""

        # 10% violation rate
        is_violation = random.random() < 0.1

        if is_violation:
            # Generate violations
            payload = {
                "applicant_name": random.choice(self.names),
                "loan_amount": random.randint(10001, 50000),  # Over limit
                "applicant_role": random.choice(["admin", "manager"]),  # Invalid roles
                "credit_score": random.randint(300, 599),  # Low credit
                "employment_status": "unemployed",
                "status": "approved"  # Invalid status transition
            }
        else:
            # Generate valid transaction
            payload = {
                "applicant_name": random.choice(self.names),
                "loan_amount": random.randint(1000, 9000),
                "applicant_role": "customer",
                "credit_score": random.randint(650, 850),
                "employment_status": random.choice(["employed", "self-employed"]),
                "status": "pending"
            }

        start_time = time.time()

        with self.client.post(
            "/api/loans/apply",
            json=payload,
            catch_response=True,
            name="POST /api/loans/apply (Spike Test)"
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
                            response.status_code,
                            'N/A'  # Queue depth would need instrumentation
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
                            'N/A'
                        ])
            except Exception as e:
                response.failure(f"Error: {str(e)}")

# Run configuration (for command-line):
# locust -f locustfile_spike_test.py --headless \
#        -u 150 --spawn-rate 150 --run-time 30s \
#        --csv spike_test \
#        --html spike_test_report.html
#
# Key difference: --spawn-rate 150 means spawn all 150 users immediately (spike!)
