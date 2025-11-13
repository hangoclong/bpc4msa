import json
import os
import time
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RULES_FILE = os.getenv("RULES_FILE", "/app/config/rules.json")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_EVENTS_TOPIC = os.getenv("KAFKA_EVENTS_TOPIC", "business-events")
KAFKA_VIOLATIONS_TOPIC = os.getenv("KAFKA_VIOLATIONS_TOPIC", "violations")
RULES_CHECK_INTERVAL = int(os.getenv("RULES_CHECK_INTERVAL", "10"))

class ComplianceService:
    def __init__(self):
        self.rules = []
        self.rules_mtime = 0
        self.consumer = None
        self.producer = None

    def load_rules(self):
        """Load rules from rules.json file."""
        try:
            if os.path.exists(RULES_FILE):
                current_mtime = os.path.getmtime(RULES_FILE)
                if current_mtime != self.rules_mtime:
                    with open(RULES_FILE, 'r') as f:
                        self.rules = json.load(f)
                    self.rules_mtime = current_mtime
                    logger.info(f"Loaded {len(self.rules)} rules from {RULES_FILE}")
            else:
                logger.warning(f"Rules file {RULES_FILE} not found")
        except Exception as e:
            logger.error(f"Error loading rules: {e}")

    def check_event(self, event):
        """Check if event violates any compliance rules."""
        violations = []

        for rule in self.rules:
            rule_type = rule.get("type")

            if rule_type == "field_value":
                # Check if a field has a forbidden value
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
                # Check if a numeric field is outside allowed range
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

    def publish_violation(self, event, violations):
        """Publish violation event to Kafka."""
        try:
            violation_event = {
                "event_type": "ViolationDetected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "transaction_id": event.get("transaction_id"),
                "architecture": event.get("architecture"),
                "original_event": event,
                "violations": violations
            }

            self.producer.send(
                KAFKA_VIOLATIONS_TOPIC,
                json.dumps(violation_event).encode('utf-8')
            )
            self.producer.flush()
            logger.info(f"Published violation for transaction {event.get('transaction_id')}")
        except Exception as e:
            logger.error(f"Error publishing violation: {e}")

    def run(self):
        """Main service loop."""
        logger.info("Starting Compliance Service...")

        # Initialize Kafka consumer
        self.consumer = KafkaConsumer(
            KAFKA_EVENTS_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='compliance-service',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        logger.info(f"Connected to Kafka, consuming from {KAFKA_EVENTS_TOPIC}")

        # Initialize Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            api_version=(0, 10, 1)
        )
        logger.info(f"Producer ready to publish to {KAFKA_VIOLATIONS_TOPIC}")

        # Load initial rules
        self.load_rules()

        last_rules_check = time.time()

        # Main event loop
        for message in self.consumer:
            # Periodically reload rules
            if time.time() - last_rules_check > RULES_CHECK_INTERVAL:
                self.load_rules()
                last_rules_check = time.time()

            event = message.value
            logger.debug(f"Processing event: {event}")

            # Check for violations
            violations = self.check_event(event)

            if violations:
                self.publish_violation(event, violations)

if __name__ == "__main__":
    service = ComplianceService()
    service.run()
