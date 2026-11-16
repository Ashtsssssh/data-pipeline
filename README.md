# data-pipeline

**Assignment: From Git to Gold** — Data Engineering Pipeline Orchestration

This repository contains four integrated components of a modern data platform:

## Repository Structure

```
freshcart-pipelines/
├── elt/                          # Part B: FreshCart ELT on Snowflake
│   └── freshcart_notebook.ipynb  # Snowflake bronze→silver→gold pipeline
├── iris_project/                 # Part C: Mage ML Pipeline
│   ├── pipelines/iris_classifier/
│   ├── data_loaders/
│   ├── transformers/
│   └── data_exporters/
├── stream/                       # Part D: RabbitMQ Food-order Stream
│   ├── dispatcher.py
│   └── driver.py
├── tests/                        # Part A: CI/CD Tests
│   └── test_prepare_data.py
└── .github/workflows/ci.yml      # GitHub Actions CI
```

## Components

### Part A — Git & CI/CD
GitHub Actions workflow that runs pytest on every push.

### Part B — FreshCart ELT (Snowflake)
A full ELT pipeline that extracts raw order data, loads it to Snowflake bronze, transforms it through silver/dim/ref layers, and produces a gold fact table with loyalty points.

### Part C — Mage ML Pipeline (Iris Classifier)
An orchestrated ML pipeline using Mage AI: loads the Iris dataset, prepares an 80/20 split, trains a Decision Tree classifier, and saves predictions — with `@test` gates between blocks.

### Part D — RabbitMQ Food-order Stream
A topic-exchange dispatcher/driver system simulating Zomato-style food-order routing across Bangalore and Chennai zones, with ACK/NACK handling.

## Setup

```bash
pip install -r requirements.txt
```

## Running Tests

```bash
pytest tests/
```

## Running the ML Pipeline

```bash
mage run iris_project iris_classifier --test
```

## Running the Stream

```bash
# Terminal 1 — dispatcher
python stream/dispatcher.py

# Terminal 2+ — drivers
python stream/driver.py Ravi "bangalore.koramangala.*"
python stream/driver.py Meena "bangalore.*.food"
```

## Platform Requirements
- Python 3.12
- Snowflake trial account
- Mage AI (`pip install mage-ai`)
- RabbitMQ broker (local or CloudAMQP free tier)
