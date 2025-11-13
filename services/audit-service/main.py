import json
import os
from kafka import KafkaConsumer
import psycopg2
from datetime import datetime
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPICS = os.getenv("KAFKA_TOPICS", "business-events,violations").split(",")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "bpc4msa")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "bpc4msa_pass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "audit_db")

class AuditService:
    def __init__(self):
        self.consumer = None
        self.db_conn = None

    def init_database(self):
        """Initialize PostgreSQL connection and create audit_log table if needed."""
        try:
            self.db_conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                database=POSTGRES_DB
            )
            self.db_conn.autocommit = True
            logger.info("Connected to PostgreSQL")

            # Create audit_log table
            cursor = self.db_conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    topic VARCHAR(255) NOT NULL,
                    event_type VARCHAR(255),
                    event_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.close()
            logger.info("Audit log table ready")

        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def log_event(self, topic, event):
        """Write event to audit_log table."""
        try:
            cursor = self.db_conn.cursor()

            # Extract event type if present
            event_type = event.get("event_type", None)

            # Get timestamp from event or use current time
            timestamp = event.get("timestamp", datetime.utcnow().isoformat())

            cursor.execute("""
                INSERT INTO audit_log (timestamp, topic, event_type, event_data)
                VALUES (%s, %s, %s, %s)
            """, (timestamp, topic, event_type, json.dumps(event)))

            cursor.close()
            logger.info(f"Logged event from {topic}: {event_type}")

        except Exception as e:
            logger.error(f"Error logging event: {e}")

    def run(self):
        """Main service loop."""
        logger.info("Starting Audit Service...")

        while True:  # Add a loop for resilience
            try:
                # Initialize database
                self.init_database()

                # Initialize Kafka consumer
                self.consumer = KafkaConsumer(
                    *KAFKA_TOPICS,
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    auto_offset_reset='earliest',
                    enable_auto_commit=True,
                    group_id='audit-service',
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    consumer_timeout_ms=30000  # Add a timeout
                )
                logger.info(f"Connected to Kafka, consuming from {KAFKA_TOPICS}")

                # Main event loop
                for message in self.consumer:
                    if message:
                        event = message.value
                        topic = message.topic
                        logger.debug(f"Received event from {topic}: {event}")
                        self.log_event(topic, event)

            except Exception as e:
                logger.error(f"An error occurred in the main loop: {e}")
                logger.info("Attempting to reconnect in 5 seconds...")
                if self.consumer:
                    self.consumer.close()
                if self.db_conn:
                    self.db_conn.close()
                time.sleep(5)


if __name__ == "__main__":
    service = AuditService()
    service.run()
