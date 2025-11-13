"""
Locust load testing script for BPC4MSA framework experiments.

This script simulates loan application requests to test the performance
and compliance capabilities of the BPC4MSA framework.

Usage:
    # Basic test (Experiments 1-2)
    locust -f locustfile.py --headless -u 50 -r 10 --run-time 60s \\
           --host=http://localhost:8000 --csv=../results/test

    # Scalability test (Experiment 3)
    locust -f locustfile.py --headless -u 100 -r 10 --run-time 120s \\
           --host=http://localhost:8000 --csv=../results/exp3_100_users

    # Effectiveness test (Experiment 4) - with violations
    VIOLATION_RATE=0.1 locust -f locustfile.py --headless -u 10 -r 2 \\
           --run-time 30s --host=http://localhost:8000

    # Dynamic adaptability test (Experiment 5) - continuous load
    locust -f locustfile.py --headless -u 25 -r 5 --run-time 300s \\
           --host=http://localhost:8000 --csv=../results/exp5_adaptability
"""

import random
import os
from locust import HttpUser, task, between, events
import logging

# Configuration
VIOLATION_RATE = float(os.getenv('VIOLATION_RATE', '0.0'))  # 0.0 to 1.0
ENABLE_LOGGING = os.getenv('ENABLE_LOGGING', 'false').lower() == 'true'

# Setup logging
if ENABLE_LOGGING:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)

# Sample names for realistic data
APPLICANT_NAMES = [
    "John Smith", "Jane Doe", "Michael Johnson", "Emily Davis",
    "David Brown", "Sarah Wilson", "James Taylor", "Jessica Anderson",
    "Robert Martinez", "Lisa Garcia", "William Rodriguez", "Maria Hernandez"
]

# Violation counters for Experiment 4
violation_count = 0
total_requests = 0


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize Locust environment."""
    logger.info(f"Starting Locust with VIOLATION_RATE={VIOLATION_RATE}")


class LoanApplicantUser(HttpUser):
    """
    Simulates a user applying for loans through the BPC4MSA system.
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    @task
    def apply_for_loan(self):
        """
        Submit a loan application. Based on VIOLATION_RATE, may intentionally
        create violations to test compliance detection.
        """
        global violation_count, total_requests
        total_requests += 1

        # Determine if this request should be a violation
        should_violate = random.random() < VIOLATION_RATE

        if should_violate:
            # Create a violation by using parameters that break rules
            violation_type = random.choice(['amount', 'status', 'role'])

            if violation_type == 'amount':
                # Rule: amount must be between 0 and 10000
                loan_amount = random.choice([15000, 20000, 25000, 50000])
            elif violation_type == 'status':
                # Rule: status must not be 'suspended' or 'blocked'
                status = random.choice(['suspended', 'blocked'])
                loan_amount = random.uniform(1000, 9000)
            else:  # role
                # Rule: user_role must not be 'admin' or 'superuser'
                role = random.choice(['admin', 'superuser'])
                loan_amount = random.uniform(1000, 9000)
                status = 'pending'

            payload = {
                "applicant_name": random.choice(APPLICANT_NAMES),
                "loan_amount": loan_amount,
                "applicant_role": role if violation_type == 'role' else 'customer',
                "status": status if violation_type == 'status' else 'pending'
            }

            violation_count += 1
            logger.info(f"Sending violation #{violation_count}: {violation_type}")

        else:
            # Create a compliant request
            payload = {
                "applicant_name": random.choice(APPLICANT_NAMES),
                "loan_amount": round(random.uniform(1000, 9000), 2),
                "applicant_role": "customer",
                "status": "pending"
            }

        # Send POST request
        with self.client.post(
            "/api/loans/apply",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
                if should_violate:
                    logger.debug(f"Violation request succeeded: {response.json()}")
            else:
                response.failure(f"Request failed: {response.status_code}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary when test completes."""
    if VIOLATION_RATE > 0:
        print(f"\n{'='*60}")
        print(f"EXPERIMENT 4 SUMMARY:")
        print(f"  Total Requests: {total_requests}")
        print(f"  Violations Sent: {violation_count}")
        print(f"  Expected Violation Rate: {VIOLATION_RATE*100:.1f}%")
        print(f"  Actual Violation Rate: {(violation_count/total_requests*100) if total_requests > 0 else 0:.1f}%")
        print(f"")
        print(f"  To verify detection, run:")
        print(f"  docker exec bpc4msa-postgres-1 psql -U bpc4msa -d audit_db \\")
        print(f"    -c \"SELECT COUNT(*) FROM audit_log WHERE event_type = 'ViolationDetected';\"")
        print(f"{'='*60}\n")
