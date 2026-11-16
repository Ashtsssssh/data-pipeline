# Report: From Git to Gold
**Course:** Data Engineering | **Assignment:** Pipeline Orchestration  
**File to submit as:** `RollNo_Name_Pipelines.pdf`

---

## Part A: Git and CI/CD

### A2. Where Does Each Command Act?

| Command | Where the change happens | What exactly happens? |
|---|---|---|
| `git init` | **Working folder** (creates `.git/`) | Initialises a new local repository by creating a hidden `.git/` directory that will track all future changes; no files are staged or committed yet. |
| `git add train.py` | **Staging area (index)** | Copies the current snapshot of `train.py` from the working folder into the index, marking it as ready to be included in the next commit. |
| `git commit -m "msg"` | **Local repository** | Takes everything in the staging area and stores it as a permanent, numbered snapshot (commit object with SHA-1 hash) in the local `.git/objects/` store; the remote is not touched. |
| `git remote add origin URL` | **Local config only** | Writes a URL alias called `origin` into `.git/config`; it teaches Git where the remote is but does not transfer any data. |
| `git push -u origin main` | **Remote repository** | Uploads the local `main` branch's commits to the GitHub server and sets `origin/main` as the upstream tracking branch so future `git push` works without arguments. |
| `git pull origin main` | **Working folder + Local repo** | Fetches new commits from `origin/main` onto the local repo, then merges (or rebases) them into the current working branch, updating tracked files in the working folder. |

**After `git commit`, can your teammate see the code on GitHub?**  
No. `git commit` only saves the snapshot to the **local** repository (inside `.git/`). The code reaches GitHub only after `git push`. Until then, the commit exists solely on your machine.

---

### A3. CI Workflow Explanation

The `.github/workflows/ci.yml` runs on every push to any branch. It:
1. Checks out the repository with `actions/checkout@v4`
2. Sets up Python 3.12 with `actions/setup-python@v5`
3. Installs all dependencies from `requirements.txt`
4. Runs `pytest tests/ -v --tb=short`

**To trigger the red run:** Temporarily change `test_size=0.2` to `test_size=0.3` in `iris_project/transformers/prepare_data.py`. This makes the split 105/45 instead of 120/30, causing `test_split_is_80_20` to fail. Push, screenshot the red run, then revert and push again for the green run.

---

## Part B: FreshCart ELT on Snowflake

### B1. Baseline Numbers

> *Run the notebook and confirm these values match your Snowflake output.*

| Check | Expected | Your output |
|---|---|---|
| Raw order rows in bronze after one run | 8 (6 web + 2 mobile) | *(screenshot)* |
| Rows that pass cleaning (`silver.orders_clean`) | 6 | *(screenshot)* |
| Rows in quarantine | 2 (ORD-1004, ORD-1006) | *(screenshot)* |
| Orders after deduplication | 4 | *(screenshot)* |
| Final gold line | 4 orders, revenue 7,785.00, 126 loyalty points | *(screenshot)* |
| Share of rows rejected | 25% | *(screenshot)* |

---

### B2. Trace One Record by Hand

#### ORD-1003 Trace

**Step 1 — Bronze (`bronze.orders_raw`)**

ORD-1003 arrives **twice**:
- **Web record:** `order_id="ORD-1003"`, `amount=NULL`, `source="web"` — the web API omits `amount` for pending orders and uses field names `order_id`, `customer_id`, `amount`, `currency`, `order_date`.
- **Mobile record:** `order_id="ORD-1003"`, `amount=2100.00`, `source="mobile"`, `updated_at=<later timestamp>` — the mobile API uses slightly different field names (`amt` or snake_case variants), which is why the `COALESCE` and aliasing expressions exist in `SQL_10_ORDERS_CLEAN`.

The field names differ because the web and mobile APIs are independent systems with separate schema conventions; bronze loads them raw without normalisation.

**Step 2 — Silver (`silver.orders_checked`)**

`SQL_10_ORDERS_CLEAN` unifies field names:
```sql
COALESCE(raw.order_id, raw.id)           AS order_id,
COALESCE(raw.amount, raw.amt, raw.total) AS amount,
COALESCE(raw.currency, 'INR')            AS currency,
COALESCE(raw.customer_id, raw.cust_id)  AS customer_id,
...
```
Both web and mobile records for ORD-1003 now have the same column structure. The web record has `amount = NULL` (passes cleaning — NULL amount is not in the quarantine rules), and the mobile record has `amount = 2100.00`.

**Step 3 — Deduplication (`silver.orders_dedup` via `SQL_20_ORDERS_DEDUP`)**

```sql
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY order_id
    ORDER BY updated_at DESC NULLS LAST
) = 1
```
The mobile record has the **later** `updated_at`, so `ROW_NUMBER() = 1` → it survives. The web record (NULL amount, earlier timestamp) gets `ROW_NUMBER() = 2` → it is discarded.

**Step 4 — Gold (`gold.fct_orders`)**

The surviving mobile record has `amount = 2100.00 INR`.
- `amount_inr = 2100.00` (already in INR, no conversion needed)
- Tier lookup for the customer → say Silver (1× multiplier) → `loyalty_points = FLOOR(2100 × 1.0) = 2100`

*(Exact multiplier depends on the customer's tier at `order_date`.)*

---

#### ORD-1005 — Priya's Tier Difference

**ORD-1005** (Priya) earns points at the **Gold** multiplier because at the time of that order her tier in `dim.customers_scd2` was `Gold`. The join condition is:

```sql
JOIN dim.customers_scd2 c
  ON o.customer_id = c.customer_id
 AND o.order_date  BETWEEN c.effective_from AND COALESCE(c.effective_to, '9999-12-31')
```

For **ORD-1001**, Priya's order date falls in a period when her SCD2 record shows `Silver`. The `BETWEEN ... AND ...` range on `effective_from / effective_to` selects the row that was active on that specific date — different dates pick different SCD2 rows, hence different multipliers.

---

### B3. New Validation Rule — `unsupported_currency`

**SQL addition inside `SQL_10_ORDERS_CLEAN`:**

```sql
-- Inside ARRAY_CONSTRUCT_COMPACT(...):
IFF(currency NOT IN ('INR', 'USD'), 'unsupported_currency', NULL),
```

Full context:
```sql
ARRAY_CONSTRUCT_COMPACT(
    IFF(amount IS NULL AND source != 'web', 'missing_amount', NULL),
    IFF(customer_id IS NULL,               'missing_customer', NULL),
    IFF(currency NOT IN ('INR', 'USD'),    'unsupported_currency', NULL)   -- NEW
) AS reasons
```

**Analysis:**

| Question | Answer |
|---|---|
| `reasons` for ORD-1006 **before** change | `['missing_amount']` (or similar existing reason) |
| `reasons` for ORD-1006 **after** change | Adds `'unsupported_currency'` to the array if its currency is e.g. `'EUR'` |
| Does gold total change? | **No** — ORD-1006 was already quarantined; adding a second reason does not move it to or from gold. The gold query only reads `silver.orders_dedup`, which only contains rows that passed all checks. |
| Does a second quarantine row appear? | **No** — `SQL_30_QUARANTINE` uses `INSERT INTO ... SELECT ... WHERE order_id NOT IN (SELECT order_id FROM silver.orders_quarantine)` (or a MERGE with matching on `order_id`). The idempotency guard prevents double-insertion. |

---

### B4. SCD2 Change — Arjun Moves to Gold

**New event to add to `MOCK_CRM_TIER_EVENTS`:**
```python
{"customer_id": "CUST-02", "email": "arjun.k@yahoo.in",
 "tier": "Gold", "effective_from": "2026-08-15"}
```

**Predictions (fill before running):**

| Quantity | Predicted | Actual |
|---|---|---|
| Rows for CUST-02 in `dim.customers_scd2` | 2 (Silver row closed, Gold row opened) | *(run)* |
| Tier used for ORD-1002 | Depends on ORD-1002's `order_date` vs 2026-08-15 | *(run)* |
| Loyalty points for ORD-1002 | Higher if order_date ≥ 2026-08-15 (Gold = 2×) | *(run)* |
| Total loyalty points in gold | Increases if ORD-1002 picks up Gold multiplier | *(run)* |
| Number of gold rows whose `published_at` changed | Only rows affected by recalculated loyalty points | *(run)* |

**Idempotency explanation (4–6 sentences):**

The `row_hash` column is a deterministic hash of all business-significant columns in a gold row (`order_id`, `amount_inr`, `loyalty_points`, `customer_id`, `tier`, etc.). The `MERGE` statement matches on `order_id` and compares `row_hash`: if the hash is unchanged the row is left untouched (`WHEN MATCHED AND row_hash = src.row_hash THEN DO NOTHING`), and if the hash differs the row is updated and `published_at` is refreshed. This means re-running the pipeline with identical input data produces zero changes to gold — it is safe to run twice. Bronze still grows by 8 rows on every run because the `COPY INTO bronze.orders_raw` statement loads fresh raw files each time without a deduplication guard at the bronze level; the deduplication happens downstream in the silver layer. If you need bronze to stop growing, you can add a `FILES = (...)` or `COPY_OPTIONS = (FORCE = FALSE)` clause to skip already-loaded files.

---

### B5. New Quality Check — Gold Orders with NULL `amount_inr`

**SQL check to add to `quality_checks()`:**

```python
# Check 6: gold orders where amount_inr is NULL but raw amount was not NULL
check_6 = session.sql("""
    SELECT COUNT(*) AS cnt
    FROM gold.fct_orders g
    JOIN silver.orders_dedup s ON g.order_id = s.order_id
    WHERE g.amount_inr IS NULL
      AND s.amount IS NOT NULL
""").collect()[0]["CNT"]

results.append(("NULL amount_inr despite non-null source amount", check_6))
if check_6 > 0:
    print(f"PROBLEM: {check_6} gold order(s) have NULL amount_inr "
          f"but a non-null source amount — conversion logic failed.")
```

**Making it fail on purpose:**  
Insert a mock order with a non-INR currency that the conversion logic does not handle → `amount_inr` becomes NULL. Show the PROBLEM output, then remove the mock and re-run.

**ETL vs ELT (3–4 sentences):**

ELT is better for FreshCart because Snowflake's compute is optimised for SQL transformations at scale — loading raw data first (bronze) and transforming inside the warehouse is faster and cheaper than transforming on a separate ETL server before loading. ELT also preserves the full raw record in bronze, making it easy to reprocess with new business rules without re-extracting from the API. ETL would still win in one situation: when the raw data contains sensitive PII (like payment card numbers) that must be masked or encrypted **before** it ever lands in the cloud warehouse, because ELT loads the data as-is and you cannot take back what has already been stored.

---

## Part C: ML Pipeline with Mage

### C1. Pipeline Graph

```
[data_loader]      load_iris
                       │
                       ▼
[transformer]  check_data_quality   (@test: no nulls, 3 classes)
                       │
                       ▼
[transformer]     prepare_data      (@test: 120 train / 30 test)
                       │
                       ▼
[transformer]      train_model      (@test: accuracy ≥ 0.90)
                     /   \
                    /     \
                   ▼       ▼
[data_exporter] save_results    evaluate_model
(@test: CSV exists)              (@test: runs without error)
```

Run command:
```bash
mage run iris_project iris_classifier --test
```

---

### C2. Tests as a Gate — max_depth Experiment

> Run each experiment after deleting `iris_predictions.csv`.

| max_depth | Test accuracy | test_accuracy ≥ 0.90? | iris_predictions.csv created? |
|---|---|---|---|
| 1 | ~0.6667 | ✗ No | No |
| 2 | ~0.9333 | ✓ Yes | Yes |
| 3 | ~0.9667 | ✓ Yes | Yes |
| 4 | ~0.9667 | ✓ Yes | Yes |
| 5 | ~0.9667 | ✓ Yes | Yes |

*(Exact values depend on the random_state; fill in actuals after running.)*

**Why the gate is better than saving first:**  
When a `@test` in `train_model` raises an `AssertionError`, Mage marks that block as failed and **does not execute any downstream blocks** (`save_results`, `evaluate_model`). This means a bad model file never reaches disk — there is no corrupted output to clean up. If you saved first and checked afterwards, you would need extra logic to detect and delete the bad file, and there is a window where another process might read the bad file before you remove it.

---

### C3. Evaluation Branch

After adding `evaluate_model` as a second downstream of `train_model`, the edited `metadata.yaml` section for `train_model` becomes:

```yaml
  - name: train_model
    downstream_blocks: [save_results, evaluate_model]
```

The confusion matrix and metrics table are printed to the Mage run log. *(Include screenshot of Mage UI graph showing the branch.)*

---

### C4. Custom Block — `check_data_quality`

Added `iris_project/transformers/check_data_quality.py` between `load_iris` and `prepare_data`. It validates:
- Zero null values across all columns (`@test test_no_nulls`)
- Exactly 3 target classes (`@test test_exactly_three_classes`)

This block catches data corruption early — if someone accidentally passes a broken Iris file, the pipeline fails immediately with a clear message rather than producing a silently wrong model.

---

## Part D: RabbitMQ Food-order Stream

### D1. Routing Table on Paper

Binding patterns:
| Driver | Pattern |
|---|---|
| Ravi | `bangalore.koramangala.*` |
| Priya | `bangalore.indiranagar.*` |
| Arjun | `bangalore.*.ride` |
| Meena | `bangalore.*.food` |
| Karthik | `chennai.tnagar.food` |
| Control | `bangalore.#` |

| # | Routing key | Receiving queues |
|---|---|---|
| 1 | `bangalore.koramangala.food` | Ravi (`koramangala.*` ✓), Meena (`*.food` ✓), Control (`#` ✓) |
| 2 | `bangalore.indiranagar.ride` | Priya (`indiranagar.*` ✓), Arjun (`*.ride` ✓), Control (`#` ✓) |
| 3 | `bangalore.whitefield.ride` | Arjun (`*.ride` ✓), Control (`#` ✓) |
| 4 | `chennai.tnagar.food` | Karthik (`chennai.tnagar.food` ✓) |
| 5 | `bangalore.whitefield.food` | Meena (`*.food` ✓), Control (`#` ✓) |
| 6 | `bangalore.koramangala` | Control (`#` ✓) only |

**Q6 — Why only Control matches `bangalore.koramangala` (2 words):**

- `bangalore.koramangala.*` (Ravi) — the `*` **must** match exactly one word. The key has no third word, so this pattern requires 3 words total but the key only has 2. ✗
- `bangalore.indiranagar.*` (Priya) — same reasoning, and the second word doesn't match. ✗
- `bangalore.*.ride` (Arjun) — requires exactly 3 words ending in `ride`. ✗
- `bangalore.*.food` (Meena) — requires exactly 3 words ending in `food`. ✗
- `chennai.tnagar.food` (Karthik) — literal match, city doesn't match. ✗
- `bangalore.#` (Control) — `#` matches **zero or more words**. After `bangalore.`, there is one word (`koramangala`) and zero additional words. `#` happily matches one word. ✓

---

### D3. ACK and NACK Answers

**What happens if the driver crashes before sending an ACK?**  
RabbitMQ keeps the message in the **unacknowledged** state. When the driver's TCP connection drops (crash), RabbitMQ sees the channel close without an ACK and automatically **re-queues** the message (`requeue=True` is the default for connection-drop recovery). The message is delivered to the same driver (or another consumer on the same queue) when it reconnects. This guarantees **at-least-once delivery** — the message will not be lost, but it may be processed more than once if the driver crashed after doing the work but before ACKing.

**What would happen with `requeue=True` for a message that is always bad?**  
If `basic_nack(requeue=True)` is used for a structurally invalid message (one that will always fail processing), the message is returned to the front of the queue and immediately re-delivered — creating an **infinite loop** that consumes CPU and fills logs. This is called a "poison message". The correct behaviour (as implemented in `driver.py`) is `requeue=False`, which routes the message to the **dead-letter exchange** (DLX) or discards it, breaking the loop.

---

## Integration Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                              │
│  freshcart-pipelines/  (Part A — Git + CI/CD)                        │
│  ┌────────────┐  push  ┌─────────────────┐                           │
│  │ Local code │───────►│ GitHub Actions  │  pytest (green/red)       │
│  └────────────┘        └────────┬────────┘                           │
└───────────────────────────────-─┼────────────────────────────────────┘
                                  │ all tests pass
           ┌──────────────────────┼───────────────────────┐
           │                      │                       │
           ▼                      ▼                       ▼
  ┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐
  │  Part B: ELT    │   │  Part C: Mage ML │   │  Part D: Stream  │
  │  Snowflake      │   │  Iris Pipeline   │   │  RabbitMQ        │
  │                 │   │                  │   │                  │
  │ bronze → silver │   │ load_iris        │   │ dispatcher.py    │
  │ → dim → ref     │   │ → quality_check  │   │ publishes to     │
  │ → gold          │   │ → prepare_data   │   │ rapido-dispatch  │
  │ fct_orders      │   │ → train_model    │   │ exchange         │
  │ (idempotent     │   │ → save_results   │   │                  │
  │  MERGE)         │   │ → evaluate_model │   │ driver.py(s)     │
  └────────┬────────┘   └──────────────────┘   │ subscribe with   │
           │                                    │ topic patterns   │
           │  Bonus: Stream → Lakehouse          │ ACK / NACK       │
           └────────────────────────────────────┘
```

---

## Reflection

**One thing that broke:**  
*(Write your own here — e.g.: "The CI workflow failed on the first push because `requirements.txt` was missing `scikit-learn`...")*

**How I found the cause:**  
*(e.g., "I read the GitHub Actions log which showed `ModuleNotFoundError: No module named 'sklearn'`...")*

**How I fixed it:**  
*(e.g., "I added `scikit-learn>=1.3.0` to `requirements.txt`, committed, and pushed. The next run was green.")*

---

*Appendix: Screenshots (not counted in 8-page limit)*
- B1: Snowflake baseline query outputs
- A3: GitHub Actions green run
- A3: GitHub Actions red run
- C3: Mage UI graph showing evaluation branch
