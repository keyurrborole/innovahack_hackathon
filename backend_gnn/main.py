"""
Model X — GNN 3D Pipeline
FastAPI microservice for 3D file upload, graph normalization,
GNN inference, and mesh reconstruction.
"""
import os
import uuid
import logging
import shutil
import traceback
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .services.normalization import mesh_to_graph
from .services.gnn_inference import run_inference
from .services.reconstruction import reconstruct_mesh

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-5s | %(message)s",
)
logger = logging.getLogger("gnn-pipeline")

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Model X GNN 3D Pipeline",
    description="MVP M0/M1 — Topological Normalization & Graph Neural Network Processing",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MVP dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "local_s3_mock" / "raw_assets"
PROCESSED_DIR = BASE_DIR / "local_s3_mock" / "processed_assets"
GRAPH_DIR = BASE_DIR / "local_s3_mock" / "graph_datasets"

ALLOWED_EXTENSIONS = {".obj", ".glb", ".gltf", ".stl", ".ply"}


# ── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    for d in [RAW_DIR, PROCESSED_DIR, GRAPH_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Storage ready at {BASE_DIR / 'local_s3_mock'}")
    logger.info("GNN 3D Pipeline is running.")


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "gnn-3d-pipeline", "version": "0.1.0"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a 3D model file, process through the GNN pipeline,
    and return a processed GLB asset.
    """
    filename = file.filename or "unknown"
    logger.info(f"Upload received: {filename}")

    try:
        # ── Validate extension ───────────────────────────────────────────
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format '{ext}'. "
                f"Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # ── Save raw file ────────────────────────────────────────────────
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        raw_path = RAW_DIR / unique_name

        with open(raw_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Saved raw file: {raw_path.name}")

        # ── Pipeline Stage 1: Topological Normalization ──────────────────
        logger.info("Stage 1/3: Topological Normalization...")
        graph_data = mesh_to_graph(str(raw_path))

        # ── Pipeline Stage 2: GNN Inference ──────────────────────────────
        logger.info("Stage 2/3: GNN Inference...")
        processed_graph = run_inference(graph_data)

        # ── Pipeline Stage 3: 3D Reconstruction ─────────────────────────
        logger.info("Stage 3/3: 3D Reconstruction...")
        output_name = f"processed_{unique_name.rsplit('.', 1)[0]}.glb"
        output_path = PROCESSED_DIR / output_name
        reconstruct_mesh(processed_graph, str(raw_path), str(output_path))

        logger.info(f"Pipeline complete: {output_name}")

        return JSONResponse(content={
            "status": "success",
            "original_file": unique_name,
            "processed_file": output_name,
            "processed_url": f"/processed/{output_name}",
            "pipeline_stats": {
                "vertex_count": graph_data["vertex_count"],
                "face_count": graph_data["face_count"],
                "num_nodes": processed_graph["num_nodes"],
            },
        })

    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(f"Pipeline error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.get("/processed/{filename}")
def get_processed_file(filename: str):
    """Serve a processed GLB asset."""
    file_path = PROCESSED_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Processed file not found.")
    return FileResponse(
        path=str(file_path),
        media_type="model/gltf-binary",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-cache",
        },
    )
