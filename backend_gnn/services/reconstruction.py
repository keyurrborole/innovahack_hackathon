"""
3D Reconstruction Service
Converts processed graph data back into a renderable 3D mesh.
Supports GLB export via trimesh, with a pure-Python OBJ fallback.
"""
import logging
import os
import struct
import json
import numpy as np

logger = logging.getLogger(__name__)

try:
    import trimesh
    HAS_TRIMESH = True
except ImportError:
    HAS_TRIMESH = False


def _export_glb_pure(vertices: np.ndarray, faces: np.ndarray, output_path: str):
    """
    Export a mesh as a minimal GLB (glTF 2.0 binary) WITHOUT trimesh.
    Produces a valid .glb file that Three.js / R3F can load.
    """
    verts = vertices.astype(np.float32)
    indices = faces.astype(np.uint32).flatten()

    # Compute bounding box for accessor
    v_min = verts.min(axis=0).tolist()
    v_max = verts.max(axis=0).tolist()

    # Binary buffers
    vert_bytes = verts.tobytes()
    idx_bytes = indices.tobytes()
    bin_data = vert_bytes + idx_bytes

    # Pad binary to 4-byte alignment
    pad = (4 - len(bin_data) % 4) % 4
    bin_data += b'\x00' * pad

    gltf = {
        "asset": {"version": "2.0", "generator": "ModelX-GNN-Pipeline"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{
            "primitives": [{
                "attributes": {"POSITION": 0},
                "indices": 1,
                "mode": 4  # TRIANGLES
            }]
        }],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,  # FLOAT
                "count": len(verts),
                "type": "VEC3",
                "min": v_min,
                "max": v_max,
            },
            {
                "bufferView": 1,
                "componentType": 5125,  # UNSIGNED_INT
                "count": len(indices),
                "type": "SCALAR",
                "min": [int(indices.min())],
                "max": [int(indices.max())],
            },
        ],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(vert_bytes),
                "target": 34962,  # ARRAY_BUFFER
            },
            {
                "buffer": 0,
                "byteOffset": len(vert_bytes),
                "byteLength": len(idx_bytes),
                "target": 34963,  # ELEMENT_ARRAY_BUFFER
            },
        ],
        "buffers": [{"byteLength": len(bin_data)}],
    }

    # Encode JSON chunk
    json_str = json.dumps(gltf, separators=(",", ":"))
    json_bytes = json_str.encode("utf-8")
    json_pad = (4 - len(json_bytes) % 4) % 4
    json_bytes += b' ' * json_pad

    # GLB header: magic + version + total length
    total_length = 12 + 8 + len(json_bytes) + 8 + len(bin_data)

    with open(output_path, "wb") as f:
        # Header
        f.write(struct.pack("<I", 0x46546C67))  # magic: 'glTF'
        f.write(struct.pack("<I", 2))  # version
        f.write(struct.pack("<I", total_length))
        # JSON chunk
        f.write(struct.pack("<I", len(json_bytes)))
        f.write(struct.pack("<I", 0x4E4F534A))  # 'JSON'
        f.write(json_bytes)
        # BIN chunk
        f.write(struct.pack("<I", len(bin_data)))
        f.write(struct.pack("<I", 0x004E4942))  # 'BIN\0'
        f.write(bin_data)


def reconstruct_mesh(
    processed_graph: dict,
    original_mesh_path: str,
    output_path: str,
) -> str:
    """
    Reconstruct a 3D mesh from GNN-processed graph data.

    Blends original geometry with GNN output (85/15) to produce a
    subtly modified mesh, then exports as GLB.
    """
    try:
        # Get GNN-updated vertex positions
        gnn_verts = processed_graph["updated_node_features"]

        # Load original mesh to get topology (faces)
        ext = os.path.splitext(original_mesh_path)[1].lower()

        if HAS_TRIMESH:
            mesh = trimesh.load(original_mesh_path, force="mesh")
            if isinstance(mesh, trimesh.Scene):
                geometries = list(mesh.geometry.values())
                if not geometries:
                    raise ValueError("No geometry in scene.")
                mesh = trimesh.util.concatenate(
                    tuple(trimesh.Trimesh(vertices=g.vertices, faces=g.faces) for g in geometries)
                )
            original_verts = np.array(mesh.vertices)
            faces = np.array(mesh.faces)
        else:
            # Use built-in OBJ parser
            from .normalization import _parse_obj_file
            if ext != ".obj":
                raise ValueError(f"Format '{ext}' requires trimesh. Only .obj supported without it.")
            parsed = _parse_obj_file(original_mesh_path)
            original_verts = parsed["vertices"]
            faces = parsed["faces"]

        # Blend: 85% original + 15% GNN output (subtle modification)
        if len(original_verts) == len(gnn_verts):
            blended = 0.85 * original_verts + 0.15 * gnn_verts
        else:
            logger.warning(
                f"Vertex count mismatch ({len(original_verts)} vs {len(gnn_verts)}). "
                f"Using original geometry."
            )
            blended = original_verts

        # Export as GLB
        if HAS_TRIMESH:
            new_mesh = trimesh.Trimesh(vertices=blended, faces=faces)
            new_mesh.export(output_path, file_type="glb")
        else:
            _export_glb_pure(blended, faces, output_path)

        logger.info(f"Reconstructed mesh saved to {output_path}")
        return str(output_path)

    except Exception as e:
        logger.error(f"Reconstruction error for {original_mesh_path}: {e}")
        raise
