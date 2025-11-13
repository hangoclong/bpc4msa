"""
Synchronous Compliance Service - Traditional SOA Approach
Single service that handles business logic, compliance validation, and audit logging synchronously.
All operations block the request until complete.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
import psycopg2
import psycopg2.extras
import json
import os
import time

app = FastAPI(title="Synchronous Compliance Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "audit_db"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres")
}

# Compliance rules
COMPLIANCE_RULES = {
    "max_amount": 1000000,
    "min_amount": 1000,
    "allowed_roles": ["customer", "manager", "admin"],
    "approved_statuses": ["pending", "approved", "rejected"]
}

# Models
class LoanApplication(BaseModel):
    loan_amount: float
    applicant_role: str
    credit_score: int
    employment_status: str
    status: str = "pending"

class Violation(BaseModel):
    rule_id: str
    rule_description: str
    violated_field: str
    violated_value: str

class LoanApplicationResponse(BaseModel):
    transaction_id: str
    status: str
    violations: List[Violation]
    processing_time_ms: float

# Database initialization
def init_db():
    """Initialize database tables"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Create audit log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log_sync (
                id SERIAL PRIMARY KEY,
                transaction_id VARCHAR(255) NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                loan_amount FLOAT,
                applicant_role VARCHAR(50),
                credit_score INTEGER,
                employment_status VARCHAR(50),
                status VARCHAR(50),
                violations JSONB,
                processing_time_ms FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

@app.on_event("startup")
async def startup_event():
    """Wait for DB and initialize"""
    max_retries = 30
    for i in range(max_retries):
        try:
            init_db()
            print("Synchronous Compliance Service started successfully")
            return
        except Exception as e:
            print(f"Waiting for database... ({i+1}/{max_retries})")
            time.sleep(2)
    print("Failed to connect to database after maximum retries")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "compliance-sync",
        "architecture": "synchronous",
        "timestamp": datetime.utcnow().isoformat()
    }

def validate_compliance(application: LoanApplication) -> List[Violation]:
    """
    SYNCHRONOUS compliance validation - BLOCKS the request
    This is the traditional approach where validation happens inline
    """
    violations = []

    # Rule 1: Loan amount limits
    if application.loan_amount > COMPLIANCE_RULES["max_amount"]:
        violations.append(Violation(
            rule_id="RULE_001",
            rule_description=f"Loan amount exceeds maximum allowed ({COMPLIANCE_RULES['max_amount']})",
            violated_field="loan_amount",
            violated_value=str(application.loan_amount)
        ))

    if application.loan_amount < COMPLIANCE_RULES["min_amount"]:
        violations.append(Violation(
            rule_id="RULE_002",
            rule_description=f"Loan amount below minimum required ({COMPLIANCE_RULES['min_amount']})",
            violated_field="loan_amount",
            violated_value=str(application.loan_amount)
        ))

    # Rule 2: Role validation
    if application.applicant_role not in COMPLIANCE_RULES["allowed_roles"]:
        violations.append(Violation(
            rule_id="RULE_003",
            rule_description=f"Invalid applicant role. Allowed: {COMPLIANCE_RULES['allowed_roles']}",
            violated_field="applicant_role",
            violated_value=application.applicant_role
        ))

    # Rule 3: Credit score validation
    if application.credit_score < 600:
        violations.append(Violation(
            rule_id="RULE_004",
            rule_description="Credit score below minimum threshold (600)",
            violated_field="credit_score",
            violated_value=str(application.credit_score)
        ))

    # Rule 4: Status validation
    if application.status not in COMPLIANCE_RULES["approved_statuses"]:
        violations.append(Violation(
            rule_id="RULE_005",
            rule_description=f"Invalid status. Allowed: {COMPLIANCE_RULES['approved_statuses']}",
            violated_field="status",
            violated_value=application.status
        ))

    return violations

def write_audit_log(transaction_id: str, application: LoanApplication,
                   violations: List[Violation], processing_time_ms: float) -> None:
    """
    SYNCHRONOUS audit logging - BLOCKS the request
    Traditional approach: write to database immediately and wait for confirmation
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Convert violations to JSON
        violations_json = [v.dict() for v in violations]

        cursor.execute("""
            INSERT INTO audit_log_sync
            (transaction_id, event_type, timestamp, loan_amount, applicant_role,
             credit_score, employment_status, status, violations, processing_time_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            transaction_id,
            "LoanApplicationProcessed",
            datetime.utcnow(),
            application.loan_amount,
            application.applicant_role,
            application.credit_score,
            application.employment_status,
            application.status,
            psycopg2.extras.Json(violations_json),
            processing_time_ms
        ))

        conn.commit()
    except Exception as e:
        print(f"Audit log error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

@app.post("/api/loans/apply", response_model=LoanApplicationResponse)
async def apply_for_loan(application: LoanApplication):
    """
    SYNCHRONOUS loan application processing
    All operations happen sequentially and block the response:
    1. Generate transaction ID
    2. Validate compliance (BLOCKING)
    3. Write audit log (BLOCKING)
    4. Return response

    This simulates traditional SOA where all operations complete before responding.
    """
    start_time = time.time()

    # Generate transaction ID
    transaction_id = f"SYNC_{uuid.uuid4().hex[:8].upper()}"

    try:
        # BLOCKING: Synchronous compliance validation
        violations = validate_compliance(application)

        # Determine final status
        final_status = "rejected" if violations else "approved"

        # Calculate processing time so far
        processing_time_ms = (time.time() - start_time) * 1000

        # BLOCKING: Synchronous audit logging
        write_audit_log(transaction_id, application, violations, processing_time_ms)

        # Final processing time
        total_processing_time_ms = (time.time() - start_time) * 1000

        return LoanApplicationResponse(
            transaction_id=transaction_id,
            status=final_status,
            violations=violations,
            processing_time_ms=total_processing_time_ms
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )

@app.get("/api/stats")
async def get_stats():
    """Get processing statistics"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_transactions,
                AVG(processing_time_ms) as avg_processing_time_ms,
                MAX(processing_time_ms) as max_processing_time_ms,
                MIN(processing_time_ms) as min_processing_time_ms,
                COUNT(CASE WHEN jsonb_array_length(violations) > 0 THEN 1 END) as total_violations
            FROM audit_log_sync
        """)

        row = cursor.fetchone()

        return {
            "architecture": "synchronous",
            "total_transactions": row[0] or 0,
            "avg_processing_time_ms": float(row[1]) if row[1] else 0.0,
            "max_processing_time_ms": float(row[2]) if row[2] else 0.0,
            "min_processing_time_ms": float(row[3]) if row[3] else 0.0,
            "total_violations": row[4] or 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
