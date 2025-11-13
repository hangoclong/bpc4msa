import asyncio
import json
import os
from kafka import KafkaConsumer
import websockets
import logging
from threading import Thread

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPICS = os.getenv("KAFKA_TOPICS", "business-events,violations").split(",")
WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
WEBSOCKET_PORT = int(os.getenv("WEBSOCKET_PORT", "8765"))

# Store all connected WebSocket clients
connected_clients = set()

# Message queue for passing events from Kafka consumer to WebSocket broadcaster
message_queue = asyncio.Queue()

async def handle_client(websocket):
    """Handle a new WebSocket client connection."""
    connected_clients.add(websocket)
    client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"Client connected: {client_info} (total: {len(connected_clients)})")

    try:
        # Keep connection alive and handle incoming messages if any
        async for message in websocket:
            logger.debug(f"Received message from {client_info}: {message}")
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_info}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client removed: {client_info} (total: {len(connected_clients)})")

async def broadcast_messages():
    """Broadcast messages from the queue to all connected clients."""
    while True:
        message = await message_queue.get()

        if connected_clients:
            # Broadcast to all connected clients
            websockets_to_remove = set()
            for websocket in connected_clients:
                try:
                    await websocket.send(message)
                except websockets.exceptions.ConnectionClosed:
                    websockets_to_remove.add(websocket)
                except Exception as e:
                    logger.error(f"Error sending to client: {e}")
                    websockets_to_remove.add(websocket)

            # Remove disconnected clients
            for websocket in websockets_to_remove:
                connected_clients.discard(websocket)

            if websockets_to_remove:
                logger.info(f"Removed {len(websockets_to_remove)} disconnected clients")

            logger.debug(f"Broadcasted message to {len(connected_clients)} clients")
        else:
            logger.debug("No connected clients, message not broadcasted")

def kafka_consumer_thread(loop):
    """Run Kafka consumer in a separate thread and feed messages to the queue."""
    logger.info("Starting Kafka consumer thread...")

    consumer = KafkaConsumer(
        *KAFKA_TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='latest',  # Only consume new messages
        enable_auto_commit=True,
        group_id='socket-service',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    logger.info(f"Kafka consumer connected to topics: {KAFKA_TOPICS}")

    for message in consumer:
        event = message.value
        topic = message.topic

        # Prepare message for broadcast
        broadcast_data = {
            "topic": topic,
            "event": event,
            "timestamp": event.get("timestamp", None)
        }

        logger.info(f"Received event from {topic}: {event.get('event_type', 'unknown')}")

        # Put message into queue (thread-safe)
        asyncio.run_coroutine_threadsafe(
            message_queue.put(json.dumps(broadcast_data)),
            loop
        )

async def main():
    """Main entry point for the WebSocket server."""
    logger.info(f"Starting WebSocket server on {WEBSOCKET_HOST}:{WEBSOCKET_PORT}")

    # Get the current event loop
    loop = asyncio.get_running_loop()

    # Start Kafka consumer in a separate thread, passing the event loop
    kafka_thread = Thread(target=kafka_consumer_thread, args=(loop,), daemon=True)
    kafka_thread.start()

    # Start the broadcaster
    broadcaster_task = asyncio.create_task(broadcast_messages())

    # Start WebSocket server
    async with websockets.serve(handle_client, WEBSOCKET_HOST, WEBSOCKET_PORT):
        logger.info(f"✓ WebSocket server running on ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
