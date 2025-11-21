# Quickstart Guide: Graph Analytics

**Date**: 2025-01-27  
**Feature**: Lightweight Local Graph Analytics

This guide explains how to use the graph analytics features to analyze Cardano blockchain data.

## Prerequisites

- Cardano graph visualization system running (see `001-cardano-graph-visualization/quickstart.md`)
- Some blockchain data loaded (at least a few blocks and transactions)
- Modern web browser with JavaScript enabled

## Overview

The analytics system provides five main capabilities:

1. **Node Degree Metrics**: Count connections per node (transaction count for blocks, input/output count for transactions)
2. **Activity Visualization**: Color-coded nodes based on activity levels (heatmap: red → yellow → green)
3. **Anomaly Detection**: Identify unusual blocks/transactions using statistical methods
4. **Clustering**: Group related addresses/transactions that frequently interact
5. **Flow Visualization**: Trace value movement through transaction paths

## Using Analytics via API

### 1. Get Node Degree Metrics

View connection counts for nodes:

```bash
# Get all node degrees
curl http://localhost:5000/api/analytics/degrees

# Get degrees for blocks only
curl http://localhost:5000/api/analytics/degrees?node_type=block

# Get degree for specific node
curl http://localhost:5000/api/analytics/degrees?node_id=block_abc123
```

**Response Example**:
```json
{
  "metrics": [
    {
      "node_id": "block_abc123",
      "node_type": "block",
      "in_degree": 1,
      "out_degree": 15,
      "total_degree": 16,
      "type_degree": 15
    }
  ]
}
```

### 2. Get Activity Metrics and Colors

View normalized activity scores and color mappings:

```bash
# Get activity metrics with default heatmap color scheme
curl http://localhost:5000/api/analytics/activity

# Get activity metrics for transactions only
curl http://localhost:5000/api/analytics/activity?node_type=transaction

# Use different color scheme
curl http://localhost:5000/api/analytics/activity?color_scheme=activity
```

**Response Example**:
```json
{
  "metrics": [
    {
      "node_id": "block_abc123",
      "node_type": "block",
      "raw_value": 25,
      "normalized_value": 75.5,
      "color_hex": "#FFA500"
    }
  ],
  "color_scheme": "heatmap"
}
```

### 3. Detect Anomalies

Identify unusual blocks or transactions:

```bash
# Detect anomalies using percentile method (default)
curl http://localhost:5000/api/analytics/anomalies

# Detect anomalies for blocks only
curl http://localhost:5000/api/analytics/anomalies?node_type=block

# Use z-score method
curl http://localhost:5000/api/analytics/anomalies?method=zscore

# Use threshold method (flag if > 2x average)
curl http://localhost:5000/api/analytics/anomalies?method=threshold&threshold=2.0
```

**Response Example**:
```json
{
  "anomalies": [
    {
      "node_id": "block_xyz789",
      "node_type": "block",
      "is_anomaly": true,
      "anomaly_score": 92.5,
      "anomaly_type": "high_transaction_count",
      "actual_value": 50
    }
  ],
  "method": "percentile",
  "statistics": {
    "mean": 15.2,
    "percentile_95": 30
  }
}
```

**Note**: Requires minimum 10 nodes for statistical validity. Returns 400 error if insufficient data.

### 4. Perform Clustering

Group related addresses or transactions:

```bash
# Cluster addresses (last 30 blocks, default)
curl http://localhost:5000/api/analytics/clusters?cluster_type=address

# Cluster transactions with custom time window
curl http://localhost:5000/api/analytics/clusters?cluster_type=transaction&time_window_blocks=20
```

**Response Example**:
```json
{
  "clusters": [
    {
      "cluster_id": 0,
      "node_ids": ["addr_abc", "addr_def", "addr_ghi"],
      "size": 3,
      "color_hex": "#FF5733"
    }
  ],
  "cluster_type": "address",
  "time_window_blocks": 30,
  "total_clusters": 5,
  "nodes_clustered": 15
}
```

### 5. Visualize Transaction Flows

Trace value movement through transactions:

```bash
# Get all flow paths (recent blocks)
curl http://localhost:5000/api/analytics/flow

# Get flows starting from specific address
curl http://localhost:5000/api/analytics/flow?start_address=addr_abc123

# Get flows for specific transaction (click interaction)
curl http://localhost:5000/api/analytics/flow?transaction_id=tx_xyz789

# Limit path depth
curl http://localhost:5000/api/analytics/flow?max_depth=3&max_blocks=5
```

**Response Example**:
```json
{
  "paths": [
    {
      "path_id": "flow_abc123",
      "start_address": "addr_abc",
      "end_address": "addr_xyz",
      "path_nodes": ["addr_abc", "tx_123", "addr_def", "tx_456", "addr_xyz"],
      "total_value": 1000000,
      "path_length": 4,
      "is_complete": true
    }
  ],
  "total_paths": 10,
  "max_depth": 5
}
```

### 6. Recalculate Analytics

Force recalculation after loading new data:

```bash
curl -X POST http://localhost:5000/api/analytics/recalculate
```

## Using Analytics in Frontend

The frontend visualization (`static/index.html`) should be extended to:

1. **Display Degree Metrics**: Show transaction counts on block nodes, input/output counts on transaction nodes
2. **Apply Color Coding**: Use `color_hex` from activity metrics to color nodes
3. **Highlight Anomalies**: Visually distinguish anomalous nodes (e.g., border, glow effect)
4. **Show Clusters**: Group clustered nodes visually (spatial grouping, cluster colors)
5. **Visualize Flows**: Highlight flow paths when user clicks a transaction node

### Example Frontend Integration

```javascript
// Fetch activity metrics and apply colors
async function applyColorCoding() {
  const response = await fetch('/api/analytics/activity?color_scheme=heatmap');
  const data = await response.json();
  
  data.metrics.forEach(metric => {
    const node = network.getNode(metric.node_id);
    if (node) {
      node.color = metric.color_hex;
      network.updateNode(node);
    }
  });
}

// Detect and highlight anomalies
async function highlightAnomalies() {
  const response = await fetch('/api/analytics/anomalies');
  const data = await response.json();
  
  data.anomalies.forEach(anomaly => {
    if (anomaly.is_anomaly) {
      const node = network.getNode(anomaly.node_id);
      if (node) {
        node.borderWidth = 3;
        node.borderColor = '#FF0000';
        network.updateNode(node);
      }
    }
  });
}

// Show flow paths on transaction click
async function showFlowPaths(transactionId) {
  const response = await fetch(`/api/analytics/flow?transaction_id=${transactionId}`);
  const data = await response.json();
  
  data.paths.forEach(path => {
    path.path_edges.forEach(edge => {
      const edgeObj = network.getEdge(edge.from, edge.to);
      if (edgeObj) {
        edgeObj.color = { color: '#00FF00', highlight: '#00FF00' };
        edgeObj.width = 3;
        network.updateEdge(edgeObj);
      }
    });
  });
}
```

## Performance Considerations

- **Degree Calculation**: Fast (< 10ms for 1000 nodes), cached automatically
- **Color Coding**: Moderate (< 50ms for 1000 nodes), recalculated on graph updates
- **Anomaly Detection**: Moderate (< 100ms for 1000 nodes), requires statistics calculation
- **Clustering**: Slower (< 500ms for 500 nodes), uses community detection algorithm
- **Flow Paths**: Moderate (< 200ms per query), limited by max_depth and max_blocks

**Tips**:
- Analytics are calculated incrementally when graph updates
- Use `POST /api/analytics/recalculate` only when needed
- Limit clustering time window (20-30 blocks) for better performance
- Limit flow path depth (3-5 hops) to prevent exponential explosion

## Configuration

Analytics behavior can be configured via API parameters:

- **Color Schemes**: `heatmap` (red-yellow-green), `activity` (blue-purple-red), `grayscale`
- **Anomaly Methods**: `percentile` (default), `zscore`, `threshold`
- **Clustering Window**: 20-50 blocks (default: 30)
- **Flow Path Depth**: 1-10 hops (default: 5)
- **Flow Block Range**: 1-10 blocks (default: 5)

## Troubleshooting

### "Insufficient data for anomaly detection"

**Issue**: Anomaly detection requires minimum 10 nodes  
**Solution**: Load more blockchain data or use threshold method with lower threshold

### Clustering returns empty results

**Issue**: No repeated interactions in time window  
**Solution**: Increase time window or wait for more data with repeated interactions

### Flow paths not found

**Issue**: No paths exist in recent blocks  
**Solution**: Increase `max_blocks` parameter or check if transactions are connected

### Analytics appear stale

**Issue**: Metrics not updated after loading new data  
**Solution**: Call `POST /api/analytics/recalculate` to force recalculation

### Performance issues

**Issue**: Analytics calculations are slow  
**Solution**: 
- Reduce clustering time window
- Limit flow path depth
- Filter by node_type to reduce dataset size
- Check dataset size (analytics optimized for < 1000 nodes)

## Next Steps

- **Explore the Code**: Review `src/analytics_engine.py` for implementation details
- **Customize Visualization**: Modify frontend to display analytics metrics
- **Add Features**: See feature spec for ideas on expanding analytics capabilities
- **Run Tests**: Execute `pytest tests/unit/test_analytics_engine.py` to verify functionality

## API Reference

See `contracts/api.yaml` for complete API documentation including:
- Request/response schemas
- Parameter descriptions
- Error codes and messages
- Example requests and responses

## Related Documentation

- **Feature Specification**: `spec.md`
- **Data Model**: `data-model.md`
- **Research**: `research.md`
- **Base API**: `../001-cardano-graph-visualization/contracts/api.yaml`

