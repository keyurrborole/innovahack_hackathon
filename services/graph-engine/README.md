# Graph Engine Service

## Overview
This service contains the Neo4j schema definitions and seed Cypher queries for the fraud intelligence platform. 
The schema supports bi-temporal querying (event time vs valid time) and includes efficient indexes for rapid graph traversals.

## Setup
1. Create a virtual environment: `python3 -m venv venv`
2. Activate and install: `source venv/bin/activate && pip install -r requirements.txt`
3. Optional: Configure `.env` if your Neo4j credentials differ from the ones in `docker-compose.yml`.

## Schema Setup
Ensure your Neo4j container is running from the `/infra` directory.

Run the Cypher commands in `schema.cypher` via the Neo4j browser at `http://localhost:7474`, or load them via the cypher-shell:
```bash
cat schema.cypher | docker exec -i fraud-neo4j cypher-shell -u neo4j -p password123
```

## Available Queries
The `queries.py` file contains the Python string definitions for the Cypher graph traversals:
- Circular Flow Detection
- Structuring Pattern Detection
- Dormant Account Activation & Rapid Outflow
- Mule Network Detection (Fan-in -> Fan-out)
