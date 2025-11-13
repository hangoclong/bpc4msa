"""
Monolithic BPMS Baseline - Traditional All-in-One Approach
Single monolithic service with layered architecture:
- Presentation Layer (API endpoints)
- Business Logic Layer (core processing)
- Compliance Layer (embedded rules)
- Data Access Layer (direct database)
All in one process, no external services.
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

app = FastAPI(title="Monolithic BPMS Baseline")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "audit_db"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres")
}

# Compliance rules embedded in the monolith
COMPLIANCE_RULES = {
    "max_amount": 1000000,
    "min_amount": 1000,
    "allowed_roles": ["customer", "manager", "admin"],
    "approved_statuses": ["pending", "approved", "rejected"],
    "min_credit_score": 600
}

# ============================================================================
# DATA MODELS (Shared across all layers)
# ============================================================================

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

# ============================================================================
# DATA ACCESS LAYER
# ============================================================================

class DataAccessLayer:
    """
    Direct database access layer
    Handles all database operations within the monolith
    """

    @staticmethod
    def init_database():
        """Initialize database schema"""
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Applications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS loan_applications (
                    id SERIAL PRIMARY KEY,
                    transaction_id VARCHAR(255) UNIQUE NOT NULL,
                    loan_amount FLOAT NOT NULL,
                    applicant_role VARCHAR(50) NOT NULL,
                    credit_score INTEGER NOT NULL,
                    employment_status VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Violations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_violations (
                    id SERIAL PRIMARY KEY,
                    transaction_id VARCHAR(255) NOT NULL,
                    rule_id VARCHAR(50) NOT NULL,
                    rule_description TEXT NOT NULL,
                    violated_field VARCHAR(100) NOT NULL,
                    violated_value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transaction_id) REFERENCES loan_applications(transaction_id)
                )
            """)

            # Audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log_mono (
                    id SERIAL PRIMARY KEY,
                    transaction_id VARCHAR(255) NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    processing_time_ms FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            print("Monolithic database initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    @staticmethod
    def save_application(transaction_id: str, application: LoanApplication,
                        violations: List[Violation], processing_time_ms: float):
        """
        Save application, violations, and audit in a SINGLE transaction
        This is the monolithic approach - everything in one database transaction
        """
        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Insert application
            cursor.execute("""
                INSERT INTO loan_applications
                (transaction_id, loan_amount, applicant_role, credit_score,
                 employment_status, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                transaction_id,
                application.loan_amount,
                application.applicant_role,
                application.credit_score,
                application.employment_status,
                "rejected" if violations else "approved"
            ))

            # Insert violations if any
            for violation in violations:
                cursor.execute("""
                    INSERT INTO compliance_violations
                    (transaction_id, rule_id, rule_description, violated_field, violated_value)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    transaction_id,
                    violation.rule_id,
                    violation.rule_description,
                    violation.violated_field,
                    violation.violated_value
                ))

            # Insert audit log
            cursor.execute("""
                INSERT INTO audit_log_mono
                (transaction_id, event_type, timestamp, processing_time_ms)
                VALUES (%s, %s, %s, %s)
            """, (
                transaction_id,
                "LoanApplicationProcessed",
                datetime.utcnow(),
                processing_time_ms
            ))

            # COMMIT SINGLE TRANSACTION - all or nothing
            conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_statistics():
        """Retrieve processing statistics"""
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
                    COUNT(DISTINCT cv.transaction_id) as total_violations
                FROM audit_log_mono a
                LEFT JOIN compliance_violations cv ON a.transaction_id = cv.transaction_id
            """)

            row = cursor.fetchone()
            return {
                "architecture": "monolithic",
                "total_transactions": row[0] or 0,
                "avg_processing_time_ms": float(row[1]) if row[1] else 0.0,
                "max_processing_time_ms": float(row[2]) if row[2] else 0.0,
                "min_processing_time_ms": float(row[3]) if row[3] else 0.0,
                "total_violations": row[4] or 0
            }
        except Exception as e:
            raise Exception(f"Statistics error: {str(e)}")
        finally:
            if conn:
                conn.close()

# ============================================================================
# COMPLIANCE LAYER
# ============================================================================

class ComplianceLayer:
    """
    Embedded compliance validation
    No external service - rules are part of the monolith
    """

    @staticmethod
    def check_compliance(application: LoanApplication) -> List[Violation]:
        """
        Validate application against embedded compliance rules
        This happens in-process, no network calls
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
        if application.credit_score < COMPLIANCE_RULES["min_credit_score"]:
            violations.append(Violation(
                rule_id="RULE_004",
                rule_description=f"Credit score below minimum threshold ({COMPLIANCE_RULES['min_credit_score']})",
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

# ============================================================================
# BUSINESS LOGIC LAYER
# ============================================================================

class BusinessLogicLayer:
    """
    Core business logic
    Orchestrates compliance checks and data persistence
    """

    @staticmethod
    def process_loan_application(application: LoanApplication) -> tuple[str, List[Violation], float]:
        """
        Process loan application through all layers
        Returns: (transaction_id, violations, processing_time_ms)
        """
        start_time = time.time()

        # Generate transaction ID
        transaction_id = f"MONO_{uuid.uuid4().hex[:8].upper()}"

        # Check compliance (in-process call)
        violations = ComplianceLayer.check_compliance(application)

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Persist everything in one transaction
        DataAccessLayer.save_application(
            transaction_id,
            application,
            violations,
            processing_time_ms
        )

        return transaction_id, violations, processing_time_ms

# ============================================================================
# PRESENTATION LAYER (API)
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    max_retries = 30
    for i in range(max_retries):
        try:
            DataAccessLayer.init_database()
            print("Monolithic BPMS started successfully")
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
        "service": "monolithic-bpms",
        "architecture": "monolithic",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/loans/apply", response_model=LoanApplicationResponse)
async def apply_for_loan(application: LoanApplication):
    """
    MONOLITHIC loan application processing
    All operations happen in-process:
    1. Validate compliance (in-memory)
    2. Process business logic (in-memory)
    3. Persist to database (single transaction)

    No external services, no network calls, everything in one process.
    """
    try:
        transaction_id, violations, processing_time_ms = \
            BusinessLogicLayer.process_loan_application(application)

        final_status = "rejected" if violations else "approved"

        return LoanApplicationResponse(
            transaction_id=transaction_id,
            status=final_status,
            violations=violations,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )

@app.get("/api/stats")
async def get_stats():
    """Get processing statistics"""
    try:
        return DataAccessLayer.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
