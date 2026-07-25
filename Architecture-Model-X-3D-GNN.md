# Architecture: Model X — GNN-Driven 3D Element & Spatial Architecture System

**Companion doc to:** PRD-Model-X-3D-GNN.md  
**Owner:** Keyur Borole  
**Registration Number:** 245891332  

---

## 1. Design Principles

1. **Graph-First Representation.** 3D elements (meshes, point clouds) are inherently non-Euclidean. Raw spatial data must be immediately transformed into graph structures (nodes as vertices/points, edges as spatial proximity or mesh topology) for all downstream ML tasks.
2. **Modular, Independently-Scalable Pipeline.** Ingestion → Voxelization/Graph Extraction → GNN Inference → 3D Reconstruction → Presentation are distinct services. Model training and inference must scale independently from the frontend rendering engine.
3. **Lossless Spatial Integrity.** Every graphical modification or feature extraction must trace back to the original topological coordinates. Downsampling for performance should maintain the underlying geometric invariants.
4. **Batch Processing for Heavy Computations, Real-Time for Rendering.** GNN message-passing and 3D generation run asynchronously. The presentation layer strictly consumes cached, optimized assets (e.g., GLTF/GLB) for high-FPS browser rendering.

## 2. High-Level Architecture

The system flows through six primary stages to convert raw 3D assets into intelligent, GNN-processed graphical elements:

```text
Sources (3D Assets) → Ingestion & Parsing → Topological Normalization → GNN Engine → Asset Reconstruction → Presentation (WebGL)
                                                                             ↓
                                                                  Cloud Storage & Metadata
```

## 3. Components

### 3.1 Data Ingestion Layer

| Source | Mechanism | Notes |
|---|---|---|
| Static 3D Models | OBJ, STL, GLTF/GLB upload | Requires immediate validation of mesh manifold and vertex counts. |
| Point Cloud Data | PLY, XYZ | Scanned environments or raw sensor data. Needs density normalization. |
| Procedural Gen | Scripted API inputs | Programmatically generated base shapes (e.g., primitives) fed directly as coordinate matrices. |

Each source emits a normalized `RawSpatialEvent`:
```json
{
  "source": "enum(mesh, point_cloud, procedural)",
  "raw_payload_uri": "s3://...",
  "vertex_count": "integer",
  "received_at": "timestamp",
  "project_id": "hashed_id"
}
```

### 3.2 Topological Normalization Service

- **Mesh-to-Graph Conversion:** Parses OBJs/GLTFs. Vertices become node features (XYZ coordinates, RGB, normals); faces/edges become the adjacency matrix.
- **Point Cloud Sampling:** Uses Farthest Point Sampling (FPS) to reduce dense point clouds to a uniform node count, followed by k-Nearest Neighbors (k-NN) to construct dynamic edges.
- **Feature Canonicalization:** Normalizes all spatial coordinates to a unit sphere ([-1, 1] range) to ensure scale-invariant GNN training.
- Output: A standardized `GraphData` object — `{node_features, edge_index, edge_attributes, batch_mapping}`.

### 3.3 Graphical Neural Network (GNN) Engine

- Takes `GraphData` and routes it through a specialized Message Passing Neural Network (MPNN).
- **Architecture Flow:**
  - *Encoder:* Graph Convolutional layers (e.g., GraphSAGE or GAT) to embed local spatial neighborhoods.
  - *Latent Space:* A bottleneck layer that captures the global geometric shape and topological style.
  - *Decoder:* Translates the latent embeddings back into modified spatial coordinates or classification labels (e.g., semantic segmentation of the 3D object).
- **Dynamic Edge Updating:** For generation tasks, edge connections are dynamically recomputed (EdgeConv) at each layer to capture new structural relationships as the shape evolves.
- Output: `ProcessedGraph` — `{updated_node_features, confidence_scores, predicted_classes}`.

### 3.4 3D Reconstruction & Optimization

- Converts the GNN's output graph back into renderable 3D formats.
- **Mesh Generation:** Uses Marching Cubes or Poisson Surface Reconstruction if the GNN outputs point clouds or implicit functions.
- **Asset Optimization:** Decimates the resulting high-poly mesh into a web-optimized, low-poly GLB file with baked textures.
- Output: A `RenderableAsset` entity — `{asset_url, bounding_box, material_params, face_count}`.

### 3.5 Storage & Data Model

| Store | Contents | Retention |
|---|---|---|
| `raw_assets_bucket` | Uploaded OBJ/STL files | Long-lived, version-controlled |
| `graph_datasets` | HDF5 or PyTorch Geometric `.pt` files | Transitory (purged after model update/inference) |
| `processed_assets` | Optimized GLB files ready for web | Long-lived, cached via CDN |
| `spatial_metadata` | DynamoDB tables mapping project IDs to asset URLs, vertex counts, and GNN inference metadata | Persistent |

### 3.6 Presentation Layer

- **WebGL / Three.js Canvas:** The primary interface for users to interact with the GNN-generated elements.
- **Dynamic Shader Injection:** Applies custom GLSL shaders based on the GNN's semantic outputs (e.g., glowing edges where the GNN detected high structural stress or specific stylistic zones).
- **State Management:** Handles orbital controls, zoom, and real-time material swapping without requiring a round-trip to the inference backend.

## 4. Suggested Tech Stack

| Layer | Suggestion |
|---|---|
| **Backend / API** | Python (FastAPI) for ML integration, managed via containerized instances. |
| **GNN Framework** | PyTorch Geometric (PyG) or Deep Graph Library (DGL) for highly optimized message-passing operations. |
| **Compute / Inference** | Amazon EC2 (G4/G5 instances with NVIDIA GPUs) for accelerated tensor operations. |
| **Data Storage** | Amazon S3 for raw/processed 3D object storage; Amazon DynamoDB for ultra-low latency metadata lookups. |
| **Frontend Rendering** | React Three Fiber (R3F) and Three.js. |
| **Geometry Processing** | Open3D or Trimesh for server-side topological calculations and conversions. |

## 5. Data Flow (Narrative)

1. A 3D design file is uploaded via the client interface and securely stored in an S3 bucket.
2. An event triggers the Topological Normalization Service, which downloads the asset, parses the geometry using Trimesh, and constructs an adjacency matrix.
3. The normalized graph data is passed to the GPU-backed EC2 inference instances.
4. The GNN Engine performs message passing, applying structural modifications, style transfers, or semantic segmentation directly onto the graph's nodes.
5. The 3D Reconstruction service translates the updated graph back into a spatial mesh, bakes the visual properties, and exports a lightweight GLB file.
6. The new asset is uploaded back to S3, metadata is logged in DynamoDB, and a WebSocket event notifies the frontend.
7. The React Three Fiber canvas dynamically loads the updated asset via a CDN for user interaction.

## 6. Scalability & Reliability

- **Asynchronous Inference:** Processing 3D graphs is computationally expensive. The API must accept the upload, return a `job_id`, and process the GNN inference in a queue (e.g., Celery/Redis) to prevent HTTP timeouts.
- **Storage Tiering:** Raw, heavy assets (OBJs) and optimized display assets (GLBs) are strictly decoupled. S3 lifecycle policies can archive raw models to Glacier if they remain untouched, while GLBs stay in hot CDN caching.
- **Dynamic Batching:** The inference server batches multiple smaller graph requests together to maximize GPU utilization during forward passes.

## 7. Phased Technical Roadmap

| Phase | Focus |
|---|---|
| **M0: Pipeline Foundation** | Setup S3 ingestion, Three.js presentation layer, and basic mesh-to-graph normalization. |
| **M1: GNN Integration** | Deploy EC2 inference nodes. Implement initial GraphSAGE/GAT model for semantic segmentation of uploaded meshes. |
| **M2: Generative Modifications** | Enable the GNN to alter node coordinates (style transfer, structural smoothing). Add mesh reconstruction (Poisson/Marching Cubes). |
| **M3: Optimization & Real-Time** | Implement aggressive GLB decimation for web. Introduce dynamic WebGL shaders tied to GNN output metadata. |

## 8. Open Technical Questions

1. **Graph Size Limits:** What is the maximum vertex count we allow per model before enforcing server-side downsampling? (Graphs over 100k nodes will severely impact GPU VRAM).
2. **Edge Construction Strategy:** Should we use static k-NN graphs based strictly on initial spatial coordinates, or dynamic edge construction (EdgeConv) that updates per layer?
3. **Texture Mapping:** How do we preserve UV maps through the GNN forward pass and reconstruction phase so that complex textures aren't lost when the geometry shifts?