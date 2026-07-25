"""
Mock GNN Inference Pipeline
Uses PyTorch Geometric if available, falls back to pure numpy simulation.
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Try importing PyG — if broken or missing, use numpy mock
HAS_PYG = False
try:
    import torch
    import torch.nn as nn
    from torch_geometric.data import Data
    from torch_geometric.nn import SAGEConv

    class MockGraphSAGE(nn.Module):
        """2-layer GraphSAGE model for mock inference."""

        def __init__(self, in_channels=6, hidden_channels=32, out_channels=3):
            super().__init__()
            self.conv1 = SAGEConv(in_channels, hidden_channels)
            self.conv2 = SAGEConv(hidden_channels, out_channels)
            self.relu = nn.ReLU()
            self.dropout = nn.Dropout(p=0.2)

        def forward(self, x, edge_index):
            x = self.conv1(x, edge_index)
            x = self.relu(x)
            x = self.dropout(x)
            x = self.conv2(x, edge_index)
            return x

    HAS_PYG = True
    logger.info("PyTorch Geometric available — real GNN inference enabled.")
except Exception as e:
    logger.warning(f"PyG not available ({e}). Using numpy-based mock GNN inference.")


def _numpy_mock_inference(graph_data: dict) -> dict:
    """
    Pure numpy mock of a 2-layer graph message-passing network.
    Simulates neighbourhood aggregation on the mesh graph.
    """
    node_features = graph_data["node_features"]  # (N, 6)
    edge_index = graph_data["edge_index"]  # (E, 2)
    n_nodes = len(node_features)

    # Initialize random "weights" (deterministic seed for reproducibility)
    rng = np.random.RandomState(42)
    W1 = rng.randn(6, 32).astype(np.float32) * 0.1
    W2 = rng.randn(32, 3).astype(np.float32) * 0.1

    # Layer 1: aggregate neighbour features + transform
    h = node_features.astype(np.float32)
    if len(edge_index) > 0:
        # Build adjacency aggregation (mean of neighbours)
        agg = np.zeros((n_nodes, 6), dtype=np.float32)
        counts = np.zeros(n_nodes, dtype=np.float32)
        for src, dst in edge_index:
            agg[dst] += h[src]
            agg[src] += h[dst]
            counts[dst] += 1
            counts[src] += 1
        counts = np.maximum(counts, 1)[:, None]
        h = np.concatenate([h, agg / counts], axis=-1)[:, :6]  # simplified

    h = h @ W1  # (N, 32)
    h = np.maximum(h, 0)  # ReLU

    # Layer 2: transform to output dimensions
    out = h @ W2  # (N, 3)

    confidence = rng.uniform(0.75, 0.98, size=(n_nodes,))

    return {
        "updated_node_features": out,
        "confidence_scores": confidence,
        "num_nodes": n_nodes,
    }


def _pyg_inference(graph_data: dict) -> dict:
    """Run inference using actual PyTorch Geometric GraphSAGE."""
    import torch

    node_features = torch.tensor(graph_data["node_features"], dtype=torch.float)
    edge_idx = graph_data["edge_index"]

    if edge_idx.size > 0:
        edge_index = torch.tensor(edge_idx, dtype=torch.long).t().contiguous()
        # Undirected: add reverse edges
        edge_index = torch.cat([edge_index, edge_index[[1, 0]]], dim=1)
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)

    model = MockGraphSAGE(in_channels=node_features.shape[1], hidden_channels=32, out_channels=3)
    model.eval()

    with torch.no_grad():
        out = model(node_features, edge_index)

    n_nodes = len(out)
    return {
        "updated_node_features": out.numpy(),
        "confidence_scores": np.random.uniform(0.75, 0.98, size=(n_nodes,)),
        "num_nodes": n_nodes,
    }


def run_inference(graph_data: dict) -> dict:
    """
    Run GNN inference on graph data.
    Uses PyG if available, otherwise falls back to numpy mock.
    """
    try:
        if graph_data.get("vertex_count", 0) == 0:
            raise ValueError("Empty graph — nothing to process.")

        if HAS_PYG:
            logger.info("Running GNN inference with PyTorch Geometric...")
            result = _pyg_inference(graph_data)
        else:
            logger.info("Running GNN inference with numpy mock...")
            result = _numpy_mock_inference(graph_data)

        logger.info(f"GNN inference complete: {result['num_nodes']} nodes processed.")
        return result

    except Exception as e:
        logger.error(f"Error during GNN inference: {e}")
        raise
