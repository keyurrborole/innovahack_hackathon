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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Model X GNN 3D Pipeline", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "local_s3_mock" / "raw_assets"
PROCESSED_DIR = BASE_DIR / "local_s3_mock" / "processed_assets"
GRAPH_DIR = BASE_DIR / "local_s3_mock" / "graph_datasets"

ALLOWED_EXTENSIONS = {".obj", ".glb", ".gltf", ".stl", ".ply"}

@app.on_event("startup")
async def startup_event():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Created mock S3 directories.")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "gnn-3d-pipeline"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid file extension {ext}. Allowed: {ALLOWED_EXTENSIONS}")
            
        unique_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        raw_path = RAW_DIR / unique_filename
        
        with open(raw_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        graph_data = mesh_to_graph(str(raw_path))
        processed_graph = run_inference(graph_data)
        
        output_filename = f"processed_{unique_filename.rsplit('.', 1)[0]}.glb"
        output_path = PROCESSED_DIR / output_filename
        
        reconstruct_mesh(processed_graph, str(raw_path), str(output_path))
        
        return JSONResponse(content={
            "status": "success",
            "original_file": unique_filename,
            "processed_file": output_filename,
            "processed_url": f"/processed/{output_filename}",
            "pipeline_stats": {
                "vertex_count": graph_data["vertex_count"],
                "face_count": graph_data["face_count"],
                "num_nodes": processed_graph["num_nodes"]
            }
        })
    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Internal server error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/processed/{filename}")
def get_processed_file(filename: str):
    file_path = PROCESSED_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="model/gltf-binary")
