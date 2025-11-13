import os
import json
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from kafka import KafkaProducer
import psycopg2
from contextlib import asynccontextmanager

app = FastAPI()

# Add CORS middleware to allow browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection instances
kafka_producer = None
postgres_conn = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize connections
    global kafka_producer, postgres_conn

    # Initialize Kafka Producer
    try:
        kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        kafka_producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            api_version=(0, 10, 1)
        )
        print(f"✓ Connected to Kafka at {kafka_bootstrap_servers}")
    except Exception as e:
        print(f"✗ Failed to connect to Kafka: {e}")

    # Initialize PostgreSQL Connection
    try:
        postgres_conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            user=os.getenv("POSTGRES_USER", "bpc4msa"),
            password=os.getenv("POSTGRES_PASSWORD", "bpc4msa_pass"),
            database=os.getenv("POSTGRES_DB", "audit_db")
        )
        print(f"✓ Connected to PostgreSQL")
    except Exception as e:
        print(f"✗ Failed to connect to PostgreSQL: {e}")

    yield

    # Shutdown: Close connections
    if kafka_producer:
        kafka_producer.close()
    if postgres_conn:
        postgres_conn.close()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Health check endpoint that verifies all connections."""
    status = {
        "status": "healthy",
        "kafka": "disconnected",
        "postgres": "disconnected"
    }

    # Check Kafka
    if kafka_producer:
        try:
            # Bootstrap check
            kafka_producer.bootstrap_connected()
            status["kafka"] = "connected"
        except Exception as e:
            status["kafka"] = f"error: {str(e)}"

    # Check PostgreSQL
    if postgres_conn and not postgres_conn.closed:
        try:
            cursor = postgres_conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            status["postgres"] = "connected"
        except Exception as e:
            status["postgres"] = f"error: {str(e)}"

    # Determine overall health
    if status["kafka"] == "connected" and status["postgres"] == "connected":
        return status
    else:
        status["status"] = "degraded"
        raise HTTPException(status_code=503, detail=status)

@app.get("/")
async def root():
    return {"message": "BPC4MSA Business Logic Service"}

# Loan Application Models
class LoanApplication(BaseModel):
    applicant_name: str
    loan_amount: float
    applicant_role: str = "customer"
    status: str = "pending"

class LoanApplicationResponse(BaseModel):
    transaction_id: str
    applicant_name: str
    loan_amount: float
    status: str
    message: str

@app.post("/api/loans/apply", response_model=LoanApplicationResponse)
async def apply_for_loan(application: LoanApplication):
    """
    Process a loan application and publish event to Kafka.
    This simulates the business logic service processing.
    """
    transaction_id = f"LOAN_{uuid.uuid4().hex[:8].upper()}"

    # Create event for Kafka
    event = {
        "event_type": "TransactionCreated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "architecture": "bpc4msa",
        "transaction_id": transaction_id,
        "amount": application.loan_amount,
        "status": application.status,
        "user_role": application.applicant_role,
        "applicant_name": application.applicant_name
    }

    # Publish to Kafka
    try:
        if kafka_producer:
            kafka_producer.send(
                'business-events',
                json.dumps(event).encode('utf-8')
            )
            kafka_producer.flush()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish event: {str(e)}")

    return LoanApplicationResponse(
        transaction_id=transaction_id,
        applicant_name=application.applicant_name,
        loan_amount=application.loan_amount,
        status=application.status,
        message="Loan application submitted successfully"
    )

@app.get("/api/stats")
async def get_stats():
    """Get transaction statistics from audit service"""
    try:
        cursor = postgres_conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM audit_log
        """)
        total = cursor.fetchone()[0] or 0

        return {
            "architecture": "bpc4msa",
            "total_transactions": total,
            "avg_processing_time_ms": 0,  # Would need to track this
            "max_processing_time_ms": 0,
            "min_processing_time_ms": 0,
            "total_violations": 0  # Would query compliance service
        }
    except Exception as e:
        return {
            "architecture": "bpc4msa",
            "total_transactions": 0,
            "avg_processing_time_ms": 0,
            "max_processing_time_ms": 0,
            "min_processing_time_ms": 0,
            "total_violations": 0
        }
