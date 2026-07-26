"""
Vercel Serverless Function — Subscription Leak Detector API
============================================================
This file is the ASGI entrypoint for Vercel Python Functions.
Vercel routes /gnn-api/* → this handler (see vercel.json rewrites).

In local dev, Vite proxy handles /gnn-api/* → localhost:8001 instead.
"""
import sys
import os
import csv
import io
import logging

# Make backend_gnn importable (Vercel deploys the full repo)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from backend_gnn.subscription_engine import (
    analyse_transactions,
    parse_sms_text,
    _parse_date,
    _parse_amount,
    _detect_columns,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vercel-sub-api")

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Subscription Leak Detector API",
    description="Detects recurring subscriptions from bank statements and SMS exports",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _parse_csv_transactions(content: str) -> list[dict]:
    """Auto-detect columns and extract transactions from a CSV string."""
    transactions = []
    try:
        reader = csv.DictReader(io.StringIO(content))
        headers = list(reader.fieldnames or [])
        col_map = _detect_columns(headers)
        date_col   = col_map.get("date")
        amount_col = col_map.get("amount")
        desc_col   = col_map.get("desc")

        rows = list(reader)

        if date_col and amount_col:
            for row in rows:
                date   = _parse_date(row.get(date_col, ""))
                amount = _parse_amount(row.get(amount_col, ""))
                desc   = row.get(desc_col, "") if desc_col else ""
                if date and amount and amount > 0:
                    transactions.append({"date": date, "description": desc, "amount": amount})
        else:
            # Positional fallback: date=col0, desc=col1, amount=last debit col
            for row in rows:
                vals = list(row.values())
                if len(vals) >= 3:
                    date   = _parse_date(vals[0])
                    amount = _parse_amount(vals[-2]) or _parse_amount(vals[-1])
                    desc   = vals[1] if len(vals) > 2 else ""
                    if date and amount and amount > 0:
                        transactions.append({"date": date, "description": desc, "amount": amount})
    except Exception as e:
        logger.warning(f"CSV parse error: {e}")
    return transactions


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
@app.get("/gnn-api/health")
def health():
    return {"status": "healthy", "service": "subscription-leak-detector", "version": "1.0.0"}


@app.post("/analyse")
@app.post("/gnn-api/analyse")
async def analyse_statement(file: UploadFile = File(...)):
    """
    Upload a bank statement (CSV/TXT/TSV) and detect subscription leaks.
    Returns: subscriptions, leak scores, action plans, savings estimates.
    """
    filename = file.filename or "upload"
    ext = os.path.splitext(filename)[1].lower()
    logger.info(f"Received file: {filename}")

    try:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8", errors="replace")

        if ext in (".csv", ".tsv"):
            transactions = _parse_csv_transactions(content)
        elif ext in (".txt",):
            transactions = _parse_csv_transactions(content)
            if len(transactions) < 2:
                transactions = parse_sms_text(content)
        else:
            raise ValueError(
                f"Unsupported format '{ext}'. Upload a CSV, TXT, or TSV file."
            )

        if not transactions:
            raise ValueError(
                "No transactions found. Ensure the file has date, description, and amount columns."
            )

        logger.info(f"Parsed {len(transactions)} transactions")
        result = analyse_transactions(transactions)
        result["transactions_parsed"] = len(transactions)
        return JSONResponse(content=result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Catch-all: forward any sub-path (e.g. /gnn-api/analyse → /analyse)
@app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS"])
async def catch_all(path: str):
    return JSONResponse({"error": f"Unknown route: /{path}"}, status_code=404)


# ── Vercel ASGI handler ───────────────────────────────────────────────────────
handler = Mangum(app, lifespan="off")
