import logging
import numpy as np
import trimesh

logger = logging.getLogger(__name__)

def mesh_to_graph(file_path: str) -> dict:
    try:
        mesh = trimesh.load(file_path, force='mesh')
        
        # Handle GLB Scenes by concatenating all meshes or extracting the first
        if isinstance(mesh, trimesh.Scene):
            if len(mesh.geometry) == 0:
                raise ValueError("No mesh geometry found in the scene.")
            mesh = trimesh.util.concatenate(
                tuple(trimesh.Trimesh(vertices=g.vertices, faces=g.faces) 
                      for g in mesh.geometry.values())
            )
        
        vertices = np.array(mesh.vertices)
        if hasattr(mesh, 'vertex_normals') and mesh.vertex_normals is not None and len(mesh.vertex_normals) > 0:
            normals = np.array(mesh.vertex_normals)
        else:
            normals = np.zeros_like(vertices)
            
        # Concatenate XYZ with normals
        node_features = np.concatenate([vertices, normals], axis=-1)
        
        # Extract edge index
        if hasattr(mesh, 'edges_unique') and len(mesh.edges_unique) > 0:
            edge_index = np.array(mesh.edges_unique)
        else:
            edge_index = np.array([])
            
        # Normalize vertices
        center = vertices.mean(axis=0)
        centered_vertices = vertices - center
        max_dist = np.max(np.sqrt(np.sum(centered_vertices**2, axis=1)))
        if max_dist > 0:
            normalized_vertices = centered_vertices / max_dist
        else:
            normalized_vertices = centered_vertices
            
        # Update node_features with normalized positions
        node_features[:, :3] = normalized_vertices
        
        logger.info(f"Processed mesh with {len(vertices)} vertices and {len(mesh.faces)} faces")
        
        return {
            "node_features": node_features,
            "edge_index": edge_index,
            "vertex_count": len(vertices),
            "face_count": len(mesh.faces)
        }
    except Exception as e:
        logger.error(f"Error processing mesh {file_path}: {str(e)}")
        raise e
