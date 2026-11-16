"""
stream/dispatcher.py
Part D — Food-order stream dispatcher using RabbitMQ topic exchange.

Usage:
    python stream/dispatcher.py [--url AMQP_URL]

Publishes a JSON order message every 2 seconds to the 'rapido-dispatch'
topic exchange. Routing key format: <city>.<zone>.<type>
Every 10th message is intentionally bad (missing 'zone' field) for D3.

Environment:
    AMQP_URL  — RabbitMQ connection URL (default: amqp://guest:guest@localhost/)
                Set via .env or environment variable. Never commit credentials.
"""

import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

import pika

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
AMQP_URL   = os.getenv("AMQP_URL", "amqp://guest:guest@localhost/")
EXCHANGE   = "rapido-dispatch"
INTERVAL   = 2        # seconds between messages
BAD_EVERY  = 10       # send one bad (zone-less) message every N messages

CITIES = {
    "bangalore": ["koramangala", "indiranagar", "whitefield", "tnagar"],
    "chennai":   ["tnagar", "anna_nagar", "velachery"],
}
TYPES = ["ride", "food"]


def build_routing_key(city: str, zone: str, order_type: str) -> str:
    return f"{city}.{zone}.{order_type}"


def connect(url: str) -> pika.BlockingConnection:
    params = pika.URLParameters(url)
    params.heartbeat = 60
    return pika.BlockingConnection(params)


def main():
    print(f"[dispatcher] Connecting to {AMQP_URL} ...")
    connection = connect(AMQP_URL)
    channel = connection.channel()

    # Declare a durable topic exchange
    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type="topic",
        durable=True,
    )
    print(f"[dispatcher] Exchange '{EXCHANGE}' ready. Sending orders every {INTERVAL}s.")
    print(f"[dispatcher] Every {BAD_EVERY}th message will be intentionally bad (D3).\n")

    counter = 0
    try:
        while True:
            counter += 1
            city = random.choice(list(CITIES.keys()))
            zone = random.choice(CITIES[city])
            order_type = random.choice(TYPES)

            # --- D3: inject a bad message (missing 'zone') every BAD_EVERY msgs ---
            if counter % BAD_EVERY == 0:
                message = {
                    "id":   str(uuid.uuid4()),
                    "city": city,
                    # 'zone' deliberately omitted
                    "type": order_type,
                    "ts":   datetime.now(timezone.utc).isoformat(),
                    "_bad": True,
                }
                routing_key = f"{city}.MISSING.{order_type}"
                print(f"[dispatcher] BAD msg #{counter}  key={routing_key}  (no zone field)")
            else:
                message = {
                    "id":   str(uuid.uuid4()),
                    "city": city,
                    "zone": zone,
                    "type": order_type,
                    "ts":   datetime.now(timezone.utc).isoformat(),
                }
                routing_key = build_routing_key(city, zone, order_type)
                print(f"[dispatcher] msg #{counter:>4}  key={routing_key:<35}  id={message['id'][:8]}")

            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,          # persistent
                    content_type="application/json",
                ),
            )
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\n[dispatcher] Stopped.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
