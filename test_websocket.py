#!/usr/bin/env python3
"""
Test WebSocket client to verify real-time event broadcasting.
"""
import asyncio
import websockets
import json
from kafka import KafkaProducer
from datetime import datetime
import time

async def test_websocket_client():
    """Connect to WebSocket server and listen for events."""
    uri = "ws://localhost:8765"

    print(f"🔌 Connecting to WebSocket server at {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            print("📡 Listening for events...\n")

            event_count = 0
            # Listen for 10 seconds or 5 events, whichever comes first
            timeout = 10
            max_events = 5

            try:
                async with asyncio.timeout(timeout):
                    while event_count < max_events:
                        message = await websocket.recv()
                        event_count += 1

                        data = json.loads(message)
                        print(f"📨 Event #{event_count} received:")
                        print(f"   Topic: {data['topic']}")
                        print(f"   Type: {data['event'].get('event_type', 'N/A')}")
                        print(f"   Timestamp: {data['event'].get('timestamp', 'N/A')}")
                        if data['topic'] == 'violations':
                            print(f"   Violations: {len(data['event'].get('violations', []))}")
                        print()

            except TimeoutError:
                print(f"\n⏱️  Timeout reached after {timeout} seconds")

            print(f"✅ Received {event_count} events total")

    except ConnectionRefusedError:
        print("❌ Could not connect to WebSocket server. Is it running?")
    except Exception as e:
        print(f"❌ Error: {e}")

def send_test_events():
    """Send some test events to Kafka."""
    print("📤 Sending test events to Kafka...\n")

    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    events = [
        {
            "event_type": "TransactionCreated",
            "timestamp": datetime.utcnow().isoformat(),
            "transaction_id": "WS_TEST_001",
            "amount": 500,
            "status": "pending",
            "user_role": "customer"
        },
        {
            "event_type": "TransactionCreated",
            "timestamp": datetime.utcnow().isoformat(),
            "transaction_id": "WS_TEST_002",
            "amount": 25000,  # Violates RULE002
            "status": "pending",
            "user_role": "customer"
        },
        {
            "event_type": "TransactionCreated",
            "timestamp": datetime.utcnow().isoformat(),
            "transaction_id": "WS_TEST_003",
            "amount": 100,
            "status": "suspended",  # Violates RULE001
            "user_role": "admin"  # Violates RULE003
        }
    ]

    for event in events:
        producer.send('business-events', event)
        print(f"✉️  Sent: {event['transaction_id']}")
        time.sleep(0.5)

    producer.flush()
    producer.close()
    print("\n✅ All test events sent\n")

async def main():
    """Main test flow."""
    print("🧪 WebSocket Service Test\n")
    print("=" * 60)

    # Start WebSocket client in background
    client_task = asyncio.create_task(test_websocket_client())

    # Wait a moment for connection
    await asyncio.sleep(1)

    # Send test events from main thread
    await asyncio.to_thread(send_test_events)

    # Wait for client to finish
    await client_task

    print("=" * 60)
    print("✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(main())
