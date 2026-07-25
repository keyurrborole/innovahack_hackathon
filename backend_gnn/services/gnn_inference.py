import logging
import numpy as np
import torch
import torch.nn as nn
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv

logger = logging.getLogger(__name__)

class MockGraphSAGE(nn.Module):
    def __init__(self, in_channels=6, hidden_channels=32, out_channels=3):
        super(MockGraphSAGE, self).__init__()
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

def run_inference(graph_data: dict) -> dict:
    try:
        if graph_data.get("vertex_count", 0) == 0:
            raise ValueError("Empty graph provided for inference.")
            
        node_features = torch.tensor(graph_data["node_features"], dtype=torch.float)
        
        # PyG edge_index needs to be [2, num_edges]
        if graph_data["edge_index"].size > 0:
            edge_index = torch.tensor(graph_data["edge_index"], dtype=torch.long).t().contiguous()
            # For undirected graph, add reverse edges
            edge_index = torch.cat([edge_index, edge_index[[1, 0]]], dim=1)
        else:
            edge_index = torch.empty((2, 0), dtype=torch.long)
            
        data = Data(x=node_features, edge_index=edge_index)
        
        model = MockGraphSAGE(in_channels=node_features.shape[1], hidden_channels=32, out_channels=3)
        model.eval()
        
        with torch.no_grad():
            out = model(data.x, data.edge_index)
            
        updated_features = out.numpy()
        confidence = np.random.uniform(0.7, 0.99, size=(len(updated_features),))
        
        logger.info(f"Ran GNN inference on {len(updated_features)} nodes")
        
        return {
            "updated_node_features": updated_features,
            "confidence_scores": confidence,
            "num_nodes": len(updated_features)
        }
    except Exception as e:
        logger.error(f"Error during GNN inference: {str(e)}")
        raise e
