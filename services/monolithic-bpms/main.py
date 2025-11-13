"""
Monolithic BPMS Architecture
All-in-one business process management system with integrated compliance.

Key characteristics:
- Single service handles all business logic AND compliance
- No service boundaries - all processing in one codebase
- Direct function calls (no HTTP, no message broker)
- Tightly coupled - business logic and compliance in same process
- Same compliance rules as BPC4MSA for fair comparison
- Simpler deployment but less scalable

This represents traditional monolithic applications where all functionality
is bundled together in a single deployable unit.
"""

import os
import json
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from contextlib import asynccontextmanager

# Database connection
postgres_conn = None

# Load compliance rules (same as BPC4MSA)
RULES_FILE = "/app/config/rules.json"
compliance_rules = []

def load_compliance_rules():
    """Load compliance rules from JSON file"""
    global compliance_rules
    try:
        if os.path.exists(RULES_FILE):
            with open(RULES_FILE, 'r') as f:
                compliance_rules = json.load(f)
            print(f"✓ Loaded {len(compliance_rules)} compliance rules")
        else:
            print(f"⚠ Rules file {RULES_FILE} not found, using defaults")
            compliance_rules = [
                {
                    "id": "RULE001",
                    "type": "field_value",
                    "description": "Transaction status must not be 'suspended'",
                    "field": "status",
                    "forbidden_values": ["suspended", "blocked"]
                },
                {
                    "id": "RULE002",
                    "type": "field_range",
                    "description": "Transaction amount must be between 0 and 10000",
                    "field": "amount",
                    "min": 0,
                    "max": 10000
                },
                {
                    "id": "RULE003",
                    "type": "field_value",
                    "description": "User role must not be 'admin' for customer transactions",
                    "field": "user_role",
                    "forbidden_values": ["admin", "superuser"]
                }
            ]
    except Exception as e:
        print(f"✗ Error loading rules: {e}")
        compliance_rules = []

def check_compliance_inline(event):
    """
    Inline compliance check - direct function call within same process.
    No network overhead, no service boundaries.
    """
    violations = []

    for rule in compliance_rules:
        rule_type = rule.get("type")

        if rule_type == "field_value":
            field = rule.get("field")
            forbidden_values = rule.get("forbidden_values", [])

            if field in event and event[field] in forbidden_values:
                violations.append({
                    "rule_id": rule.get("id"),
                    "rule_description": rule.get("description"),
                    "violated_field": field,
                    "violated_value": event[field]
                })

        elif rule_type == "field_range":
            field = rule.get("field")
            min_value = rule.get("min")
            max_value = rule.get("max")

            if field in event:
                value = event[field]
                if (min_value is not None and value < min_value) or \
                   (max_value is not None and value > max_value):
                    violations.append({
                        "rule_id": rule.get("id"),
                        "rule_description": rule.get("description"),
                        "violated_field": field,
                        "violated_value": value
                    })

    return violations

def log_to_database(event_type, event_data):
    """Log event to PostgreSQL audit_log table"""
    try:
        if postgres_conn and not postgres_conn.closed:
            cursor = postgres_conn.cursor()
            # Extract timestamp from event data, default to now if not present
            event_timestamp = event_data.get('timestamp', datetime.now(timezone.utc).isoformat())

            cursor.execute(
                """
                INSERT INTO audit_log (timestamp, topic, event_type, event_data)
                VALUES (%s, %s, %s, %s)
                """,
                (event_timestamp, "mono-events", event_type, json.dumps(event_data))
            )
            postgres_conn.commit()
            cursor.close()
    except Exception as e:
        print(f"✗ Database logging error: {e}")

def process_loan_application_monolithic(application_data):
    """
    Monolithic processing - all business logic and compliance in one function.
    This represents the tightly-coupled nature of monolithic systems.
    """
    transaction_id = f"MONO_{uuid.uuid4().hex[:8].upper()}"

    # Step 1: Business logic - create transaction
    transaction_event = {
        "event_type": "TransactionCreated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "architecture": "monolithic",
        "transaction_id": transaction_id,
        "amount": application_data.get("loan_amount"),
        "status": application_data.get("status"),
        "user_role": application_data.get("applicant_role"),
        "applicant_name": application_data.get("applicant_name"),
        "credit_score": application_data.get("credit_score"),
        "employment_status": application_data.get("employment_status")
    }

    # Log transaction creation
    log_to_database("TransactionCreated", transaction_event)

    # Step 2: Compliance logic - inline check (direct function call)
    violations = check_compliance_inline(transaction_event)

    # Step 3: Log compliance result
    if violations:
        violation_event = {
            "event_type": "ViolationDetected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "architecture": "monolithic",
            "transaction_id": transaction_id,
            "violations": violations
        }
        log_to_database("ViolationDetected", violation_event)
    else:
        compliance_event = {
            "event_type": "CompliancePassed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "architecture": "monolithic",
            "transaction_id": transaction_id
        }
        log_to_database("CompliancePassed", compliance_event)

    # Step 4: Return result
    return {
        "transaction_id": transaction_id,
        "violations": violations,
        "status": "approved" if not violations else "rejected"
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize connections
    global postgres_conn

    # Load compliance rules
    load_compliance_rules()

    # Initialize PostgreSQL Connection
    try:
        postgres_conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            user=os.getenv("POSTGRES_USER", "monolithic"),
            password=os.getenv("POSTGRES_PASSWORD", "mono_pass"),
            database=os.getenv("POSTGRES_DB", "mono_db")
        )
        print(f"✓ Connected to PostgreSQL")
    except Exception as e:
        print(f"✗ Failed to connect to PostgreSQL: {e}")

    yield

    # Shutdown: Close connections
    if postgres_conn:
        postgres_conn.close()

app = FastAPI(title="Monolithic BPMS Service", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Loan Application Models
class LoanApplication(BaseModel):
    applicant_name: str
    loan_amount: float
    applicant_role: str = "customer"
    status: str = "pending"
    credit_score: int = 700
    employment_status: str = "employed"

class LoanApplicationResponse(BaseModel):
    transaction_id: str
    applicant_name: str
    loan_amount: float
    status: str
    message: str
    violations: list = []

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "service": "monolithic-bpms",
        "architecture": "monolithic",
        "postgres": "disconnected"
    }

    # Check PostgreSQL
    if postgres_conn and not postgres_conn.closed:
        try:
            cursor = postgres_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            status["postgres"] = "connected"
        except Exception as e:
            status["postgres"] = f"error: {str(e)}"

    return status

@app.get("/api/stats")
async def get_stats():
    """Get service statistics from database"""
    try:
        cursor = postgres_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM audit_log")
        total = cursor.fetchone()[0] or 0
        cursor.close()

        return {
            "architecture": "monolithic",
            "total_transactions": total,
            "avg_processing_time_ms": 0.0,
            "max_processing_time_ms": 0.0,
            "min_processing_time_ms": 0.0,
            "total_violations": 0
        }
    except Exception as e:
        return {
            "architecture": "monolithic",
            "total_transactions": 0,
            "avg_processing_time_ms": 0.0,
            "max_processing_time_ms": 0.0,
            "min_processing_time_ms": 0.0,
            "total_violations": 0
        }

@app.post("/api/loans/apply", response_model=LoanApplicationResponse)
async def apply_for_loan(application: LoanApplication):
    """
    Process loan application in monolithic style.

    Flow:
    1. Single function handles all processing
    2. Business logic and compliance are tightly coupled
    3. Direct function calls (no service boundaries)
    4. All logging happens inline
    5. Return response

    This represents traditional monolithic architecture where all components
    are part of the same codebase and deployment unit.
    """
    # Convert Pydantic model to dict for internal processing
    application_data = {
        "applicant_name": application.applicant_name,
        "loan_amount": application.loan_amount,
        "applicant_role": application.applicant_role,
        "status": application.status,
        "credit_score": application.credit_score,
        "employment_status": application.employment_status
    }

    # Process everything in one monolithic function
    result = process_loan_application_monolithic(application_data)

    return LoanApplicationResponse(
        transaction_id=result["transaction_id"],
        applicant_name=application.applicant_name,
        loan_amount=application.loan_amount,
        status=result["status"],
        message="Loan application processed monolithically",
        violations=result["violations"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
