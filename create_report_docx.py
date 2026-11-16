import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

doc = Document()

# Set standard margins (1 inch)
for section in doc.sections:
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

# Colors
COLOR_PRIMARY = RGBColor(26, 54, 93)     # Deep Navy
COLOR_SECONDARY = RGBColor(43, 108, 176) # Blue
COLOR_TEXT = RGBColor(45, 55, 72)        # Charcoal

def style_heading(p, font_size, color, bold=True):
    for run in p.runs:
        run.font.name = "Calibri"
        run.font.size = Pt(font_size)
        run.font.color.rgb = color
        run.font.bold = bold

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def style_table(table, header_bg="1A365D", alt_bg="F7FAFC"):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(table.rows):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="120" w:type="dxa"/><w:bottom w:w="120" w:type="dxa"/><w:left w:w="160" w:type="dxa"/><w:right w:w="160" w:type="dxa"/></w:tcMar>')
            tcPr.append(tcMar)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(9.5)
            if i == 0:
                set_cell_background(cell, header_bg)
                for p in cell.paragraphs:
                    for run in p.runs:
                        run.font.color.rgb = RGBColor(255, 255, 255)
                        run.font.bold = True
            elif i % 2 == 1:
                set_cell_background(cell, alt_bg)

# ==========================================
# TITLE SECTION
# ==========================================
title_p = doc.add_paragraph()
title_p.paragraph_format.space_before = Pt(0)
title_p.paragraph_format.space_after = Pt(4)
r = title_p.add_run("Assignment: From Git to Gold")
style_heading(title_p, 24, COLOR_PRIMARY, bold=True)

sub_p = doc.add_paragraph()
sub_p.paragraph_format.space_after = Pt(14)
r_sub = sub_p.add_run("Version Control, ELT, ML Pipelines and Event Streaming, End to End")
style_heading(sub_p, 13, COLOR_SECONDARY, bold=False)

meta_p = doc.add_paragraph()
meta_p.paragraph_format.space_after = Pt(20)
meta_p.add_run("Student Name: ").bold = True
meta_p.add_run("Ashutosh\n")
meta_p.add_run("Course: ").bold = True
meta_p.add_run("Data Engineering — Pipeline Orchestration\n")
meta_p.add_run("GitHub Repository: ").bold = True
meta_p.add_run("https://github.com/Ashtsssssh/data-pipeline\n")
meta_p.add_run("Platforms Used: ").bold = True
meta_p.add_run("Google Colab, Snowflake Trial (AWS), GitHub Actions, Mage AI, RabbitMQ\n")

# ==========================================
# PART A: GIT AND CI/CD
# ==========================================
p = doc.add_paragraph()
p.add_run("Part A: Git and CI/CD (15 Marks)")
style_heading(p, 16, COLOR_PRIMARY, bold=True)

p_a1 = doc.add_paragraph()
p_a1.add_run("A1. Repository Structure & Commit History\n").bold = True
p_a1.add_run(
    "The repository freshcart-pipelines was created and structured following professional software engineering practices. "
    "A total of 10 meaningful commits were executed over the course of the project development lifecycle, verifying incremental progress:\n"
)

git_log_table = doc.add_table(rows=1, cols=2)
git_log_table.rows[0].cells[0].text = "Commit Hash"
git_log_table.rows[0].cells[1].text = "Commit Message / Description"

commits = [
    ("58c72fa", "feat: initialise repo with README, gitignore, requirements"),
    ("93c3307", "feat(ci): add GitHub Actions workflow and pytest test for prepare_data"),
    ("236ee45", "feat(mage): add iris_classifier pipeline blocks with @test gates"),
    ("d630d2b", "test: break split ratio to trigger red CI (test_size=0.3)"),
    ("9e5cae5", "fix(ci): optimize requirements for CI runner and restore 80/20 split"),
    ("aced77e", "test: break split ratio to 0.3 for intentional red CI"),
    ("dd5de03", "fix(ci): restore 80/20 split (test_size=0.2) to pass CI"),
    ("3d2a006", "feat: add stream scripts, FreshCart ELT notebooks, and report draft"),
    ("c099ed8", "feat(elt): configure Snowflake account credentials"),
    ("0159702", "feat(elt): complete FreshCart ELT notebook with all outputs (B1-B5)"),
]

for chash, msg in commits:
    row = git_log_table.add_row()
    row.cells[0].text = chash
    row.cells[1].text = msg

style_table(git_log_table)

# A2: Command Table
p_a2 = doc.add_paragraph()
p_a2.paragraph_format.space_before = Pt(14)
p_a2.add_run("A2. Where Does Each Git Command Act?\n").bold = True

git_cmd_table = doc.add_table(rows=1, cols=3)
git_cmd_table.rows[0].cells[0].text = "Command"
git_cmd_table.rows[0].cells[1].text = "Where the change happens"
git_cmd_table.rows[0].cells[2].text = "What exactly happens? (In own words)"

cmds = [
    ("git init", "Working folder (creates .git/)", "Creates a new hidden .git directory in the current folder, initialising local version tracking without staging any files."),
    ("git add train.py", "Staging area (index)", "Copies the current snapshot of train.py into the Git index, preparing it to be bundled into the next commit."),
    ("git commit -m \"msg\"", "Local repository (.git/objects/)", "Permanently records the staged snapshot as a cryptographically hashed commit object in the local repository history."),
    ("git remote add origin URL", "Local config (.git/config)", "Registers a named shorthand alias ('origin') for the remote server URL in local config without moving any data."),
    ("git push -u origin main", "Remote repository (GitHub)", "Uploads local branch commits to the remote server and binds the local branch to track the remote branch automatically."),
    ("git pull origin main", "Local repo + Working folder", "Fetches latest commits from the remote server and merges them directly into the current active local branch.")
]

for cmd, loc, desc in cmds:
    row = git_cmd_table.add_row()
    row.cells[0].text = cmd
    row.cells[1].text = loc
    row.cells[2].text = desc

style_table(git_cmd_table)

p_teammate = doc.add_paragraph()
p_teammate.paragraph_format.space_before = Pt(8)
p_teammate.add_run("Can your teammate see your code on GitHub after git commit? Why or why not?\n").bold = True
p_teammate.add_run(
    "No, your teammate cannot see your code after running 'git commit'. Git is a distributed version control system. "
    "A commit operates entirely within your local repository store (.git/objects/). It does not touch network sockets "
    "or communicate with the remote server. Your code only becomes visible to teammates on GitHub once you explicitly run 'git push origin main'."
)

# A3: Small CI Workflow
p_a3 = doc.add_paragraph()
p_a3.paragraph_format.space_before = Pt(14)
p_a3.add_run("A3. Small CI Workflow (GitHub Actions)\n").bold = True
p_a3.add_run(
    "A continuous integration workflow was configured at .github/workflows/ci.yml to execute automatically on every push. "
    "It checks out the code, initializes a clean Python 3.12 runner, installs required dependencies, and executes pytest on tests/test_prepare_data.py.\n"
    "• Green Run: Default configuration with test_size=0.2 passed all 3 assertions (120 train / 30 test split).\n"
    "• Red Run: Changing test_size to 0.3 intentionally broke the split ratio (105 train / 45 test), causing an immediate assertion failure in GitHub Actions (see Appendix for screenshots)."
)

# ==========================================
# PART B: FRESHCART ELT ON SNOWFLAKE
# ==========================================
doc.add_page_break()
p_b = doc.add_paragraph()
p_b.add_run("Part B: FreshCart ELT on Snowflake (30 Marks)")
style_heading(p_b, 16, COLOR_PRIMARY, bold=True)

p_b1 = doc.add_paragraph()
p_b1.add_run("B1. Baseline Pipeline Execution\n").bold = True
p_b1.add_run("The complete FreshCart ELT pipeline was executed top-to-bottom on Snowflake AWS trial account (IABCYFQ-GU56801). All baseline quantities matched expected numbers perfectly:\n")

b1_table = doc.add_table(rows=1, cols=3)
b1_table.rows[0].cells[0].text = "Check"
b1_table.rows[0].cells[1].text = "Expected"
b1_table.rows[0].cells[2].text = "Actual Run Output"

b1_data = [
    ("Raw order rows in bronze after one run", "8 (6 web + 2 mobile)", "8 (6 web + 2 mobile)"),
    ("Rows that pass cleaning (silver.orders_clean)", "6", "6"),
    ("Rows in quarantine", "2 (ORD-1004, ORD-1006)", "2 (ORD-1004, ORD-1006)"),
    ("Orders after deduplication", "4", "4"),
    ("Final gold line", "4 orders, revenue ₹7,785.00, 126 loyalty points", "4 orders, revenue ₹7,785.00, 126 loyalty points"),
    ("Share of rows rejected", "25%", "25.0%")
]

for chk, exp, act in b1_data:
    row = b1_table.add_row()
    row.cells[0].text = chk
    row.cells[1].text = exp
    row.cells[2].text = act

style_table(b1_table)

# B2: Trace One Record by Hand
p_b2 = doc.add_paragraph()
p_b2.paragraph_format.space_before = Pt(14)
p_b2.add_run("B2. Record Hand-Trace: ORD-1003 and ORD-1005\n").bold = True
p_b2.add_run("Detailed Step-by-Step Trace for ORD-1003:\n").bold = True
p_b2.add_run(
    "1. Bronze Layer (bronze.orders_raw): ORD-1003 arrives via two distinct channels. The website record arrives with order_id='ORD-1003', cust_email='meera@outlook.com', amount=None, and updated_at='2026-09-02 09:10:00'. "
    "The mobile app record arrives with orderId='ORD-1003', customer.email='Meera@Outlook.com', total.value='2,100.00', and updatedAt='2026-09-02T18:40:00'. "
    "Field names differ because the web portal and mobile app represent independently developed upstream clients using separate JSON payloads (flat vs nested).\n\n"
    "2. Silver Layer Normalization (silver.orders_checked): SQL_10_ORDERS_CLEAN unifies the disparate schemas using:\n"
    "   • TRIM(order_id) and raw:orderId::STRING -> order_id\n"
    "   • LOWER(TRIM(cust_email)) and raw:customer.email::STRING -> email\n"
    "   • TRY_TO_DECIMAL(REGEXP_REPLACE(amount, '[^0-9.-]', ''), 12, 2) and raw:total.value::STRING -> amount\n"
    "   • Both records pass validation into silver.orders_checked because NULL amount on web is explicitly permitted for pending orders.\n\n"
    "3. Deduplication (silver.orders_dedup): The SQL_20_ORDERS_DEDUP logic executes:\n"
    "   QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC, ingest_seq DESC) = 1\n"
    "   The mobile record has updated_at = '2026-09-02 18:40:00', whereas the web record has updated_at = '2026-09-02 09:10:00'. "
    "   Because 18:40:00 > 09:10:00, the mobile copy receives ROW_NUMBER() = 1 and survives; the web copy receives ROW_NUMBER() = 2 and is discarded.\n\n"
    "4. Gold Layer Computation (gold.fct_orders):\n"
    "   • Amount in INR: The surviving mobile record has amount = 2,100.00 INR. Since currency is INR, fx_rate = 1.00 -> amount_inr = 2,100.00 * 1.0 = ₹2,100.00.\n"
    "   • Loyalty Points: Meera (CUST-03) has Platinum tier since 2022-11-01 (multiplier = 3). Formula: FLOOR(2100.00 / 100) * 3 = 21 * 3 = 63 loyalty points.\n\n"
    "Explanation for ORD-1005 (Priya's Tier Multiplier):\n"
).bold = False
p_b2.add_run(
    "Priya earns points at the Gold multiplier (2x) for ORD-1005, but at the Silver multiplier (1x) for ORD-1001. "
    "This occurs due to the point-in-time join against dim.customers_scd2:\n"
    "   ON o.customer_id = c.customer_id AND o.order_date BETWEEN c.valid_from AND COALESCE(c.valid_to, '9999-12-31')\n"
    "Priya's SCD2 record transitioned from Silver to Gold effective 2026-09-03. ORD-1001 was placed on 2026-09-01 (falls in Silver window), whereas ORD-1005 was placed on 2026-09-03 (falls in Gold window)."
)

# B3: Validation Rule
p_b3 = doc.add_paragraph()
p_b3.paragraph_format.space_before = Pt(14)
p_b3.add_run("B3. Add Validation Rule: unsupported_currency\n").bold = True
p_b3.add_run(
    "Inside ARRAY_CONSTRUCT_COMPACT(...) in SQL_10_ORDERS_CLEAN, the following rule was added:\n"
    "   IFF(currency NOT IN ('INR', 'USD'), 'unsupported_currency', NULL)\n\n"
    "1. Reasons Array for ORD-1006:\n"
    "   • Before Change: ['bad_email', 'bad_pincode']\n"
    "   • After Change: ['bad_email', 'bad_pincode', 'unsupported_currency']\n\n"
    "2. Does the Gold Total Change? Why or Why Not?\n"
    "   No, the gold totals do not change. ORD-1006 was already quarantined in the baseline run due to bad email and bad pincode. Adding another failure reason simply appends to the reasons array; it does not alter the set of clean rows progressing to gold.\n\n"
    "3. Does the New Run Add a Second Quarantine Row? Which SQL Decides This?\n"
    "   No, it does not add a second row. The INSERT INTO quarantine.orders query contains the idempotency predicate:\n"
    "   AND NOT EXISTS (\n"
    "       SELECT 1 FROM quarantine.orders q\n"
    "       WHERE q.source = c.source AND EQUAL_NULL(q.order_id, c.order_id)\n"
    "         AND EQUAL_NULL(q.row_data:UPDATED_AT::TIMESTAMP_NTZ, c.updated_at))\n"
    "   This stops duplicate bad records with identical order_id and updated_at from being appended."
)

# B4: Change History and Idempotency
p_b4 = doc.add_paragraph()
p_b4.paragraph_format.space_before = Pt(14)
p_b4.add_run("B4. Change History and Idempotency (Arjun moves to Gold)\n").bold = True
p_b4.add_run(
    "A new CRM event was injected: Arjun (CUST-02, arjun.k@yahoo.in) moves to Gold with effective_from = 2026-08-15.\n"
)

b4_table = doc.add_table(rows=1, cols=3)
b4_table.rows[0].cells[0].text = "Quantity"
b4_table.rows[0].cells[1].text = "Your Prediction (Before Run)"
b4_table.rows[0].cells[2].text = "Actual Output After Run"

b4_data = [
    ("Rows for CUST-02 in dim.customers_scd2", "2 (Silver up to Aug 14, Gold from Aug 15)", "2"),
    ("Tier used for ORD-1002", "Gold (Order date 2026-09-01 >= 2026-08-15)", "Gold"),
    ("Loyalty points for ORD-1002", "70 (35 points * 2x Gold multiplier)", "70"),
    ("Total loyalty points in gold", "161 (126 baseline + 35 new points)", "161"),
    ("Number of gold rows whose published_at changed", "1 (Only ORD-1002 updated)", "1")
]

for q, pred, act in b4_data:
    row = b4_table.add_row()
    row.cells[0].text = q
    row.cells[1].text = pred
    row.cells[2].text = act

style_table(b4_table)

p_idem = doc.add_paragraph()
p_idem.paragraph_format.space_before = Pt(8)
p_idem.add_run("Explanation of row_hash, MERGE, and Bronze Growth (Idempotency):\n").bold = True
p_idem.add_run(
    "In gold.fct_orders, every row is stamped with a deterministic row_hash generated from all business columns. "
    "The publication step uses a MERGE statement matching on order_id. When incoming row_hash matches existing target row_hash, "
    "no update occurs, preserving the original published_at timestamp. Only when an attribute changes (such as Arjun's tier upgrading to Gold) "
    "does row_hash differ, triggering an in-place UPDATE and updating published_at. Meanwhile, bronze.orders_raw is an append-only landing table "
    "designed to retain an immutable audit log of every extraction batch, which is why bronze grows by 8 rows on every pipeline execution."
)

# B5: Quality Check and ELT vs ETL
p_b5 = doc.add_paragraph()
p_b5.paragraph_format.space_before = Pt(14)
p_b5.add_run("B5. Data Quality Check and Architecture Evaluation\n").bold = True
p_b5.add_run(
    "A 6th check was added to quality_checks():\n"
    "   'gold orders with NULL amount_inr': 'SELECT COUNT_IF(amount IS NOT NULL AND amount_inr IS NULL) FROM gold.fct_orders'\n\n"
    "Making Check Fail on Purpose:\n"
    "Temporarily setting amount_inr = NULL on ORD-1001 triggered the expected alert:\n"
    "   gold orders with NULL amount_inr       1   PROBLEM\n"
    "Restoring amount_inr returned the check to 0 OK (see Appendix for screenshots).\n\n"
    "Architectural Analysis: Why ELT is Better for FreshCart, and When ETL Still Wins:\n"
    "ELT is superior for FreshCart because raw data from varied channels can be landed immediately without rigid upfront schemas, "
    "leveraging Snowflake's massive parallel compute engine to perform transformations and point-in-time enrichments in SQL. "
    "Furthermore, ELT enables reprocessing historical raw bronze data whenever business logic changes. "
    "However, traditional ETL would still win in scenarios with strict pre-load data privacy regulations (e.g. PCI-DSS credit card numbers or HIPAA patient identifiers) "
    "where unmasked sensitive data cannot legally enter the cloud data warehouse under any circumstances."
)

# ==========================================
# PART C: ML PIPELINE WITH MAGE
# ==========================================
doc.add_page_break()
p_c = doc.add_paragraph()
p_c.add_run("Part C: ML Pipeline with Mage (20 Marks)")
style_heading(p_c, 16, COLOR_PRIMARY, bold=True)

p_c1 = doc.add_paragraph()
p_c1.add_run("C1. Pipeline Architecture & Execution\n").bold = True
p_c1.add_run(
    "The iris_classifier pipeline was constructed in Mage AI consisting of orchestrated blocks connected in a Directed Acyclic Graph (DAG):\n"
    "1. load_iris (data_loader): Loads Iris dataset; @test verifies (150, 6) shape and 3 target classes.\n"
    "2. check_data_quality (transformer - Part C4): Custom block validating zero missing values and exactly 3 classes.\n"
    "3. prepare_data (transformer): Splits data 80/20; @test verifies 120 train / 30 test records.\n"
    "4. train_model (transformer): Fits DecisionTreeClassifier; @test enforces accuracy >= 0.90.\n"
    "5. save_results (data_exporter): Exports predictions to iris_predictions.csv.\n"
    "6. evaluate_model (data_exporter - Part C3): Downstream branch calculating confusion matrix and classification metrics."
)

p_c2 = doc.add_paragraph()
p_c2.paragraph_format.space_before = Pt(14)
p_c2.add_run("C2. Tests as a Gate (max_depth Experiment)\n").bold = True

c2_table = doc.add_table(rows=1, cols=4)
c2_table.rows[0].cells[0].text = "max_depth"
c2_table.rows[0].cells[1].text = "Test Accuracy"
c2_table.rows[0].cells[2].text = "test_accuracy Passed? (>= 0.90)"
c2_table.rows[0].cells[3].text = "iris_predictions.csv Created?"

c2_data = [
    ("1", "66.67% (0.6667)", "No (Failed test_accuracy_gate)", "No (BLOCKED)"),
    ("2", "93.33% (0.9333)", "Yes", "Yes (CREATED)"),
    ("3", "96.67% (0.9667)", "Yes", "Yes (CREATED)"),
    ("4", "93.33% (0.9333)", "Yes", "Yes (CREATED)"),
    ("5", "93.33% (0.9333)", "Yes", "Yes (CREATED)")
]

for md, acc, passed, cr in c2_data:
    row = c2_table.add_row()
    row.cells[0].text = md
    row.cells[1].text = acc
    row.cells[2].text = passed
    row.cells[3].text = cr

style_table(c2_table)

p_gate = doc.add_paragraph()
p_gate.paragraph_format.space_before = Pt(8)
p_gate.add_run("Why a Test Gate is Superior to Post-Export Validation:\n").bold = True
p_gate.add_run(
    "When a @test block in train_model fails, Mage halts pipeline execution immediately and suppresses all downstream tasks. "
    "Consequently, save_results never executes, and iris_predictions.csv is never written. "
    "This gate pattern prevents poisoned or substandard predictions from ever reaching shared storage or downstream consumers, "
    "eliminating race conditions and manual clean-up workflows required when checking files after export."
)

p_c3 = doc.add_paragraph()
p_c3.paragraph_format.space_before = Pt(14)
p_c3.add_run("C3. Evaluation Branch & Mage UI Visualization\n").bold = True
p_c3.add_run(
    "The evaluate_model exporter was attached as a parallel branch to train_model. "
    "It computes test-set confusion matrix and classification metrics:\n\n"
    "CONFUSION MATRIX (test set):\n"
    "                 pred_setosa  pred_versicolor  pred_virginica\n"
    "true_setosa               10                0               0\n"
    "true_versicolor            0                9               1\n"
    "true_virginica             0                0              10\n\n"
    "Overall Test Accuracy: 0.9667 (96.67%)\n\n"
    "The Mage UI was launched via Cloudflare tunnel, visualizing the DAG branch where train_model splits into save_results and evaluate_model."
)

# ==========================================
# PART D: FOOD-ORDER STREAM WITH RABBITMQ
# ==========================================
doc.add_page_break()
p_d = doc.add_paragraph()
p_d.add_run("Part D: Food-Order Stream with RabbitMQ (20 Marks)")
style_heading(p_d, 16, COLOR_PRIMARY, bold=True)

p_d1 = doc.add_paragraph()
p_d1.add_run("D1. Topic Routing on Paper\n").bold = True

d1_table = doc.add_table(rows=1, cols=4)
d1_table.rows[0].cells[0].text = "#"
d1_table.rows[0].cells[1].text = "Routing Key"
d1_table.rows[0].cells[2].text = "Receiving Queues"
d1_table.rows[0].cells[3].text = "Matching Pattern Rationale"

d1_data = [
    ("1", "bangalore.koramangala.food", "Ravi, Meena, Control", "Ravi (koramangala.*), Meena (*.food), Control (#)"),
    ("2", "bangalore.indiranagar.ride", "Priya, Arjun, Control", "Priya (indiranagar.*), Arjun (*.ride), Control (#)"),
    ("3", "bangalore.whitefield.ride", "Arjun, Control", "Arjun (*.ride), Control (#)"),
    ("4", "chennai.tnagar.food", "Karthik", "Karthik (chennai.tnagar.food) - exact 3-word match"),
    ("5", "bangalore.whitefield.food", "Meena, Control", "Meena (*.food), Control (#)"),
    ("6", "bangalore.koramangala", "Control only", "2-word key: * patterns fail (require 3 words); # matches 0+ words")
]

for num, rk, rq, rat in d1_data:
    row = d1_table.add_row()
    row.cells[0].text = num
    row.cells[1].text = rk
    row.cells[2].text = rq
    row.cells[3].text = rat

style_table(d1_table)

p_q6 = doc.add_paragraph()
p_q6.paragraph_format.space_before = Pt(8)
p_q6.add_run("Question 6 Analysis (Two-Word Routing Key):\n").bold = True
p_q6.add_run(
    "In AMQP topic exchanges, the '*' symbol matches exactly one word, whereas '#' matches zero or more words. "
    "Patterns such as 'bangalore.koramangala.*' or 'bangalore.*.food' strictly require three dot-separated words. "
    "Because 'bangalore.koramangala' contains only two words, all '*' binding patterns fail. "
    "Only 'bangalore.#' successfully matches because '#' matches the single remaining word 'koramangala' followed by zero words."
)

p_d2 = doc.add_paragraph()
p_d2.paragraph_format.space_before = Pt(14)
p_d2.add_run("D2 & D3. Broker Execution, ACK and NACK Protocols\n").bold = True
p_d2.add_run(
    "The dispatcher.py and driver.py scripts were executed on a RabbitMQ message broker. "
    "The dispatcher published JSON orders to the rapido-dispatch topic exchange every 2 seconds, intentionally omitting the 'zone' key on every 10th message.\n\n"
    "Handling Malformed Messages (D3):\n"
    "Drivers validate the presence of the 'zone' attribute. When 'zone' is absent, the driver issues basic_nack(delivery_tag, requeue=False), "
    "causing the bad message to be safely discarded (or dead-lettered) rather than reprocessed.\n\n"
    "Theory Questions:\n"
    "1. What happens if a driver crashes before sending an ACK?\n"
    "   RabbitMQ maintains the unacknowledged message in its queue buffer. When the driver process crashes, its TCP socket closes. "
    "   RabbitMQ automatically re-queues the unacknowledged message, allowing it to be redelivered to another active driver instance (at-least-once delivery).\n\n"
    "2. What would happen with requeue=True for an always-bad message?\n"
    "   If an inherently unparseable poison message is rejected with requeue=True, RabbitMQ reinserts it at the head of the queue. "
    "   The consumer immediately redelivers and rejects it in an infinite crash loop, consuming 100% CPU and flooding logs."
)

# ==========================================
# PART E: INTEGRATION DIAGRAM & REFLECTION
# ==========================================
doc.add_page_break()
p_e = doc.add_paragraph()
p_e.add_run("Part E: End-to-End Platform Integration & Reflection (15 Marks)")
style_heading(p_e, 16, COLOR_PRIMARY, bold=True)

p_e1 = doc.add_paragraph()
p_e1.add_run("E1. Platform Integration Architecture\n").bold = True
p_e1.add_run(
    "The modern data platform combines software engineering, batch ELT, ML orchestration, and real-time event streaming:\n\n"
    "1. Git & GitHub Actions (Part A): Serves as the single source of truth. Every commit triggers automated unit tests ensuring pipeline transformation integrity before deployment.\n"
    "2. FreshCart Snowflake ELT (Part B): Extracts multi-source batch orders into raw Bronze tables, normalizes and dedupes in Silver, and publishes an idempotent Gold fact table using SCD2 point-in-time joins.\n"
    "3. Mage ML Pipeline (Part C): Pulls clean Gold tabular data to train classification models with automated test gates preventing defective model artifacts from reaching production.\n"
    "4. RabbitMQ Streaming (Part D): Ingests real-time transactional orders and driver dispatches through topic exchanges with reliable ACK/NACK semantics."
)

p_e2 = doc.add_paragraph()
p_e2.paragraph_format.space_before = Pt(14)
p_e2.add_run("E2. Reflection: Challenge Encountered, Root Cause, and Solution\n").bold = True
p_e2.add_run(
    "One major issue encountered occurred during the deployment of Mage AI in Google Colab. "
    "When attempting to install mage-ai via pip, the installation aborted with a C-compilation failure: 'Failed to build Pillow when getting requirements to build wheel'.\n\n"
    "Investigation & Root Cause Analysis:\n"
    "By checking the environment runtime via Python sys.version, I observed that Google Colab had recently upgraded its base environment to Python 3.13. "
    "The mage-ai package and its pinned Pillow dependencies lacked pre-compiled binary wheels for Python 3.13 on Linux, forcing pip to attempt building from source without required C development headers.\n\n"
    "Resolution:\n"
    "Rather than downgrading the entire system, I installed the 'uv' package manager to spin up an isolated Python 3.11 standalone environment ('uv venv .venv --python 3.11'). "
    "Because Python 3.11 has full pre-built binary wheel coverage across PyPI, mage-ai and its machine learning dependencies installed cleanly in under 15 seconds with zero build errors."
)

# ==========================================
# APPENDIX: SCREENSHOT CHECKLIST
# ==========================================
doc.add_page_break()
p_app = doc.add_paragraph()
p_app.add_run("Appendix: Verification Screenshots Checklist")
style_heading(p_app, 16, COLOR_PRIMARY, bold=True)

p_app_desc = doc.add_paragraph()
p_app_desc.add_run("Please insert your saved verification screenshots below each corresponding section header:")

screens = [
    ("Figure 1: Part A3 — Green (Passing) GitHub Actions CI Workflow Run", "Insert passing pytest screenshot showing 3 passed tests"),
    ("Figure 2: Part A3 — Red (Failing) GitHub Actions CI Workflow Run", "Insert failing pytest screenshot showing intentional split ratio break"),
    ("Figure 3: Part B1 — Baseline Snowflake Output", "Insert output showing 8 bronze, 6 silver clean, 2 quarantine, 4 gold orders"),
    ("Figure 4: Part B3 — Reasons Array Before Change", "Insert quarantine query output showing ['bad_email', 'bad_pincode']"),
    ("Figure 5: Part B3 — Reasons Array After Change", "Insert silver.orders_checked output showing ['bad_email', 'bad_pincode', 'unsupported_currency']"),
    ("Figure 6: Part B4 — Arjun SCD2 and Gold Totals", "Insert output showing 2 rows for CUST-02 and 161 total loyalty points"),
    ("Figure 7: Part B5 — Data Quality Check Failure Alert", "Insert quality_checks() output showing 'gold orders with NULL amount_inr ... PROBLEM'"),
    ("Figure 8: Part C1 — Baseline Mage Pipeline Run", "Insert mage run iris_project iris_classifier --test terminal output"),
    ("Figure 9: Part C2 — Test Gate Results (max_depth 1 through 5)", "Insert terminal log showing blocked predictions for depth 1 and success for depths 2-5"),
    ("Figure 10: Part C3 — Mage UI Pipeline Graph with Evaluation Branch", "Insert Mage web UI graph showing train_model branching into save_results and evaluate_model"),
    ("Figure 11: Part D2 & D3 — RabbitMQ Dispatcher and Driver Logs", "Insert terminal output showing routed messages and NACK for missing zone")
]

for title, desc in screens:
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(10)
    sp.add_run(f"{title}\n").bold = True
    sp.add_run(f"[{desc}]\n\n")

# Save document
output_path = r"c:\Users\ashut\OneDrive\Desktop\data_engineering\repo\freshcart-pipelines\RollNo_Name_Pipelines.docx"
doc.save(output_path)

output_path_root = r"c:\Users\ashut\OneDrive\Desktop\data_engineering\RollNo_Name_Pipelines.docx"
doc.save(output_path_root)

print(f"Generated DOCX at: {output_path}")
print(f"Generated DOCX copy at: {output_path_root}")
