# Part A — Git & CI/CD

## A2: Git Command Table

| Command | Where the change happens | What exactly happens? |
|---|---|---|
| `git init` | Working folder (creates `.git/`) | Initialises a new local repository by creating a hidden `.git/` directory; no files are staged or committed yet. |
| `git add train.py` | Staging area (index) | Copies the current snapshot of `train.py` into the index, marking it ready for the next commit. |
| `git commit -m "msg"` | Local repository | Saves everything in the staging area as a permanent snapshot (commit object) in `.git/objects/`; the remote is not touched. |
| `git remote add origin URL` | Local config (`.git/config`) | Writes a URL alias called `origin`; teaches Git where the remote lives but transfers no data. |
| `git push -u origin main` | Remote repository (GitHub) | Uploads local commits to GitHub and sets `origin/main` as the upstream branch. |
| `git pull origin main` | Local repo + Working folder | Fetches new commits from GitHub and merges them into the current branch. |

**After `git commit`, can your teammate see the code on GitHub?**  
No. `git commit` saves to your **local** repository only. The teammate can only see the code after `git push` transfers it to the remote.

---

## A3: CI Workflow

The workflow in `.github/workflows/ci.yml`:
- Triggers on every push to any branch
- Sets up Python 3.12
- Installs `requirements.txt`
- Runs `pytest tests/ -v --tb=short`

**Green run:** Default `test_size=0.2` → 120/30 split → all 3 tests pass ✓  
**Red run:** Change `test_size=0.3` → 105/45 split → `test_split_is_80_20` fails, `test_output_has_all_rows` still passes ✗

---

# Part B — FreshCart ELT

## B2: ORD-1003 Trace

### Bronze
Two raw records for `ORD-1003`:
- **Web record**: `order_id=ORD-1003`, `amount=NULL`, `source=web`
- **Mobile record**: `order_id=ORD-1003`, `amount=2100.00`, `source=mobile`, `updated_at=<later>`

Field names differ because the web and mobile APIs are independent systems with separate schema conventions — bronze stores them raw without normalisation.

### Silver (`SQL_10_ORDERS_CLEAN`)
Both records get unified columns via `COALESCE`:
```sql
COALESCE(raw.order_id, raw.id)           AS order_id
COALESCE(raw.amount, raw.amt, raw.total) AS amount
COALESCE(raw.currency, 'INR')            AS currency
```
Both records pass to `silver.orders_checked` (NULL amount on web record is not a quarantine condition for web-source orders).

### Deduplication (`SQL_20_ORDERS_DEDUP`)
```sql
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY order_id
    ORDER BY updated_at DESC NULLS LAST
) = 1
```
Mobile record has later `updated_at` → gets ROW_NUMBER=1 → survives.  
Web record gets ROW_NUMBER=2 → discarded.

### Gold
Surviving record: `amount=2100.00 INR`  
`amount_inr = 2100.00`  
`loyalty_points = FLOOR(2100.00 × multiplier)` where multiplier depends on customer's tier at `order_date`.

### ORD-1005 vs ORD-1001 (Priya's tier difference)
The join condition:
```sql
JOIN dim.customers_scd2 c
  ON o.customer_id = c.customer_id
 AND o.order_date BETWEEN c.effective_from AND COALESCE(c.effective_to, '9999-12-31')
```
ORD-1005's `order_date` falls in Priya's Gold tier period → 2× multiplier.  
ORD-1001's `order_date` falls in her Silver tier period → 1× multiplier.  
Different dates select different SCD2 rows.

---

## B3: Validation Rule — `unsupported_currency`

```sql
-- Add inside ARRAY_CONSTRUCT_COMPACT(...) in SQL_10_ORDERS_CLEAN:
IFF(currency NOT IN ('INR', 'USD'), 'unsupported_currency', NULL)
```

- ORD-1006 `reasons` **before**: e.g. `['missing_amount']`
- ORD-1006 `reasons` **after**: e.g. `['missing_amount', 'unsupported_currency']`
- **Gold total does not change** — ORD-1006 was already quarantined; adding a reason doesn't affect gold.
- **No second quarantine row** — the quarantine INSERT uses `WHERE order_id NOT IN (SELECT order_id FROM silver.orders_quarantine)`, preventing duplicates.

---

## B4: SCD2 Idempotency

**New event**: CUST-02 moves to Gold with `effective_from = 2026-08-15`

**Idempotency explanation:**  
`row_hash` is a deterministic hash of all business-significant columns. The `MERGE` on `gold.fct_orders` matches on `order_id` and only updates rows where `row_hash` changed — leaving untouched rows unchanged. Re-running the pipeline with identical data produces zero changes to gold. Bronze still grows by 8 rows per run because `COPY INTO bronze.orders_raw` loads fresh raw files each time without a deduplication guard at bronze level.

---

## B5: Quality Check — NULL `amount_inr`

```python
check_6 = session.sql("""
    SELECT COUNT(*) AS cnt
    FROM gold.fct_orders g
    JOIN silver.orders_dedup s ON g.order_id = s.order_id
    WHERE g.amount_inr IS NULL AND s.amount IS NOT NULL
""").collect()[0]["CNT"]
results.append(("NULL amount_inr despite non-null source amount", check_6))
if check_6 > 0:
    print(f"PROBLEM: {check_6} gold orders have NULL amount_inr but non-null source amount")
```

**ELT vs ETL:**  
ELT suits FreshCart because Snowflake's SQL engine handles transformations at scale far more efficiently than a separate ETL server. Loading raw data first (bronze) lets us reprocess with new business rules without re-extracting from APIs. ETL would still win when raw data contains PII (e.g. card numbers) that must be masked **before** landing in the cloud.

---

# Part C — Mage ML Pipeline

## C1: Pipeline Graph

```
load_iris ──► check_data_quality ──► prepare_data ──► train_model ──┬──► save_results
                                                                     └──► evaluate_model
```

**Block types:**
- `load_iris`: data_loader
- `check_data_quality`: transformer (custom, Part C4)
- `prepare_data`: transformer
- `train_model`: transformer
- `save_results`: data_exporter
- `evaluate_model`: data_exporter

## C2: Test-gate Table

| max_depth | Expected accuracy | Passes gate (≥0.90)? | CSV created? |
|---|---|---|---|
| 1 | ~0.67 | ✗ No | No |
| 2 | ~0.93 | ✓ Yes | Yes |
| 3 | ~0.97 | ✓ Yes | Yes |
| 4 | ~0.97 | ✓ Yes | Yes |
| 5 | ~0.97 | ✓ Yes | Yes |

**Gate explanation:** When `@test` raises `AssertionError`, Mage marks the block failed and skips all downstream blocks. `save_results` never runs → no bad CSV is ever created. This is safer than saving first because there is no window where a bad file exists on disk.

## C3: Evaluation Branch
`train_model` now has two downstream blocks: `save_results` AND `evaluate_model`. They run in parallel. `evaluate_model` prints the confusion matrix and per-class metrics without saving any file.

## C4: Custom Block
`check_data_quality` transformer:
- Tests: no null values (`test_no_nulls`), exactly 3 classes (`test_exactly_three_classes`)
- Placed between `load_iris` and `prepare_data`
- Catches data corruption early before any ML processing

---

# Part D — RabbitMQ Stream

## D1: Routing Table

| # | Routing key | Receiving queues | Reason |
|---|---|---|---|
| 1 | `bangalore.koramangala.food` | Ravi, Meena, Control | `koramangala.*`✓, `*.food`✓, `#`✓ |
| 2 | `bangalore.indiranagar.ride` | Priya, Arjun, Control | `indiranagar.*`✓, `*.ride`✓, `#`✓ |
| 3 | `bangalore.whitefield.ride` | Arjun, Control | `*.ride`✓, `#`✓ |
| 4 | `chennai.tnagar.food` | Karthik | literal match ✓ |
| 5 | `bangalore.whitefield.food` | Meena, Control | `*.food`✓, `#`✓ |
| 6 | `bangalore.koramangala` | Control only | `#` matches 1+ words; `*` patterns need 3 words |

**Q6 explanation:** `bangalore.koramangala` has only 2 words. Patterns with `*` require exactly one word per `*` — `bangalore.koramangala.*` needs a 3rd word. Only `bangalore.#` matches because `#` can match zero or more words.

## D3: ACK/NACK

**Crash before ACK:** RabbitMQ keeps the message unacknowledged. When the connection drops, it re-queues the message automatically — guaranteeing at-least-once delivery. The message is redelivered when the driver reconnects.

**`requeue=True` for always-bad messages:** Creates an infinite loop — the message is returned to the queue and immediately redelivered forever, consuming CPU and flooding logs (a "poison message"). `requeue=False` discards it (or sends to dead-letter exchange), breaking the loop.

---

# Integration Diagram

```
GitHub (freshcart-pipelines)
         │
         ▼ push
    GitHub Actions CI
    pytest tests/ ──→ green ✓ / red ✗
         │
    (on green)
    ┌────┴──────────────────────┐
    │                           │
    ▼                           ▼
Part B: Snowflake ELT      Part C: Mage ML
bronze→silver→gold         load→prepare→train→save
(MERGE idempotent)         (@test gates)
    │                           │
    └───────────┬───────────────┘
                │
                ▼
         Part D: RabbitMQ
         dispatcher → topic exchange → drivers
         ACK/NACK handling
                │
         BONUS: consumer writes
         streamed orders → gold.fct_orders
```

---

# Reflection
*(Fill in your own experience — e.g.:)*

**What broke:** The CI workflow failed on the first push because `scikit-learn` was missing from `requirements.txt`.  
**How I found it:** The GitHub Actions log showed `ModuleNotFoundError: No module named 'sklearn'`.  
**How I fixed it:** Added `scikit-learn>=1.3.0` to `requirements.txt`, committed with message `fix: add scikit-learn to requirements`, and pushed. The next run was green.
