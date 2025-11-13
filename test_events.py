#!/usr/bin/env python3
"""
Test script to send events to Kafka and verify compliance and audit services.
"""
import json
from kafka import KafkaProducer
from datetime import datetime
import time

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("🚀 Sending test events to Kafka...")

# Test 1: Valid event (should pass compliance)
valid_event = {
    "event_type": "TransactionCreated",
    "timestamp": datetime.utcnow().isoformat(),
    "transaction_id": "TXN001",
    "amount": 5000,
    "status": "pending",
    "user_role": "customer"
}

print(f"\n✅ Sending valid event: {valid_event}")
producer.send('business-events', valid_event)

time.sleep(1)

# Test 2: Event with forbidden status (should trigger RULE001)
forbidden_status_event = {
    "event_type": "TransactionCreated",
    "timestamp": datetime.utcnow().isoformat(),
    "transaction_id": "TXN002",
    "amount": 3000,
    "status": "suspended",  # Violates RULE001
    "user_role": "customer"
}

print(f"\n❌ Sending event with forbidden status: {forbidden_status_event}")
producer.send('business-events', forbidden_status_event)

time.sleep(1)

# Test 3: Event with amount out of range (should trigger RULE002)
excessive_amount_event = {
    "event_type": "TransactionCreated",
    "timestamp": datetime.utcnow().isoformat(),
    "transaction_id": "TXN003",
    "amount": 15000,  # Violates RULE002 (max 10000)
    "status": "pending",
    "user_role": "customer"
}

print(f"\n❌ Sending event with excessive amount: {excessive_amount_event}")
producer.send('business-events', excessive_amount_event)

time.sleep(1)

# Test 4: Event with forbidden user role (should trigger RULE003)
forbidden_role_event = {
    "event_type": "TransactionCreated",
    "timestamp": datetime.utcnow().isoformat(),
    "transaction_id": "TXN004",
    "amount": 2000,
    "status": "pending",
    "user_role": "admin"  # Violates RULE003
}

print(f"\n❌ Sending event with forbidden role: {forbidden_role_event}")
producer.send('business-events', forbidden_role_event)

time.sleep(1)

# Test 5: Multiple violations in one event
multi_violation_event = {
    "event_type": "TransactionCreated",
    "timestamp": datetime.utcnow().isoformat(),
    "transaction_id": "TXN005",
    "amount": 20000,  # Violates RULE002
    "status": "blocked",  # Violates RULE001
    "user_role": "superuser"  # Violates RULE003
}

print(f"\n❌❌❌ Sending event with multiple violations: {multi_violation_event}")
producer.send('business-events', multi_violation_event)

producer.flush()
producer.close()

print("\n✨ All test events sent!")
print("\n📋 Next steps:")
print("   1. Check compliance-service logs: docker-compose logs compliance-service")
print("   2. Check audit-service logs: docker-compose logs audit-service")
print("   3. Query audit_log table to verify events were logged")
