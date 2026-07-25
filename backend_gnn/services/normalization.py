"""
Topological Normalization Service
Converts 3D mesh files into graph data structures.
Uses trimesh for mesh loading with a pure-Python OBJ fallback.
"""
import logging
import os
import re
import numpy as np

logger = logging.getLogger(__name__)

# Try to import trimesh; fall back to a built-in OBJ parser
try:
    import trimesh
    HAS_TRIMESH = True
    logger.info("Trimesh available — full format support enabled.")
except ImportError:
    HAS_TRIMESH = False
    logger.warning("Trimesh not installed — only .obj files supported via built-in parser.")


def _parse_obj_file(file_path: str) -> dict:
    """Pure-Python Wavefront OBJ parser. No external dependencies."""
    vertices = []
    faces = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("v "):
                parts = line.split()
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif line.startswith("f "):
                parts = line.split()[1:]
                # OBJ faces can be "v", "v/vt", "v/vt/vn", or "v//vn"
                indices = [int(re.split(r"[/]", p)[0]) - 1 for p in parts]
                # Triangulate quads and n-gons via fan triangulation
                for i in range(1, len(indices) - 1):
                    faces.append([indices[0], indices[i], indices[i + 1]])

    if len(vertices) == 0:
        raise ValueError("OBJ file contains no vertices.")

    return {
        "vertices": np.array(vertices, dtype=np.float64),
        "faces": np.array(faces, dtype=np.int64) if faces else np.empty((0, 3), dtype=np.int64),
    }


def _load_mesh(file_path: str) -> dict:
    """Load a mesh from file, returning vertices, faces, and edges."""
    ext = os.path.splitext(file_path)[1].lower()

    if HAS_TRIMESH:
        mesh = trimesh.load(file_path, force="mesh")
        if isinstance(mesh, trimesh.Scene):
            geometries = list(mesh.geometry.values())
            if len(geometries) == 0:
                raise ValueError("No mesh geometry found in the scene.")
            mesh = trimesh.util.concatenate(
                tuple(
                    trimesh.Trimesh(vertices=g.vertices, faces=g.faces)
                    for g in geometries
                )
            )
        vertices = np.array(mesh.vertices)
        faces = np.array(mesh.faces)
        normals = (
            np.array(mesh.vertex_normals)
            if hasattr(mesh, "vertex_normals") and mesh.vertex_normals is not None and len(mesh.vertex_normals) > 0
            else np.zeros_like(vertices)
        )
        edges = np.array(mesh.edges_unique) if hasattr(mesh, "edges_unique") and len(mesh.edges_unique) > 0 else None
    else:
        if ext != ".obj":
            raise ValueError(
                f"File format '{ext}' requires trimesh. Install it with: pip install trimesh\n"
                f"Only .obj is supported without trimesh."
            )
        parsed = _parse_obj_file(file_path)
        vertices = parsed["vertices"]
        faces = parsed["faces"]
        # Compute simple normals (zeros placeholder)
        normals = np.zeros_like(vertices)
        edges = None

    # Build edge list from faces if not provided
    if edges is None and len(faces) > 0:
        edge_set = set()
        for face in faces:
            for i in range(len(face)):
                e = tuple(sorted((int(face[i]), int(face[(i + 1) % len(face)]))))
                edge_set.add(e)
        edges = np.array(list(edge_set), dtype=np.int64)
    elif edges is None:
        edges = np.empty((0, 2), dtype=np.int64)

    return {
        "vertices": vertices,
        "faces": faces,
        "normals": normals,
        "edges": edges,
    }


def mesh_to_graph(file_path: str) -> dict:
    """
    Convert a 3D mesh file into a graph data structure.

    Returns:
        dict with keys:
            - node_features: np.ndarray (N, 6) — XYZ + normals
            - edge_index: np.ndarray (E, 2) — edge list
            - vertex_count: int
            - face_count: int
            - original_vertices: np.ndarray (N, 3) — un-normalized positions
    """
    try:
        mesh = _load_mesh(file_path)
        vertices = mesh["vertices"]
        normals = mesh["normals"]
        edges = mesh["edges"]
        faces = mesh["faces"]

        # Store originals before normalization
        original_vertices = vertices.copy()

        # Normalize to unit sphere [-1, 1]
        center = vertices.mean(axis=0)
        centered = vertices - center
        max_dist = np.max(np.sqrt(np.sum(centered ** 2, axis=1)))
        if max_dist > 0:
            normalized = centered / max_dist
        else:
            normalized = centered

        # Node features: normalized XYZ + normals
        node_features = np.concatenate([normalized, normals], axis=-1)

        logger.info(
            f"Mesh-to-graph complete: {len(vertices)} vertices, "
            f"{len(faces)} faces, {len(edges)} edges"
        )

        return {
            "node_features": node_features,
            "edge_index": edges,
            "vertex_count": int(len(vertices)),
            "face_count": int(len(faces)),
            "original_vertices": original_vertices,
        }
    except Exception as e:
        logger.error(f"Error processing mesh {file_path}: {e}")
        raise
