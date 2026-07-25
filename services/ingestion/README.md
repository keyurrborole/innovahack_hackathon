# Ingestion Service

## Overview
This service contains a Kafka producer and consumer that validate schemas for banking transactions.
The producer generates synthetic data and injects specific fraud patterns (Circular Flows, Structuring, and Mule Networks) into the dataset.

## Setup
1. Create a virtual environment: `python3 -m venv venv`
2. Activate and install: `source venv/bin/activate && pip install -r requirements.txt`
3. Optional: Configure `.env` using `.env.example`.

## Usage
Start Kafka inside the `/infra` directory first.

Run the consumer:
```bash
python consumer.py
```

Run the producer:
```bash
python producer.py
```
