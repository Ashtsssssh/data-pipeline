"""
stream/driver.py
Part D — Food-order stream driver (consumer) using RabbitMQ topic exchange.

Usage:
    python stream/driver.py <NAME> <PATTERN> [--url AMQP_URL]

Examples:
    python stream/driver.py Ravi  "bangalore.koramangala.*"
    python stream/driver.py Meena "bangalore.*.food"
    python stream/driver.py Arjun "bangalore.*.ride"

Part D3 behaviour:
    - Messages missing the 'zone' field are NACK'd with requeue=False
      (they go to the dead-letter queue / are discarded).
    - All valid messages are ACK'd.

Environment:
    AMQP_URL  — RabbitMQ connection URL (default: amqp://guest:guest@localhost/)
"""

import json
import os
import sys
from datetime import datetime, timezone

import pika

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
AMQP_URL = os.getenv("AMQP_URL", "amqp://guest:guest@localhost/")
EXCHANGE  = "rapido-dispatch"


def connect(url: str) -> pika.BlockingConnection:
    params = pika.URLParameters(url)
    params.heartbeat = 60
    return pika.BlockingConnection(params)


def make_callback(driver_name: str):
    """Return a message-handler closure that knows the driver's name."""

    def on_message(ch, method, properties, body):
        try:
            msg = json.loads(body)
        except json.JSONDecodeError:
            # Malformed JSON — discard immediately
            print(f"[{driver_name}] ✗ Malformed JSON — NACK (discard)")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # -------------------------------------------------------------------
        # D3: reject messages that are missing the 'zone' field
        # -------------------------------------------------------------------
        if "zone" not in msg or msg.get("_bad"):
            print(
                f"[{driver_name}] ✗ BAD message (no 'zone') "
                f"id={msg.get('id', '?')[:8]} — NACK (discard, requeue=False)"
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # -------------------------------------------------------------------
        # Valid message — process and ACK
        # -------------------------------------------------------------------
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        print(
            f"[{driver_name}] ✓ ACK  "
            f"key={method.routing_key:<35}  "
            f"city={msg['city']}  zone={msg['zone']}  "
            f"type={msg['type']}  id={msg['id'][:8]}  received={now}"
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    return on_message


def main():
    if len(sys.argv) < 3:
        print("Usage: python stream/driver.py <NAME> <PATTERN>")
        print('Example: python stream/driver.py Ravi "bangalore.koramangala.*"')
        sys.exit(1)

    driver_name = sys.argv[1]
    pattern     = sys.argv[2]

    print(f"[{driver_name}] Connecting to {AMQP_URL} ...")
    connection = connect(AMQP_URL)
    channel = connection.channel()

    # Declare the same exchange (idempotent)
    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type="topic",
        durable=True,
    )

    # Declare an exclusive, auto-delete private queue for this driver
    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue

    # Bind the queue with the driver's routing pattern
    channel.queue_bind(
        exchange=EXCHANGE,
        queue=queue_name,
        routing_key=pattern,
    )

    # One message at a time (fair dispatch)
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=queue_name,
        on_message_callback=make_callback(driver_name),
    )

    print(f"[{driver_name}] Listening on exchange='{EXCHANGE}'  pattern='{pattern}'")
    print(f"[{driver_name}] Private queue: {queue_name}")
    print(f"[{driver_name}] Waiting for orders... (Ctrl+C to stop)\n")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(f"\n[{driver_name}] Stopped.")
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
