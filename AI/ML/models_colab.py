# pyright: basic
# type: ignore
import os
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv
from sklearn.model_selection import train_test_split
from typing import Tuple, Dict, List, Optional
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx

DATASET_PATH = '/content'


class GraphSAGE(torch.nn.Module):
    def __init__(self, in_channels: int, hidden_channels: int = 64, out_channels: int = 2, dropout: float = 0.3):
        super().__init__()
        self.conv1 = SAGEConv(in_channels, hidden_channels, aggr='mean')
        self.conv2 = SAGEConv(hidden_channels, out_channels, aggr='mean')
        self.dropout = dropout

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        return x

    def get_embeddings(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        return x


def load_elliptic_dataset(dataset_path: str = DATASET_PATH) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    features_df = pd.read_csv(
        os.path.join(dataset_path, 'elliptic_txs_features.csv'),
        header=None
    )
    
    edges_df = pd.read_csv(
        os.path.join(dataset_path, 'elliptic_txs_edgelist.csv')
    )
    
    classes_df = pd.read_csv(
        os.path.join(dataset_path, 'elliptic_txs_classes.csv')
    )
    
    return features_df, edges_df, classes_df


def build_graph_data(
    features_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    classes_df: pd.DataFrame,
    clip_value: float = 5.0
) -> Tuple[Data, Dict[int, int], List[int]]:
    
    tx_ids = features_df.iloc[:, 0].values
    tx_id_to_idx = {tx_id: idx for idx, tx_id in enumerate(tx_ids)}
    
    node_features = features_df.iloc[:, 1:].values.astype(np.float32)
    node_features = np.clip(node_features, -clip_value, clip_value)
    x = torch.tensor(node_features, dtype=torch.float)
    
    valid_edges = edges_df[
        edges_df['txId1'].isin(tx_id_to_idx) & 
        edges_df['txId2'].isin(tx_id_to_idx)
    ]
    
    source_nodes = valid_edges['txId1'].map(tx_id_to_idx).values
    target_nodes = valid_edges['txId2'].map(tx_id_to_idx).values
    edge_index = torch.tensor(np.array([source_nodes, target_nodes]), dtype=torch.long)
    
    y = torch.full((len(tx_ids),), -1, dtype=torch.long)
    
    for _, row in classes_df.iterrows():
        tx_id = row['txId']
        label = row['class']
        
        if tx_id in tx_id_to_idx:
            idx = tx_id_to_idx[tx_id]
            if label == '1' or label == 1:
                y[idx] = 1
            elif label == '2' or label == 2:
                y[idx] = 0
    
    data = Data(x=x, edge_index=edge_index, y=y)
    
    return data, tx_id_to_idx, tx_ids.tolist()


def create_masks(
    data: Data,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    seed: int = 42
) -> Data:
    
    labeled_mask = data.y >= 0
    labeled_indices = torch.where(labeled_mask)[0].numpy()
    labels = data.y[labeled_mask].numpy()
    
    train_idx, temp_idx, train_labels, temp_labels = train_test_split(
        labeled_indices, labels,
        train_size=train_ratio,
        stratify=labels,
        random_state=seed
    )
    
    val_size = val_ratio / (1 - train_ratio)
    val_idx, test_idx = train_test_split(
        temp_idx,
        train_size=val_size,
        stratify=temp_labels,
        random_state=seed
    )
    
    num_nodes = data.x.size(0)
    
    train_mask = torch.zeros(num_nodes, dtype=torch.bool)
    val_mask = torch.zeros(num_nodes, dtype=torch.bool)
    test_mask = torch.zeros(num_nodes, dtype=torch.bool)
    
    train_mask[train_idx] = True
    val_mask[val_idx] = True
    test_mask[test_idx] = True
    
    data.train_mask = train_mask
    data.val_mask = val_mask
    data.test_mask = test_mask
    
    return data


def compute_class_weights(data: Data) -> torch.Tensor:
    labeled_mask = data.y >= 0
    labels = data.y[labeled_mask]
    
    num_licit = (labels == 0).sum().item()
    num_illicit = (labels == 1).sum().item()
    total = num_licit + num_illicit
    
    weight_licit = total / (2.0 * num_licit) if num_licit > 0 else 1.0
    weight_illicit = total / (2.0 * num_illicit) if num_illicit > 0 else 1.0
    
    return torch.tensor([weight_licit, weight_illicit], dtype=torch.float)


def train_epoch(
    model: GraphSAGE,
    data: Data,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    class_weights: Optional[torch.Tensor] = None
) -> float:
    
    model.train()
    optimizer.zero_grad()
    
    out = model(data.x, data.edge_index)

        # 🔒 PREVENT LOGIT EXPLOSION
    out = torch.clamp(out, min=-10.0, max=10.0)
    
    train_mask = data.train_mask.to(device)
    y_train = data.y.to(device)[train_mask]
    out_train = out[train_mask]
    
    if class_weights is not None:
        class_weights = class_weights.to(device)
        loss = F.cross_entropy(out_train, y_train, weight=class_weights)
    else:
        loss = F.cross_entropy(out_train, y_train)
    
    # NaN loss guard: stop training if loss is NaN
    if torch.isnan(loss):
        raise ValueError("NaN loss detected — training stopped to prevent model corruption")
    
    loss.backward()
    
    # Gradient clipping for numerical stability
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    
    optimizer.step()
    
    return loss.item()


@torch.no_grad()
def evaluate(
    model: GraphSAGE,
    data: Data,
    mask: torch.Tensor,
    device: torch.device
) -> Tuple[float, float]:
    
    model.eval()
    
    out = model(data.x.to(device), data.edge_index.to(device))
    # Numerical stability fix: sanitize logits before softmax
    out = torch.nan_to_num(out, nan=0.0, posinf=10.0, neginf=-10.0)
    pred = out.argmax(dim=1)
    probs = F.softmax(out, dim=1)[:, 1]
    # Probability safety: clamp to safe range
    probs = torch.clamp(probs, 1e-6, 1 - 1e-6)
    
    mask = mask.to(device)
    y_true = data.y.to(device)[mask]
    y_pred = pred[mask]
    y_probs = probs[mask]
    
    correct = (y_pred == y_true).sum().item()
    total = mask.sum().item()
    accuracy = correct / total if total > 0 else 0
    
    sorted_indices = torch.argsort(y_probs, descending=True)
    top_k = min(100, len(sorted_indices))
    top_k_labels = y_true[sorted_indices[:top_k]]
    precision_at_k = (top_k_labels == 1).sum().item() / top_k if top_k > 0 else 0
    
    return accuracy, precision_at_k


@torch.no_grad()
def compute_precision_at_k(
    model: GraphSAGE,
    data: Data,
    mask: torch.Tensor,
    device: torch.device,
    k_values: List[int] = [20, 50, 100]
) -> Dict[int, float]:
    
    model.eval()
    
    out = model(data.x.to(device), data.edge_index.to(device))
    # Numerical stability fix: sanitize logits before softmax
    out = torch.nan_to_num(out, nan=0.0, posinf=10.0, neginf=-10.0)
    probs = F.softmax(out, dim=1)[:, 1]
    # Probability safety: clamp to safe range
    probs = torch.clamp(probs, 1e-6, 1 - 1e-6)
    
    mask = mask.to(device)
    y_true = data.y.to(device)[mask]
    y_probs = probs[mask]
    
    sorted_indices = torch.argsort(y_probs, descending=True)
    
    precision_at_k = {}
    for k in k_values:
        top_k = min(k, len(sorted_indices))
        top_k_labels = y_true[sorted_indices[:top_k]]
        precision_at_k[k] = (top_k_labels == 1).sum().item() / top_k if top_k > 0 else 0
    
    return precision_at_k


@torch.no_grad()
def get_suspicious_scores(
    model: GraphSAGE,
    data: Data,
    tx_ids: List[int],
    device: torch.device,
    top_k: int = 20
) -> pd.DataFrame:
    
    model.eval()
    
    out = model(data.x.to(device), data.edge_index.to(device))
    # Numerical stability fix: sanitize logits before softmax
    out = torch.nan_to_num(out, nan=0.0, posinf=10.0, neginf=-10.0)
    probs = F.softmax(out, dim=1)[:, 1]
    # Probability safety: clamp to safe range
    probs = torch.clamp(probs, 1e-6, 1 - 1e-6).cpu().numpy()
    
    results = pd.DataFrame({
        'txId': tx_ids,
        'suspicious_score': probs,
        'label': data.y.numpy()
    })
    
    results['label_str'] = results['label'].map({0: 'licit', 1: 'illicit', -1: 'unknown'})
    # Reporting fix: exclude unknown labels (-1) from Top-K display
    results_known = results[results['label'] != -1]
    results_known = results_known.sort_values('suspicious_score', ascending=False)
    
    return results_known.head(top_k)


def visualize_laundering_subgraph(
    data: Data,
    tx_ids: List[int],
    suspicious_scores: np.ndarray,
    tx_id_to_idx: Dict[int, int],
    output_path: str = '/content/laundering_graph.png',
    top_k: int = 20,
    hop: int = 2,
    suspicious_threshold: float = 0.7
) -> nx.DiGraph:
    """
    Extract and visualize suspicious laundering subgraphs for interpretability.
    
    Args:
        data: PyTorch Geometric Data object with x, edge_index, y
        tx_ids: List of transaction IDs
        suspicious_scores: Array of suspicious scores for all nodes
        tx_id_to_idx: Mapping from txId to node index
        output_path: Path to save the visualization
        top_k: Number of top suspicious nodes to visualize
        hop: Number of hops for ego network extraction
        suspicious_threshold: Threshold for "highly suspicious" edge styling
    
    Returns:
        NetworkX DiGraph of the extracted subgraph
    """
    
    idx_to_tx_id = {idx: tx_id for tx_id, idx in tx_id_to_idx.items()}
    
    # Step 1: Select top K nodes with highest suspicious scores
    top_k_indices = np.argsort(suspicious_scores)[-top_k:][::-1]
    top_k_scores = suspicious_scores[top_k_indices]
    
    print(f"Top {top_k} suspicious nodes selected (scores: {top_k_scores.min():.4f} - {top_k_scores.max():.4f})")
    
    # Build full graph for ego network extraction
    edge_index = data.edge_index.numpy()
    full_graph = nx.DiGraph()
    full_graph.add_edges_from(zip(edge_index[0], edge_index[1]))
    
    # Step 2: Extract k-hop ego networks for each top suspicious node
    subgraph_nodes = set()
    for node_idx in top_k_indices:
        if node_idx in full_graph:
            # Get k-hop neighbors (both in and out directions)
            ego_nodes = {node_idx}
            frontier = {node_idx}
            
            for _ in range(hop):
                new_frontier = set()
                for n in frontier:
                    # Successors (outgoing edges)
                    if n in full_graph:
                        new_frontier.update(full_graph.successors(n))
                        new_frontier.update(full_graph.predecessors(n))
                new_frontier -= ego_nodes
                ego_nodes.update(new_frontier)
                frontier = new_frontier
            
            subgraph_nodes.update(ego_nodes)
    
    # Step 3: Create subgraph and remove isolated nodes
    subgraph_edges = [
        (src, dst) for src, dst in zip(edge_index[0], edge_index[1])
        if src in subgraph_nodes and dst in subgraph_nodes
    ]
    
    G = nx.DiGraph()
    G.add_edges_from(subgraph_edges)
    
    # Remove isolated nodes
    isolated = list(nx.isolates(G))
    G.remove_nodes_from(isolated)
    
    if G.number_of_nodes() == 0:
        print("Warning: Subgraph is empty after removing isolated nodes")
        return G
    
    print(f"Subgraph extracted: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Step 4: Prepare node styling
    node_colors = []
    node_sizes = []
    node_borders = []
    node_border_widths = []
    
    top_k_set = set(top_k_indices)
    score_min = suspicious_scores[list(G.nodes())].min()
    score_max = suspicious_scores[list(G.nodes())].max()
    
    for node in G.nodes():
        # Color by label
        label = data.y[node].item()
        if label == 1:  # illicit
            node_colors.append('#ff4444')
        elif label == 0:  # licit
            node_colors.append('#44cc44')
        else:  # unknown
            node_colors.append('#888888')
        
        # Scale size by suspicious score (normalized)
        score = suspicious_scores[node]
        if score_max > score_min:
            normalized_score = (score - score_min) / (score_max - score_min)
        else:
            normalized_score = 0.5
        node_sizes.append(100 + 400 * normalized_score)
        
        # Highlight top suspicious with border
        if node in top_k_set:
            node_borders.append('#000000')
            node_border_widths.append(2.5)
        else:
            node_borders.append('#444444')
            node_border_widths.append(0.5)
    
    # Step 5: Prepare edge styling
    edge_widths = []
    edge_colors = []
    
    for src, dst in G.edges():
        src_score = suspicious_scores[src]
        dst_score = suspicious_scores[dst]
        
        # Increase width if both endpoints are highly suspicious
        if src_score > suspicious_threshold and dst_score > suspicious_threshold:
            edge_widths.append(2.0)
            edge_colors.append('#ff6666')
        elif src_score > suspicious_threshold or dst_score > suspicious_threshold:
            edge_widths.append(1.2)
            edge_colors.append('#999999')
        else:
            edge_widths.append(0.5)
            edge_colors.append('#cccccc')
    
    # Step 6: Layout with fixed seed
    plt.figure(figsize=(18, 14))
    
    pos = nx.spring_layout(G, k=1.5, iterations=100, seed=42)
    
    # Draw edges first (so nodes are on top)
    nx.draw_networkx_edges(
        G, pos,
        edge_color=edge_colors,
        width=edge_widths,
        arrows=True,
        arrowsize=12,
        arrowstyle='-|>',
        connectionstyle='arc3,rad=0.1',
        alpha=0.6,
        min_source_margin=10,
        min_target_margin=10
    )
    
    # Draw nodes with borders
    nx.draw_networkx_nodes(
        G, pos,
        node_color=node_colors,
        node_size=node_sizes,
        edgecolors=node_borders,
        linewidths=node_border_widths,
        alpha=0.85
    )
    
    # Add labels only for top suspicious nodes
    labels = {}
    for node in top_k_indices:
        if node in G.nodes():
            tx_id = idx_to_tx_id.get(node, node)
            score = suspicious_scores[node]
            labels[node] = f"{str(tx_id)[:6]}\n{score:.2f}"
    
    nx.draw_networkx_labels(
        G, pos,
        labels=labels,
        font_size=7,
        font_color='black',
        font_weight='bold'
    )
    
    # Step 7: Create legend
    legend_elements = [
        plt.scatter([], [], c='#ff4444', s=150, edgecolors='black', linewidths=2, label='Illicit (known)'),
        plt.scatter([], [], c='#44cc44', s=150, edgecolors='black', linewidths=2, label='Licit (known)'),
        plt.scatter([], [], c='#888888', s=150, edgecolors='black', linewidths=2, label='Unknown'),
        plt.scatter([], [], c='white', s=80, edgecolors='black', linewidths=2.5, label='Top-K Suspicious (border)'),
        Line2D([0], [0], color='#ff6666', linewidth=2.5, label='High-risk edge'),
        Line2D([0], [0], color='#cccccc', linewidth=1, label='Normal edge'),
    ]
    
    # Size legend
    size_legend = [
        plt.scatter([], [], c='gray', s=100, alpha=0.5, label='Low score'),
        plt.scatter([], [], c='gray', s=300, alpha=0.5, label='Medium score'),
        plt.scatter([], [], c='gray', s=500, alpha=0.5, label='High score'),
    ]
    
    legend1 = plt.legend(
        handles=legend_elements,
        loc='upper left',
        title='Node & Edge Types',
        fontsize=9,
        title_fontsize=10
    )
    plt.gca().add_artist(legend1)
    
    plt.legend(
        handles=size_legend,
        loc='lower left',
        title='Suspicious Score (size)',
        fontsize=9,
        title_fontsize=10
    )
    
    plt.title(
        f'Detected Laundering Subgraph (Top {top_k} Suspicious Transactions)\n'
        f'{G.number_of_nodes()} nodes, {G.number_of_edges()} edges | {hop}-hop ego networks',
        fontsize=14,
        fontweight='bold'
    )
    
    plt.axis('off')
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"\nVisualization saved to: {output_path}")
    
    # Print summary statistics
    illicit_in_subgraph = sum(1 for n in G.nodes() if data.y[n].item() == 1)
    licit_in_subgraph = sum(1 for n in G.nodes() if data.y[n].item() == 0)
    unknown_in_subgraph = sum(1 for n in G.nodes() if data.y[n].item() == -1)
    
    print(f"\nSubgraph composition:")
    print(f"  Illicit nodes: {illicit_in_subgraph} ({illicit_in_subgraph/G.number_of_nodes()*100:.1f}%)")
    print(f"  Licit nodes: {licit_in_subgraph} ({licit_in_subgraph/G.number_of_nodes()*100:.1f}%)")
    print(f"  Unknown nodes: {unknown_in_subgraph} ({unknown_in_subgraph/G.number_of_nodes()*100:.1f}%)")
    
    return G


@torch.no_grad()
def get_all_suspicious_scores(
    model: GraphSAGE,
    data: Data,
    device: torch.device
) -> np.ndarray:
    """
    Get suspicious scores for ALL nodes in the graph.
    
    Returns:
        numpy array of suspicious scores (probability of illicit class)
    """
    model.eval()
    out = model(data.x.to(device), data.edge_index.to(device))
    # Numerical stability fix: sanitize logits before softmax
    out = torch.nan_to_num(out, nan=0.0, posinf=10.0, neginf=-10.0)
    probs = F.softmax(out, dim=1)[:, 1]
    # Probability safety: clamp to safe range
    probs = torch.clamp(probs, 1e-6, 1 - 1e-6).cpu().numpy()
    return probs


def detect_fan_patterns(
    data: Data,
    tx_id_to_idx: Dict[int, int],
    min_fan_out: int = 3,
    min_fan_in: int = 3
) -> Tuple[List[int], List[int]]:
    
    idx_to_tx_id = {idx: tx_id for tx_id, idx in tx_id_to_idx.items()}
    
    edge_index = data.edge_index.numpy()
    
    out_degree = {}
    in_degree = {}
    
    for src, dst in zip(edge_index[0], edge_index[1]):
        out_degree[src] = out_degree.get(src, 0) + 1
        in_degree[dst] = in_degree.get(dst, 0) + 1
    
    fan_out_nodes = [idx_to_tx_id[idx] for idx, deg in out_degree.items() if deg >= min_fan_out and idx in idx_to_tx_id]
    fan_in_nodes = [idx_to_tx_id[idx] for idx, deg in in_degree.items() if deg >= min_fan_in and idx in idx_to_tx_id]
    
    return fan_out_nodes, fan_in_nodes


def train_model(
    epochs: int = 100,
    hidden_dim: int = 64,
    lr: float = 0.001,
    dropout: float = 0.3,
    clip_value: float = 5.0,
    device: str = None
) -> Tuple[GraphSAGE, Data, List[int], Dict]:
    
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(device)
    
    print(f"Using device: {device}")
    print("Loading dataset...")
    
    features_df, edges_df, classes_df = load_elliptic_dataset()
    
    print("Building graph...")
    data, tx_id_to_idx, tx_ids = build_graph_data(features_df, edges_df, classes_df, clip_value=clip_value)
    
    print(f"Graph stats:")
    print(f"  Nodes: {data.x.size(0)}")
    print(f"  Edges: {data.edge_index.size(1)}")
    print(f"  Features: {data.x.size(1)}")
    print(f"  Labeled nodes: {(data.y >= 0).sum().item()}")
    print(f"  Illicit: {(data.y == 1).sum().item()}")
    print(f"  Licit: {(data.y == 0).sum().item()}")
    
    print("Creating train/val/test splits...")
    data = create_masks(data)
    
    # Label distribution logging for diagnostics
    train_labels = data.y[data.train_mask]
    val_labels = data.y[data.val_mask]
    test_labels = data.y[data.test_mask]
    print(f"Train split: {(train_labels == 0).sum().item()} licit, {(train_labels == 1).sum().item()} illicit")
    print(f"Val split: {(val_labels == 0).sum().item()} licit, {(val_labels == 1).sum().item()} illicit")
    print(f"Test split: {(test_labels == 0).sum().item()} licit, {(test_labels == 1).sum().item()} illicit")
    
    in_channels = data.x.size(1)
    model = GraphSAGE(
        in_channels=in_channels,
        hidden_channels=hidden_dim,
        out_channels=2,
        dropout=dropout
    ).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    
    class_weights = compute_class_weights(data)
    print(f"Class weights - Licit: {class_weights[0]:.4f}, Illicit: {class_weights[1]:.4f}")
    
    print(f"\nTraining for {epochs} epochs...")
    print("-" * 60)
    
    best_val_prec = 0
    best_model_state = None
    metrics_history = {'train_loss': [], 'val_acc': [], 'val_prec_at_k': []}
    
    try:
        for epoch in range(1, epochs + 1):
            loss = train_epoch(model, data, optimizer, device, class_weights)
            val_acc, val_prec = evaluate(model, data, data.val_mask, device)
            
            metrics_history['train_loss'].append(loss)
            metrics_history['val_acc'].append(val_acc)
            metrics_history['val_prec_at_k'].append(val_prec)
            
            if val_prec > best_val_prec:
                best_val_prec = val_prec
                best_model_state = model.state_dict().copy()
            
            if epoch % 10 == 0 or epoch == 1:
                print(f"Epoch {epoch:03d} | Loss: {loss:.4f} | Val Acc: {val_acc:.4f} | Val P@100: {val_prec:.4f}")
    except ValueError as e:
        # Catch NaN-related exceptions from train_epoch
        print(f"\n{e}")
        if best_model_state is not None:
            print("Restoring best model state before NaN occurred.")
            model.load_state_dict(best_model_state)
    
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    print("-" * 60)
    
    # Safety check: verify test set has both classes
    test_labels = data.y[data.test_mask]
    num_test_illicit = (test_labels == 1).sum().item()
    num_test_licit = (test_labels == 0).sum().item()
    skip_accuracy = num_test_illicit == 0 or num_test_licit == 0
    
    if skip_accuracy:
        print("WARNING: Test set contains no illicit samples; accuracy is not meaningful.")
    
    test_acc, test_prec = evaluate(model, data, data.test_mask, device)
    precision_at_k = compute_precision_at_k(model, data, data.test_mask, device, k_values=[20, 50, 100, 200])
    
    print(f"\n{'='*60}")
    print("TEST RESULTS REPORT")
    print(f"{'='*60}")
    
    # Only print accuracy if test set has both classes
    if skip_accuracy:
        print("\nAccuracy: SKIPPED (test set missing one or both classes)")
    else:
        print(f"\nAccuracy: {test_acc:.4f}")
    
    print(f"\nPrecision@K (% of top-K predictions that are truly illicit):")
    for k, prec in precision_at_k.items():
        print(f"  P@{k}: {prec:.4f} ({prec*100:.1f}%)")
    
    print(f"\nTop 20 Most Suspicious Transactions:")
    print("-" * 60)
    top_suspicious = get_suspicious_scores(model, data, tx_ids, device, top_k=20)
    print(top_suspicious.to_string(index=False))
    
    illicit_in_top20 = (top_suspicious['label'] == 1).sum()
    print(f"\n% Illicit in Top-20: {illicit_in_top20}/20 = {illicit_in_top20/20*100:.1f}%")
    
    print(f"\nDetecting fan-out/fan-in patterns...")
    tx_id_to_idx_map = {tx_id: idx for idx, tx_id in enumerate(tx_ids)}
    fan_out, fan_in = detect_fan_patterns(data, tx_id_to_idx_map, min_fan_out=5, min_fan_in=5)
    print(f"  Fan-out nodes (out-degree >= 5): {len(fan_out)}")
    print(f"  Fan-in nodes (in-degree >= 5): {len(fan_in)}")
    
    print(f"\nVisualizing laundering subgraph...")
    suspicious_scores = get_all_suspicious_scores(model, data, device)
    G = visualize_laundering_subgraph(
        data=data,
        tx_ids=tx_ids,
        suspicious_scores=suspicious_scores,
        tx_id_to_idx=tx_id_to_idx_map,
        output_path='/content/laundering_graph.png',
        top_k=20,
        hop=2,
        suspicious_threshold=0.7
    )
    
    return model, data, tx_ids, metrics_history


def save_model(model: GraphSAGE, path: str):
    torch.save(model.state_dict(), path)
    print(f"Model saved to {path}")


def load_model(path: str, in_channels: int, hidden_channels: int = 64) -> GraphSAGE:
    model = GraphSAGE(in_channels=in_channels, hidden_channels=hidden_channels)
    model.load_state_dict(torch.load(path))
    model.eval()
    return model


if __name__ == "__main__":
    model, data, tx_ids, history = train_model(
        epochs=100,
        hidden_dim=64,
        lr=0.001,
        dropout=0.3,
        clip_value=5.0
    )
    
    save_model(model, '/content/smurf_hunter_model.pt')
