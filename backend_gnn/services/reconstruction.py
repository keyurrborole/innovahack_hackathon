import logging
import numpy as np
import trimesh

logger = logging.getLogger(__name__)

def reconstruct_mesh(processed_graph: dict, original_mesh_path: str, output_path: str) -> str:
    try:
        mesh = trimesh.load(original_mesh_path, force='mesh')
        
        if isinstance(mesh, trimesh.Scene):
            if len(mesh.geometry) == 0:
                raise ValueError("No mesh geometry found in the scene.")
            mesh = trimesh.util.concatenate(
                tuple(trimesh.Trimesh(vertices=g.vertices, faces=g.faces) 
                      for g in mesh.geometry.values())
            )
            
        original_vertices = np.array(mesh.vertices)
        gnn_updated_vertices = processed_graph["updated_node_features"]
        
        # Check for size mismatches
        if len(original_vertices) != len(gnn_updated_vertices):
            logger.warning(f"Vertex count mismatch: original {len(original_vertices)}, gnn {len(gnn_updated_vertices)}. Skipping blend.")
            new_vertices = original_vertices
        else:
            # Subtle blend: 85% original, 15% gnn_updated
            new_vertices = 0.85 * original_vertices + 0.15 * gnn_updated_vertices
            
        new_mesh = trimesh.Trimesh(vertices=new_vertices, faces=mesh.faces)
        new_mesh.export(output_path, file_type='glb')
        
        logger.info(f"Reconstructed mesh exported to {output_path}")
        return str(output_path)
    except Exception as e:
        logger.error(f"Error reconstructing mesh {original_mesh_path}: {str(e)}")
        raise e
