# Research: Lightweight Local Graph Analytics

**Date**: 2025-01-27  
**Feature**: Lightweight Local Graph Analytics  
**Phase**: 0 - Research & Clarification

## Overview

This document consolidates research findings for implementing lightweight graph analytics on the Cardano blockchain visualization system. All analytics must operate locally on the loaded data subset using NetworkX.

## Research Areas

### 1. Node Degree Calculation

**Decision**: Use NetworkX built-in degree methods with custom filtering for node types

**Rationale**: 
- NetworkX provides `G.degree(node)` for total degree and `G.in_degree(node)`, `G.out_degree(node)` for directed graphs
- For block nodes: Count outgoing edges of type `block_tx` (transactions in block)
- For transaction nodes: Count incoming edges of type `tx_input` (inputs) and outgoing edges of type `tx_output` (outputs)
- For address nodes: Count edges where address is involved (both input and output transactions)

**Alternatives Considered**:
- Manual edge counting: More verbose, less maintainable
- Custom degree tracking: Unnecessary complexity, NetworkX already provides this

**Implementation Notes**:
- Filter edges by `type` attribute to get accurate counts per node type
- Cache degree calculations during graph updates to avoid recomputation
- Update degrees incrementally as new nodes/edges are added

---

### 2. Color Coding Strategy

**Decision**: Use HSL color space with hue/intensity gradients based on normalized activity scores

**Rationale**:
- HSL provides intuitive color progression (e.g., cool colors for low activity, warm colors for high activity)
- Normalize activity metrics to 0-100 scale for consistent color mapping
- Use color intensity (saturation/lightness) to represent activity levels
- Support multiple color schemes: heatmap (red-yellow-green), activity (blue-purple-red), or grayscale

**Alternatives Considered**:
- RGB interpolation: Less intuitive color progression
- Fixed color buckets: Less granular, harder to distinguish subtle differences
- External color libraries: Unnecessary dependency, simple HSL math sufficient

**Implementation Notes**:
- Normalize each metric type independently (block tx_count, transaction input/output count, address UTxO count)
- Map normalized value (0-100) to HSL: `hue = base_hue + (value * hue_range / 100)`, `saturation = base_sat + (value * sat_range / 100)`
- Convert HSL to RGB/hex for PyVis node color attribute
- Provide configurable color schemes via API parameter

**Color Mapping Formula**:
```
normalized_value = (actual_value - min_value) / (max_value - min_value) * 100
hue = base_hue + (normalized_value * hue_range / 100)
saturation = min(100, base_saturation + (normalized_value * saturation_boost))
lightness = base_lightness - (normalized_value * lightness_reduction / 100)
```

---

### 3. Anomaly Detection Methods

**Decision**: Use statistical methods (z-scores and percentile-based thresholds) appropriate for small datasets

**Rationale**:
- Z-score method: Identify values > 2 standard deviations from mean (catches ~95% of normal distribution)
- Percentile method: Flag top 5% or bottom 5% as anomalies (more robust for skewed distributions)
- Hybrid approach: Use z-score for normally distributed metrics, percentile for skewed metrics
- Threshold-based: Simple comparison against fixed multipliers (e.g., 3x average, 2x median)

**Alternatives Considered**:
- Machine learning (isolation forests, autoencoders): Overkill for small datasets, requires training data
- Complex statistical tests: Unnecessary complexity for simple anomaly detection
- External anomaly detection libraries: Adds dependency, simple stats sufficient

**Implementation Notes**:
- For transaction values: Use percentile method (top 5% as anomalies) since value distribution is typically skewed
- For block transaction counts: Use z-score method (values > mean + 2*std) since counts are more normally distributed
- Calculate statistics on loaded dataset only (not historical data)
- Cache statistics to avoid recalculation on every check
- Provide anomaly score (0-100) indicating how unusual the value is

**Anomaly Detection Algorithm**:
```python
def detect_anomalies(values, method='zscore', threshold=2.0):
    if method == 'zscore':
        mean = np.mean(values)
        std = np.std(values)
        anomalies = [v for v in values if abs(v - mean) > threshold * std]
    elif method == 'percentile':
        p95 = np.percentile(values, 95)
        p5 = np.percentile(values, 5)
        anomalies = [v for v in values if v > p95 or v < p5]
    return anomalies
```

---

### 4. Clustering Algorithms

**Decision**: Use NetworkX community detection algorithms (greedy modularity communities) for simple clustering

**Rationale**:
- NetworkX provides `nx.community.greedy_modularity_communities()` for community detection
- Works well on small-medium graphs (up to several thousand nodes)
- Identifies clusters based on edge density (addresses/transactions that frequently interact)
- Can filter by time window by creating subgraph of recent blocks only

**Alternatives Considered**:
- K-means clustering: Requires pre-defined number of clusters, not suitable for graph data
- Hierarchical clustering: More complex, slower for larger graphs
- Custom clustering: Unnecessary when NetworkX provides proven algorithms
- External clustering libraries (scikit-learn): Adds dependency, NetworkX sufficient

**Implementation Notes**:
- Create subgraph containing only nodes from last N blocks (configurable, default 20-50)
- For address clustering: Use undirected graph of address-address connections (addresses that share transactions)
- For transaction clustering: Use undirected graph of transaction-transaction connections (transactions sharing addresses)
- Assign cluster IDs to nodes as node attributes
- Visualize clusters by assigning distinct colors or grouping nodes spatially

**Clustering Algorithm**:
```python
def cluster_addresses(graph, time_window_blocks=20):
    # Get recent blocks
    recent_blocks = get_recent_blocks(graph, time_window_blocks)
    # Create subgraph of addresses connected to recent blocks
    subgraph = create_address_subgraph(graph, recent_blocks)
    # Convert to undirected for community detection
    undirected = subgraph.to_undirected()
    # Find communities
    communities = nx.community.greedy_modularity_communities(undirected)
    # Assign cluster IDs
    cluster_map = {}
    for cluster_id, community in enumerate(communities):
        for node in community:
            cluster_map[node] = cluster_id
    return cluster_map
```

---

### 5. Transaction Flow Visualization

**Decision**: Use NetworkX shortest path algorithms with value aggregation along paths

**Rationale**:
- NetworkX provides `nx.shortest_path()` and `nx.all_simple_paths()` for path finding
- For flow visualization: Find paths from input addresses → transactions → output addresses
- Aggregate value amounts along paths by summing edge weights (transaction output amounts)
- Highlight paths by adding visual attributes (color, width) to edges in path

**Alternatives Considered**:
- Custom path-finding: Unnecessary, NetworkX provides efficient algorithms
- External graph libraries: Adds dependency, NetworkX sufficient
- Complex flow algorithms (max flow, min cost flow): Overkill for visualization purposes

**Implementation Notes**:
- Filter to recent transactions (last 5-10 blocks) to limit path complexity
- Use edge weights (transaction output amounts) to prioritize high-value paths
- Find paths starting from input addresses, through transactions, to output addresses
- Store path information as node/edge attributes for frontend visualization
- Limit path depth to prevent exponential explosion (max 5-10 hops)

**Flow Path Algorithm**:
```python
def find_transaction_flows(graph, start_address, max_depth=5):
    flows = []
    # Find all transactions where address is input
    input_txs = [n for n in graph.successors(start_address) 
                 if graph.nodes[n]['type'] == 'transaction']
    for tx in input_txs:
        # Find paths from this transaction to output addresses
        paths = nx.all_simple_paths(graph, tx, target_nodes, cutoff=max_depth)
        for path in paths:
            # Calculate total value along path
            total_value = sum(graph.edges[path[i], path[i+1]].get('weight', 0) 
                            for i in range(len(path)-1))
            flows.append({'path': path, 'value': total_value})
    return sorted(flows, key=lambda x: x['value'], reverse=True)
```

---

### 6. Performance Optimization

**Decision**: Use incremental updates, caching, and lazy evaluation for analytics calculations

**Rationale**:
- Incremental updates: Recalculate only affected metrics when graph changes (not full recalculation)
- Caching: Store computed metrics (degrees, statistics, clusters) and invalidate on graph updates
- Lazy evaluation: Calculate analytics only when requested (not on every graph update)
- Batch operations: Process multiple nodes/edges together to reduce overhead

**Alternatives Considered**:
- Full recalculation on every update: Too slow for real-time updates
- External computation engines: Unnecessary complexity, Python/NetworkX sufficient for small graphs
- Precomputed analytics: Not feasible for dynamic graph updates

**Implementation Notes**:
- Cache degree calculations: Update only when edges added/removed for specific nodes
- Cache statistics: Recalculate mean/std/percentiles only when relevant nodes change
- Cache clusters: Recalculate only when nodes/edges in time window change
- Use dirty flags to track which metrics need recalculation
- Batch API requests: Calculate all requested analytics in single pass when possible

**Performance Targets**:
- Degree calculation: < 10ms for 1000 nodes
- Color coding: < 50ms for 1000 nodes (includes normalization and color conversion)
- Anomaly detection: < 100ms for 1000 nodes (includes statistics calculation)
- Clustering: < 500ms for 500 nodes (community detection)
- Flow paths: < 200ms for single address with max_depth=5

---

## Technology Choices Summary

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Graph Library | NetworkX 3.0+ | Already in use, provides all needed algorithms |
| Degree Calculation | NetworkX degree methods | Built-in, efficient, well-tested |
| Color Mapping | HSL color space | Intuitive gradients, simple math |
| Anomaly Detection | NumPy statistics (z-score, percentiles) | Simple, effective, no new dependencies |
| Clustering | NetworkX community detection | Built-in, works on small-medium graphs |
| Flow Visualization | NetworkX path algorithms | Built-in, efficient for small paths |
| Performance | Incremental updates + caching | Maintains real-time performance |

## Dependencies

**New Dependencies**: None required (all functionality available in existing dependencies)

**Optional Enhancements** (future):
- `numpy` for faster statistical calculations (if not already available)
- `scipy` for advanced statistical tests (if needed for more sophisticated anomaly detection)

## Open Questions Resolved

1. **Q**: How to handle very small datasets (1-2 blocks)?  
   **A**: Use simple threshold-based anomaly detection (e.g., flag if > 2x average) instead of statistical methods

2. **Q**: How to handle identical activity levels (all nodes same color)?  
   **A**: Use grayscale gradient or add small random variation to distinguish nodes

3. **Q**: How to handle clustering when no repeated interactions exist?  
   **A**: Return empty clusters or single-node clusters, indicate "no clusters found" in UI

4. **Q**: How to handle very large transaction values skewing statistics?  
   **A**: Use percentile-based methods (robust to outliers) or log-transform values before statistics

5. **Q**: How to update analytics when graph changes?  
   **A**: Use incremental updates with dirty flags, recalculate only affected metrics

## Next Steps

Proceed to Phase 1: Design & Contracts
- Define analytics data model extensions
- Design API endpoints for analytics queries
- Create quickstart guide for using analytics features

