"""
Experiment 3: Scalability Assessment
Goal: Evaluate how BPC4MSA scales under increasing load
Method: Test all 3 architectures with increasing TPS: 10, 25, 50, 75, 100

Load Pattern: Stepped load increase, each step runs for 2 minutes
Total Duration: ~10 minutes (5 steps × 2 min)

Metrics:
- Actual TPS achieved vs Target TPS (scalability curve)
- P95 latency at each load level (latency degradation)
- Resource consumption (CPU%, Memory) at each level
"""

import random
import json
from locust import HttpUser, task, between, events, LoadTestShape
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
        csv_file = open(f'/tmp/experiment3_scalability_{int(time.time())}.csv', 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            'timestamp', 'architecture', 'target_tps', 'transaction_id',
            'response_time_ms', 'success', 'loan_amount', 'has_violation',
            'status_code'
        ])

@events.quitting.add_listener
def on_locust_quit(environment, **kwargs):
    """Close CSV file"""
    global csv_file
    if csv_file:
        csv_file.close()

class CustomLoadShape(LoadTestShape):
    """
    Stepped load shape for scalability testing
    Each step runs for 120 seconds

    Steps:
    1. 10 TPS (10 users, spawn rate 2)
    2. 25 TPS (25 users, spawn rate 5)
    3. 50 TPS (50 users, spawn rate 10)
    4. 75 TPS (75 users, spawn rate 15)
    5. 100 TPS (100 users, spawn rate 20)
    """

    stages = [
        {"duration": 120, "users": 10, "spawn_rate": 2, "target_tps": 10},
        {"duration": 240, "users": 25, "spawn_rate": 5, "target_tps": 25},
        {"duration": 360, "users": 50, "spawn_rate": 10, "target_tps": 50},
        {"duration": 480, "users": 75, "spawn_rate": 15, "target_tps": 75},
        {"duration": 600, "users": 100, "spawn_rate": 20, "target_tps": 100},
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None  # Stop test after all stages

class ScalabilityTestUser(HttpUser):
    wait_time = between(0.8, 1.2)  # Tighter timing for higher TPS

    # Set architecture via environment variable
    # Example: ARCHITECTURE=bpc4msa
    import os
    architecture = os.getenv("ARCHITECTURE", "bpc4msa")

    # Port mapping
    ports = {
        "bpc4msa": 8000,
        "synchronous": 8001,
        "monolithic": 8002
    }

    @property
    def host(self):
        return f"http://localhost:{self.ports[self.architecture]}"

    names = ["Alice", "Bob", "Carol", "David", "Emma", "Frank", "Grace", "Henry"]

    @task
    def apply_for_loan(self):
        """Submit loan application with 30% violation rate"""

        # 30% chance of violation
        violate = random.random() < 0.3

        if violate:
            # Violating transaction
            payload = {
                "applicant_name": random.choice(self.names),
                "loan_amount": random.randint(15000, 50000),  # Exceeds limit
                "applicant_role": random.choice(["admin", "customer"]),  # Might be admin
                "credit_score": random.randint(400, 850),
                "employment_status": random.choice(["employed", "unemployed"]),
                "status": "pending"
            }
        else:
            # Valid transaction
            payload = {
                "applicant_name": random.choice(self.names),
                "loan_amount": random.randint(1000, 9000),
                "applicant_role": "customer",
                "credit_score": random.randint(600, 850),
                "employment_status": "employed",
                "status": "pending"
            }

        start_time = time.time()

        # Determine current target TPS based on elapsed time
        run_time = time.time() - self.environment.runner.start_time
        target_tps = 10  # Default
        for stage in CustomLoadShape.stages:
            if run_time < stage["duration"]:
                target_tps = stage["target_tps"]
                break

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

                    # Check if violations were returned (SOA/Mono only)
                    has_violation = False
                    if 'violations' in data and len(data['violations']) > 0:
                        has_violation = True

                    if csv_writer:
                        csv_writer.writerow([
                            time.time(),
                            self.architecture,
                            target_tps,
                            transaction_id,
                            response_time,
                            True,
                            payload['loan_amount'],
                            has_violation,
                            response.status_code
                        ])

                    response.success()
                else:
                    response.failure(f"Status {response.status_code}")

                    if csv_writer:
                        csv_writer.writerow([
                            time.time(),
                            self.architecture,
                            target_tps,
                            'FAILED',
                            response_time,
                            False,
                            payload['loan_amount'],
                            False,
                            response.status_code
                        ])
            except Exception as e:
                response.failure(f"Error: {str(e)}")

# Run configuration (run 3 times, once per architecture):
#
# BPC4MSA:
# ARCHITECTURE=bpc4msa locust -f locustfile_experiment3_scalability.py --headless \
#    --csv experiment3_scalability_bpc4msa --html experiment3_scalability_bpc4msa.html
#
# Synchronous SOA:
# ARCHITECTURE=synchronous locust -f locustfile_experiment3_scalability.py --headless \
#    --csv experiment3_scalability_synchronous --html experiment3_scalability_synchronous.html
#
# Monolithic:
# ARCHITECTURE=monolithic locust -f locustfile_experiment3_scalability.py --headless \
#    --csv experiment3_scalability_monolithic --html experiment3_scalability_monolithic.html
