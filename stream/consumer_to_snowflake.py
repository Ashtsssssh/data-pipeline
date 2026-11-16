"""
stream/consumer_to_snowflake.py
BONUS — Stream into the Lakehouse.

Receives FreshCart-style order messages from RabbitMQ for 60 seconds,
writes them as a raw JSON file using write_landing(), then calls the
load + transform SQL so the streamed orders reach gold.fct_orders.

Usage:
    python stream/consumer_to_snowflake.py

Environment variables (use .env file — never commit):
    AMQP_URL            RabbitMQ connection URL
    SNOWFLAKE_ACCOUNT   e.g. abc12345.us-east-1
    SNOWFLAKE_USER
    SNOWFLAKE_PASSWORD
    SNOWFLAKE_DATABASE  (default: FRESHCART)
    SNOWFLAKE_WAREHOUSE (default: COMPUTE_WH)
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pika

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
AMQP_URL        = os.getenv("AMQP_URL", "amqp://guest:guest@localhost/")
EXCHANGE        = "rapido-dispatch"
LISTEN_SECONDS  = 60
LANDING_DIR     = Path("elt/stream_landing")
LANDING_DIR.mkdir(parents=True, exist_ok=True)

# Snowflake — imported lazily so the script is usable without the connector
SF_ACCOUNT   = os.getenv("SNOWFLAKE_ACCOUNT", "")
SF_USER      = os.getenv("SNOWFLAKE_USER", "")
SF_PASSWORD  = os.getenv("SNOWFLAKE_PASSWORD", "")
SF_DATABASE  = os.getenv("SNOWFLAKE_DATABASE", "FRESHCART")
SF_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")

collected_orders = []


# ---------------------------------------------------------------------------
# Step 1 — Collect messages from RabbitMQ for LISTEN_SECONDS
# ---------------------------------------------------------------------------
def collect_messages():
    """Listen on rapido-dispatch for LISTEN_SECONDS and collect JSON bodies."""
    params = pika.URLParameters(AMQP_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    result = channel.queue_declare(queue="", exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=EXCHANGE, queue=queue_name, routing_key="#")

    deadline = time.time() + LISTEN_SECONDS
    print(f"[consumer] Collecting messages for {LISTEN_SECONDS}s ...")

    while time.time() < deadline:
        method, props, body = channel.basic_get(queue=queue_name, auto_ack=True)
        if body:
            try:
                msg = json.loads(body)
                # Map RabbitMQ fields → FreshCart order schema
                order = {
                    "order_id":    msg.get("id", str(uuid.uuid4())),
                    "customer_id": f"CUST-{msg.get('zone', 'UNK')[:3].upper()}",
                    "amount":      round(100 + 900 * (hash(msg.get("id", "")) % 100) / 100, 2),
                    "currency":    "INR",
                    "order_date":  msg.get("ts", datetime.now(timezone.utc).isoformat()),
                    "source":      "stream",
                    "city":        msg.get("city", "unknown"),
                    "zone":        msg.get("zone", "unknown"),
                    "type":        msg.get("type", "ride"),
                }
                collected_orders.append(order)
                print(f"  [consumer] Captured order {order['order_id'][:8]} "
                      f"city={order['city']} zone={order['zone']}")
            except Exception as e:
                print(f"  [consumer] Skipped bad message: {e}")
        else:
            time.sleep(0.5)

    connection.close()
    print(f"[consumer] Collected {len(collected_orders)} orders.")


# ---------------------------------------------------------------------------
# Step 2 — write_landing(): save as a raw JSON file in the stage directory
# ---------------------------------------------------------------------------
def write_landing():
    if not collected_orders:
        print("[consumer] No orders to write.")
        return None

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    file_path = LANDING_DIR / f"stream_orders_{ts}.json"
    with open(file_path, "w") as f:
        json.dump(collected_orders, f, indent=2)
    print(f"[consumer] Written {len(collected_orders)} orders → {file_path}")
    return file_path


# ---------------------------------------------------------------------------
# Step 3 — load_file(): PUT the file to Snowflake stage and COPY INTO bronze
# ---------------------------------------------------------------------------
LOAD_SQL = """
-- Step 3a: PUT file to internal stage
-- (run separately: PUT file:///{file_path} @%BRONZE.ORDERS_RAW)

-- Step 3b: COPY INTO bronze (idempotent — Snowflake tracks loaded files)
COPY INTO BRONZE.ORDERS_RAW
FROM @%BRONZE.ORDERS_RAW
FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE)
ON_ERROR = 'CONTINUE';
"""

TRANSFORM_SQL = """
-- Re-run the transform chain (same SQL as the notebook — idempotent via MERGE)
CALL SILVER.PROC_ORDERS_CLEAN();
CALL SILVER.PROC_ORDERS_DEDUP();
CALL DIM.PROC_CUSTOMERS_SCD2();
CALL GOLD.PROC_FCT_ORDERS();    -- uses MERGE on row_hash → no double-counting
"""


def load_file(file_path):
    """PUT the landing file to Snowflake and COPY INTO bronze."""
    if not SF_ACCOUNT:
        print("[consumer] Snowflake credentials not set — skipping load_file().")
        print(f"[consumer] Manually PUT {file_path} and run:\n{LOAD_SQL}")
        return

    import snowflake.connector
    conn = snowflake.connector.connect(
        account=SF_ACCOUNT, user=SF_USER, password=SF_PASSWORD,
        database=SF_DATABASE, warehouse=SF_WAREHOUSE,
    )
    cs = conn.cursor()

    # PUT the file
    put_cmd = f"PUT file:///{file_path.resolve()} @%BRONZE.ORDERS_RAW AUTO_COMPRESS=TRUE"
    print(f"[consumer] {put_cmd}")
    cs.execute(put_cmd)

    # COPY INTO bronze
    copy_cmd = (
        "COPY INTO BRONZE.ORDERS_RAW FROM @%BRONZE.ORDERS_RAW "
        "FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE) ON_ERROR = 'CONTINUE'"
    )
    cs.execute(copy_cmd)
    print("[consumer] COPY INTO bronze complete.")

    # Run transform chain
    for stmt in TRANSFORM_SQL.strip().split("\n"):
        stmt = stmt.strip()
        if stmt and not stmt.startswith("--"):
            cs.execute(stmt)
            print(f"[consumer] Executed: {stmt}")

    cs.close()
    conn.close()
    print("[consumer] Gold table updated. Running the batch twice will NOT double gold totals")
    print("           because gold.PROC_FCT_ORDERS uses MERGE ON order_id matching row_hash.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    collect_messages()
    file_path = write_landing()
    if file_path:
        load_file(file_path)
