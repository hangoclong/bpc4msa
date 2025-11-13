"""
Steady-State Workload for Single-Instance Performance Comparison
Phase 1 Experimental Protocol

Goal: Generate realistic, sustained load for baseline performance measurement
Workload: 90% valid loan applications, 10% policy violations
Pattern: Human-like behavior with think time

Configuration:
- User wait time: 1-3 seconds (realistic think time)
- Request mix: Balanced between valid and violation scenarios
- Designed for load levels: 50, 100, 200, 400 concurrent users
"""

import random
import time
from locust import HttpUser, task, between

class SteadyStateUser(HttpUser):
    """
    Simulates a user applying for loans with realistic behavior patterns.

    This workload is designed for steady-state performance measurement,
    NOT for spike testing or stress testing.
    """

    # Realistic think time between requests (human-like behavior)
    wait_time = between(1, 3)

    # Sample applicant names for variety
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily",
                   "Robert", "Lisa", "James", "Maria", "William", "Anna"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martinez", "Wilson", "Anderson"]

    @task(9)  # 90% of requests
    def apply_loan_valid(self):
        """
        Submit a valid loan application that should pass compliance checks.

        Valid criteria:
        - Loan amount: 1,000 - 9,000 (within limit)
        - Credit score: 650+ (good)
        - Employment: employed or self-employed
        - Role: customer (valid)
        - Status: pending (correct initial state)
        """

        # Generate realistic applicant data
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        applicant_name = f"{first_name} {last_name}"

        payload = {
            "applicant_name": applicant_name,
            "loan_amount": random.randint(1000, 9000),  # Within policy limit
            "applicant_role": "customer",
            "credit_score": random.randint(650, 850),  # Good to excellent
            "employment_status": random.choice(["employed", "self-employed"]),
            "status": "pending"
        }

        # Submit application
        with self.client.post(
            "/api/loans/apply",
            json=payload,
            catch_response=True,
            name="POST /api/loans/apply (Valid)"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    @task(1)  # 10% of requests
    def apply_loan_violation(self):
        """
        Submit a loan application that violates compliance policies.

        Purpose: Test BPC4MSA's compliance service handling.

        Violation scenarios (randomly selected):
        1. Loan amount too high (>10,000)
        2. Low credit score (<600)
        3. Unemployed applicant
        4. Invalid role (admin/manager attempting customer transaction)
        """

        # Generate violation scenario
        violation_type = random.choice([
            "high_amount",
            "low_credit",
            "unemployed",
            "invalid_role"
        ])

        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        applicant_name = f"{first_name} {last_name}"

        if violation_type == "high_amount":
            # Violation: Loan amount exceeds policy limit
            payload = {
                "applicant_name": applicant_name,
                "loan_amount": random.randint(10001, 50000),  # Over limit
                "applicant_role": "customer",
                "credit_score": random.randint(650, 850),
                "employment_status": "employed",
                "status": "pending"
            }

        elif violation_type == "low_credit":
            # Violation: Credit score below threshold
            payload = {
                "applicant_name": applicant_name,
                "loan_amount": random.randint(1000, 9000),
                "applicant_role": "customer",
                "credit_score": random.randint(300, 599),  # Poor credit
                "employment_status": "employed",
                "status": "pending"
            }

        elif violation_type == "unemployed":
            # Violation: Unemployed applicant
            payload = {
                "applicant_name": applicant_name,
                "loan_amount": random.randint(1000, 9000),
                "applicant_role": "customer",
                "credit_score": random.randint(650, 850),
                "employment_status": "unemployed",
                "status": "pending"
            }

        else:  # invalid_role
            # Violation: Invalid role for transaction
            payload = {
                "applicant_name": applicant_name,
                "loan_amount": random.randint(1000, 9000),
                "applicant_role": random.choice(["admin", "manager"]),  # Invalid
                "credit_score": random.randint(650, 850),
                "employment_status": "employed",
                "status": "pending"
            }

        # Submit application (may be rejected)
        with self.client.post(
            "/api/loans/apply",
            json=payload,
            catch_response=True,
            name="POST /api/loans/apply (Violation)"
        ) as response:
            # Accept any response (200, 400, etc.) as "success" for load testing
            # We're measuring performance, not business logic correctness
            if response.status_code in [200, 400, 422]:
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")


# Run configuration (for command-line execution)
# Example usage:
#
# locust -f locustfile_steady_state.py --headless \
#        -u 50 --spawn-rate 75 --run-time 180s \
#        --host=http://localhost:8000 \
#        --csv steady_state_results \
#        --only-summary
#
# Parameters:
#   -u: Number of concurrent users (50, 100, 200, 400)
#   --spawn-rate: Users spawned per second (users * 1.5)
#   --run-time: Test duration (180s = 3 minutes)
#   --host: Target architecture endpoint
#   --csv: Output file prefix for results
#   --only-summary: Suppress verbose output
