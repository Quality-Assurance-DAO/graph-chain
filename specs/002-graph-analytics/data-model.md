# Data Model: Graph Analytics Extensions

**Date**: 2025-01-27  
**Feature**: Lightweight Local Graph Analytics  
**Extends**: [001-cardano-graph-visualization/data-model.md](../001-cardano-graph-visualization/data-model.md)

## Overview

This document extends the existing graph data model with analytics entities and metrics. Analytics operate on the existing graph structure without modifying core entities, adding computed attributes and derived metrics.

## Analytics Entities

### 1. Node Degree Metrics

Represents computed degree metrics for each node type in the graph.

**Attributes**:
- `node_id` (string, required): Graph node identifier
- `node_type` (string, required): Type of node (`block`, `transaction`, `address`)
- `in_degree` (integer): Number of incoming edges
- `out_degree` (integer): Number of outgoing edges
- `total_degree` (integer): Total number of edges (in + out)
- `type_specific_degree` (integer): Degree specific to node type:
  - Block: Count of `block_tx` edges (transaction count)
  - Transaction: Count of `tx_input` edges (input count) + `tx_output` edges (output count)
  - Address: Count of edges where address participates (UTxO count)

**Computation**:
- Calculated using NetworkX `G.degree()`, `G.in_degree()`, `G.out_degree()` methods
- Filtered by edge `type` attribute for type-specific degrees
- Updated incrementally when edges are added/removed

**Storage**:
- Stored as node attributes in NetworkX graph: `degree`, `in_degree`, `out_degree`, `type_degree`
- Cached in `GraphBuilder` for quick access

---

### 2. Activity Metric

Represents normalized activity level for color coding and visualization.

**Attributes**:
- `node_id` (string, required): Graph node identifier
- `metric_type` (string, required): Type of activity metric:
  - `block_tx_count`: Transaction count for blocks
  - `tx_input_output_count`: Input + output count for transactions
  - `address_utxo_count`: UTxO count for addresses
- `raw_value` (integer): Original unnormalized value
- `normalized_value` (float): Normalized value (0-100 scale)
- `min_value` (integer): Minimum value in dataset for normalization
- `max_value` (integer): Maximum value in dataset for normalization

**Computation**:
- Normalization formula: `normalized = ((raw_value - min_value) / (max_value - min_value)) * 100`
- Handles edge cases: If `max_value == min_value`, set `normalized = 50` (middle value)
- Calculated per metric type independently

**Storage**:
- Stored as node attributes: `activity_score`, `activity_metric_type`
- Cached with statistics (min/max) for normalization

---

### 3. Color Mapping

Represents visual color encoding for activity levels.

**Attributes**:
- `node_id` (string, required): Graph node identifier
- `color_scheme` (string, required): Color scheme name (`heatmap`, `activity`, `grayscale`)
- `hue` (float): HSL hue value (0-360)
- `saturation` (float): HSL saturation value (0-100)
- `lightness` (float): HSL lightness value (0-100)
- `color_hex` (string): Final RGB hex color code (e.g., `#FF5733`)
- `normalized_activity` (float): Normalized activity value used for color calculation (0-100)

**Computation**:
- Based on normalized activity value
- Color scheme mappings:
  - `heatmap`: Red (low) → Yellow (medium) → Green (high)
  - `activity`: Blue (low) → Purple (medium) → Red (high)
  - `grayscale`: Black (low) → Gray (medium) → White (high)
- HSL to RGB conversion for final hex color

**Storage**:
- Stored as node attributes: `color`, `color_scheme`
- Used directly by PyVis for node visualization

---

### 4. Anomaly Detection Result

Represents anomaly detection results for nodes.

**Attributes**:
- `node_id` (string, required): Graph node identifier
- `node_type` (string, required): Type of node (`block`, `transaction`)
- `anomaly_type` (string, required): Type of anomaly:
  - `high_transaction_count`: Block with unusually many transactions
  - `high_transaction_value`: Transaction with unusually large value
- `is_anomaly` (boolean): Whether node is flagged as anomaly
- `anomaly_score` (float): Anomaly score (0-100, higher = more anomalous)
- `detection_method` (string): Method used (`zscore`, `percentile`, `threshold`)
- `threshold_value` (float): Threshold used for detection
- `actual_value` (float): Actual metric value
- `statistical_context` (dict): Statistics used (mean, std, percentile, etc.)

**Computation**:
- For blocks: Compare transaction count against dataset statistics
- For transactions: Compare transaction value (sum of outputs) against dataset statistics
- Methods:
  - Z-score: Flag if `|value - mean| > 2 * std`
  - Percentile: Flag if value > 95th percentile or < 5th percentile
  - Threshold: Flag if value > threshold * average

**Storage**:
- Stored as node attributes: `is_anomaly`, `anomaly_score`, `anomaly_type`
- Statistics cached separately for performance

---

### 5. Cluster Assignment

Represents cluster membership for nodes.

**Attributes**:
- `node_id` (string, required): Graph node identifier
- `cluster_id` (integer): Unique cluster identifier (-1 if not clustered)
- `cluster_type` (string, required): Type of clustering (`address`, `transaction`)
- `cluster_size` (integer): Number of nodes in cluster
- `time_window_blocks` (integer): Number of blocks used for clustering (e.g., 20-50)
- `cluster_color` (string): Color assigned to cluster for visualization (hex code)

**Computation**:
- Using NetworkX `nx.community.greedy_modularity_communities()` algorithm
- Applied to subgraph containing nodes from last N blocks
- For address clustering: Undirected graph of address-address connections
- For transaction clustering: Undirected graph of transaction-transaction connections

**Storage**:
- Stored as node attributes: `cluster_id`, `cluster_type`, `cluster_color`
- Cluster metadata stored separately: `cluster_info` dict mapping cluster_id to metadata

---

### 6. Transaction Flow Path

Represents a path showing value flow through transactions.

**Attributes**:
- `path_id` (string, required): Unique path identifier
- `start_address` (string, required): Starting address node ID
- `end_address` (string, optional): Ending address node ID (if path completes)
- `path_nodes` (list[string], required): Ordered list of node IDs in path
- `path_edges` (list[tuple], required): List of (source, target) edge tuples
- `total_value` (integer): Total value (Lovelace) flowing through path
- `path_length` (integer): Number of hops in path
- `block_range` (tuple[int, int]): (min_block_height, max_block_height) in path
- `is_complete` (boolean): Whether path reaches an output address

**Computation**:
- Using NetworkX `nx.all_simple_paths()` or `nx.shortest_path()` algorithms
- Filtered to recent blocks (last 5-10 blocks)
- Value aggregated by summing edge weights along path
- Limited to max_depth (5-10 hops) to prevent exponential explosion

**Storage**:
- Stored separately in `AnalyticsEngine` as `flow_paths` list
- Referenced by node IDs for quick lookup
- Not stored as graph attributes (too many paths possible)

---

## Graph Schema Extensions

### Extended Node Attributes

All node types now support additional analytics attributes:

| Attribute | Type | Description | Applicable Node Types |
|-----------|------|-------------|----------------------|
| `degree` | integer | Total degree (in + out) | all |
| `in_degree` | integer | Incoming edge count | all |
| `out_degree` | integer | Outgoing edge count | all |
| `type_degree` | integer | Type-specific degree | all |
| `activity_score` | float | Normalized activity (0-100) | all |
| `color` | string | Hex color code | all |
| `color_scheme` | string | Color scheme name | all |
| `is_anomaly` | boolean | Anomaly flag | block, transaction |
| `anomaly_score` | float | Anomaly score (0-100) | block, transaction |
| `anomaly_type` | string | Type of anomaly | block, transaction |
| `cluster_id` | integer | Cluster membership ID | address, transaction |
| `cluster_type` | string | Type of clustering | address, transaction |
| `cluster_color` | string | Cluster visualization color | address, transaction |

### Extended Edge Attributes

Edges support flow visualization attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `in_flow_path` | boolean | Whether edge is part of a flow path |
| `flow_path_id` | string | ID of flow path containing this edge |
| `flow_value` | integer | Value flowing through this edge (for flow visualization) |

---

## Analytics Engine

New component: `AnalyticsEngine` class that extends `GraphBuilder` functionality.

**Responsibilities**:
- Calculate and cache node degree metrics
- Compute activity metrics and color mappings
- Detect anomalies using statistical methods
- Perform clustering on address/transaction subgraphs
- Find and store transaction flow paths
- Update analytics incrementally when graph changes

**Integration**:
- Wraps or extends `GraphBuilder` class
- Listens to graph update events via callbacks
- Provides analytics API methods for querying metrics
- Caches computed metrics for performance

**Data Flow**:
1. Graph update event (node/edge added/removed)
2. Analytics engine marks affected metrics as dirty
3. On next analytics query, recalculate dirty metrics
4. Store results as node/edge attributes
5. Return analytics data via API

---

## Validation Rules

- **Degree Metrics**: Must be non-negative integers
- **Activity Scores**: Must be in range 0-100 (normalized)
- **Color Codes**: Must be valid hex color format (`#RRGGBB`)
- **Anomaly Scores**: Must be in range 0-100
- **Cluster IDs**: Must be non-negative integers (-1 for unclustered)
- **Flow Paths**: Must contain valid node IDs that exist in graph
- **Statistics**: Mean, std, percentiles must be calculated on non-empty datasets

---

## Performance Considerations

- **Caching**: Cache computed metrics to avoid recalculation
- **Incremental Updates**: Only recalculate metrics for affected nodes
- **Lazy Evaluation**: Calculate analytics on-demand, not on every graph update
- **Batch Operations**: Process multiple nodes together when possible
- **Memory Management**: Limit cached flow paths to prevent memory growth

---

## Future Enhancements (Out of Scope)

- Historical analytics (trends over time)
- Advanced clustering algorithms (hierarchical, spectral)
- Machine learning-based anomaly detection
- Predictive analytics
- Export analytics results to external formats
- Real-time streaming analytics

