"""
Model X — GNN 3D Pipeline + Subscription Leak Detector
FastAPI microservice (port 8001)
"""
import os
import csv
import io
import uuid
import logging
import shutil
import traceback
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .services.normalization import mesh_to_graph
from .services.gnn_inference import run_inference
from .services.reconstruction import reconstruct_mesh
from .subscription_engine import (
    analyse_transactions,
    parse_sms_text,
    _parse_date,
    _parse_amount,
    _detect_columns,
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-5s | %(message)s",
)
logger = logging.getLogger("gnn-pipeline")

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Model X — GNN Pipeline & Subscription Detector",
    description="MVP M0/M1: 3D GNN Pipeline + Bank Statement Subscription Leak Detection",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent.parent
RAW_DIR       = BASE_DIR / "local_s3_mock" / "raw_assets"
PROCESSED_DIR = BASE_DIR / "local_s3_mock" / "processed_assets"
GRAPH_DIR     = BASE_DIR / "local_s3_mock" / "graph_datasets"

MESH_EXTENSIONS = {".obj", ".glb", ".gltf", ".stl", ".ply"}
DATA_EXTENSIONS = {".csv", ".txt", ".tsv"}


@app.on_event("startup")
async def startup_event():
    for d in [RAW_DIR, PROCESSED_DIR, GRAPH_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Model X GNN + Subscription Detector running.")


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "gnn-3d-pipeline", "version": "0.2.0"}


# ── 3D upload ─────────────────────────────────────────────────────────────────
@app.post("/upload")
async def upload_3d_file(file: UploadFile = File(...)):
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()
    logger.info(f"3D upload: {filename}")
    try:
        if ext not in MESH_EXTENSIONS:
            raise ValueError(f"Unsupported format '{ext}'. Accepted: {', '.join(sorted(MESH_EXTENSIONS))}")

        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        raw_path    = RAW_DIR / unique_name
        with open(raw_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        graph_data      = mesh_to_graph(str(raw_path))
        processed_graph = run_inference(graph_data)
        output_name     = f"processed_{unique_name.rsplit('.', 1)[0]}.glb"
        reconstruct_mesh(processed_graph, str(raw_path), str(PROCESSED_DIR / output_name))

        return JSONResponse(content={
            "status": "success",
            "processed_url": f"/processed/{output_name}",
            "pipeline_stats": {
                "vertex_count": graph_data["vertex_count"],
                "face_count":   graph_data["face_count"],
                "num_nodes":    processed_graph["num_nodes"],
            },
        })
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(500, detail=str(e))


@app.get("/processed/{filename}")
def get_processed_file(filename: str):
    p = PROCESSED_DIR / filename
    if not p.exists():
        raise HTTPException(404, "File not found.")
    return FileResponse(str(p), media_type="model/gltf-binary",
                        headers={"Access-Control-Allow-Origin": "*"})


# ── Subscription analyse ───────────────────────────────────────────────────────
def _parse_csv_transactions(content: str) -> list[dict]:
    """Parse CSV bank statement into transaction list."""
    transactions = []
    try:
        reader = csv.DictReader(io.StringIO(content))
        headers = reader.fieldnames or []
        col_map = _detect_columns(list(headers))
        date_col   = col_map.get("date")
        amount_col = col_map.get("amount")
        desc_col   = col_map.get("desc")

        if not date_col or not amount_col:
            # Try positional — assume first col=date, last-1=debit, second=description
            rows = list(reader)
            for row in rows:
                vals = list(row.values())
                if len(vals) >= 3:
                    date = _parse_date(vals[0])
                    amount = _parse_amount(vals[-2]) or _parse_amount(vals[-1])
                    desc = vals[1] if len(vals) > 2 else ""
                    if date and amount and amount > 0:
                        transactions.append({"date": date, "description": desc, "amount": amount})
        else:
            for row in reader:
                date = _parse_date(row.get(date_col, ""))
                raw_amount = row.get(amount_col, "")
                amount = _parse_amount(raw_amount)
                desc = row.get(desc_col, "") if desc_col else ""
                if date and amount and amount > 0:
                    transactions.append({"date": date, "description": desc, "amount": amount})
    except Exception as e:
        logger.warning(f"CSV parse error: {e}")
    return transactions


@app.post("/analyse")
async def analyse_statement(file: UploadFile = File(...)):
    """
    Upload a bank statement (CSV), SMS export (TXT/CSV), or transaction file.
    Returns subscription detection results with leak scores and action plans.
    """
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()
    logger.info(f"Statement upload: {filename}")

    try:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8", errors="replace")

        transactions = []

        if ext in (".csv", ".tsv"):
            transactions = _parse_csv_transactions(content)
        elif ext in (".txt",):
            # Try CSV first, then SMS parser
            transactions = _parse_csv_transactions(content)
            if len(transactions) < 2:
                transactions = parse_sms_text(content)
        else:
            raise ValueError(f"Unsupported format '{ext}'. Upload CSV, TXT, or TSV.")

        if not transactions:
            raise ValueError(
                "Could not extract any transactions. "
                "Ensure your file has date, description, and amount columns."
            )

        logger.info(f"Parsed {len(transactions)} transactions from {filename}")
        result = analyse_transactions(transactions)
        result["transactions_parsed"] = len(transactions)
        return JSONResponse(content=result)

    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        logger.error(traceback.format_exc())
        raise HTTPException(500, detail=str(e))
