# Feature Specification: Lightweight Local Graph Analytics

**Feature Branch**: `002-graph-analytics`  
**Created**: 2025-01-27  
**Status**: Draft  
**Input**: User description: "add the ability to perform lightweight, local graph analytics on the subset of data you have loaded, such as: Block/transaction node degree, Count number of transactions per block (block node degree), Count number of inputs/outputs per transaction (transaction node degree), Useful to highlight "busy" blocks or high-activity transactions, Simple clustering on small graphs, Cluster addresses or transactions in the last N blocks (e.g., last 20–50 blocks), Useful to identify small clusters of repeated interactions, Transaction flow visualization, Show token/ADA movement from inputs → outputs for recent transactions, Can highlight paths in the last few blocks, Basic anomaly spotting, Highlight unusually large transactions in the fetched subset, Flag blocks with unusually many transactions, Color coding & heatmaps, Use node color to indicate transaction count or UTxO count per node, Visual feedback helps users understand which blocks/transactions are "hot""

## Clarifications

### Session 2025-01-27

- Q: What specific anomaly detection method and thresholds should be used? → A: Percentile-based detection: Flag transactions/blocks above 95th percentile or below 5th percentile (minimum 10 nodes required)
- Q: What default color scheme should be used for activity visualization? → A: Heatmap scheme: Red (low activity) → Yellow (medium) → Green (high activity)
- Q: What default clustering time window should be used? → A: Last 30 blocks (configurable range: 20-50 blocks)
- Q: How should users trigger transaction flow path visualization? → A: Click to select: User clicks a transaction node to show its flow paths
- Q: What user feedback should be shown during analytics calculations? → A: Loading indicator: Show spinner/progress message during calculations

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify High-Activity Blocks and Transactions (Priority: P1)

A user wants to quickly identify which blocks contain the most transactions and which transactions have the most inputs/outputs. This helps them understand blockchain activity patterns and spot "busy" periods or high-volume transactions.

**Why this priority**: Node degree metrics provide fundamental analytical insights that enable users to understand activity patterns. This is the foundation for other analytics features.

**Independent Test**: Can be fully tested by loading blockchain data and verifying that block nodes display transaction counts and transaction nodes display input/output counts. The test passes when users can visually identify blocks with high transaction counts and transactions with many inputs/outputs.

**Acceptance Scenarios**:

1. **Given** the system has loaded blockchain data, **When** a user views the graph, **Then** each block node displays the count of transactions it contains
2. **Given** the system has loaded blockchain data, **When** a user views the graph, **Then** each transaction node displays the count of inputs and outputs it has
3. **Given** multiple blocks are displayed, **When** a user examines the graph, **Then** they can identify which blocks have unusually high transaction counts compared to others
4. **Given** multiple transactions are displayed, **When** a user examines the graph, **Then** they can identify which transactions have unusually many inputs or outputs

---

### User Story 2 - Visualize Activity Through Color Coding (Priority: P1)

A user wants to quickly understand activity levels across the graph through visual indicators. Color coding helps them immediately see which blocks, transactions, or addresses are most active without reading numerical values.

**Why this priority**: Visual feedback dramatically improves user comprehension of activity patterns. Color coding enables at-a-glance understanding of "hot" vs "cold" nodes.

**Independent Test**: Can be fully tested by loading blockchain data and verifying that node colors reflect activity levels (transaction counts, UTxO counts). The test passes when users can distinguish high-activity nodes from low-activity nodes based on color intensity or hue.

**Acceptance Scenarios**:

1. **Given** the system displays blocks with varying transaction counts, **When** a user views the graph, **Then** block nodes are colored using heatmap scheme (red for low, yellow for medium, green for high transaction counts)
2. **Given** the system displays transactions with varying input/output counts, **When** a user views the graph, **Then** transaction nodes are colored according to their input/output count
3. **Given** the system displays addresses with varying UTxO counts, **When** a user views the graph, **Then** address nodes are colored according to their UTxO count
4. **Given** nodes are color-coded by activity, **When** a user views the graph, **Then** they can immediately identify the most active nodes without reading labels

---

### User Story 3 - Detect Anomalies in Loaded Data (Priority: P2)

A user wants to identify unusual patterns in the blockchain data they've loaded, such as transactions with unusually large values or blocks with abnormally high transaction counts. This helps them spot potential interesting events or outliers.

**Why this priority**: Anomaly detection provides analytical value by highlighting unusual patterns that might warrant investigation. This enables users to focus attention on potentially significant events.

**Independent Test**: Can be fully tested by loading blockchain data and verifying that unusually large transactions or blocks with unusually many transactions are visually highlighted or flagged. The test passes when users can identify anomalies through visual indicators or explicit flags.

**Acceptance Scenarios**:

1. **Given** the system has loaded multiple transactions, **When** a transaction has an unusually large value compared to others, **Then** it is visually highlighted or flagged as an anomaly
2. **Given** the system has loaded multiple blocks, **When** a block contains an unusually high number of transactions compared to others, **Then** it is visually highlighted or flagged as an anomaly
3. **Given** anomalies are detected, **When** a user views the graph, **Then** they can see which nodes are flagged as unusual
4. **Given** anomalies are displayed, **When** a user examines an anomaly, **Then** they can understand why it was flagged (e.g., "transaction value 10x higher than average")

---

### User Story 4 - Cluster Related Addresses and Transactions (Priority: P2)

A user wants to identify clusters of addresses or transactions that frequently interact with each other within a recent time window (default: last 30 blocks, configurable: 20-50 blocks). This helps them understand relationship patterns and identify groups of related activity.

**Why this priority**: Clustering reveals relationship patterns that aren't immediately obvious from individual connections. This enables users to understand groups and repeated interactions.

**Independent Test**: Can be fully tested by loading data from the last N blocks and verifying that addresses or transactions that frequently interact are grouped into clusters. The test passes when users can visually identify clusters of related nodes.

**Acceptance Scenarios**:

1. **Given** the system has loaded data from the last N blocks (default: 30 blocks, configurable: 20-50 blocks), **When** addresses frequently interact with each other, **Then** they are grouped into a cluster
2. **Given** the system has loaded data from the last N blocks (default: 30 blocks), **When** transactions share common addresses, **Then** they are grouped into a cluster
3. **Given** clusters are identified, **When** a user views the graph, **Then** they can visually distinguish different clusters
4. **Given** clusters are displayed, **When** a user examines a cluster, **Then** they can see which addresses or transactions belong to that cluster

---

### User Story 5 - Visualize Transaction Flow Paths (Priority: P3)

A user wants to see how value (ADA or tokens) flows from input addresses through transactions to output addresses. This helps them trace value movement and understand transaction paths in recent blocks.

**Why this priority**: Flow visualization provides deeper understanding of value movement patterns. While valuable, this is more advanced than basic metrics and can be built after core analytics are in place.

**Independent Test**: Can be fully tested by loading recent transaction data and verifying that paths showing value flow from inputs to outputs are visually highlighted. The test passes when users can trace value movement through connected transactions.

**Acceptance Scenarios**:

1. **Given** the system has loaded recent transactions, **When** a user clicks a transaction node, **Then** they can see the flow path from input addresses through the transaction to output addresses
2. **Given** multiple connected transactions exist, **When** a user clicks a transaction node, **Then** they can see highlighted paths showing value flow through multiple connected transactions
3. **Given** transaction flows are displayed, **When** a user examines a flow path, **Then** they can see the value amounts at each step
4. **Given** transaction flows are visualized, **When** a user views recent blocks, **Then** they can identify common flow patterns

---

### Edge Cases

- What happens when no data is loaded yet?
- How does the system handle blocks with zero transactions?
- What occurs when all transactions have the same input/output count (no variation)?
- How does clustering behave when there are no repeated interactions in the time window?
- What happens when anomaly thresholds result in flagging all or none of the transactions?
- How does the system handle very small datasets (e.g., only 1-2 blocks loaded)? (Anomaly detection requires minimum 10 nodes; smaller datasets skip anomaly detection)
- What occurs when transaction values are missing or zero?
- How does color coding work when all nodes have identical activity levels?
- What happens when clustering identifies a single large cluster containing most nodes?
- How does the system handle user interactions during analytics calculation periods? (Loading indicator shown, interactions may be queued or disabled)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate and display the transaction count for each block node (block node degree)
- **FR-002**: System MUST calculate and display the input count for each transaction node
- **FR-003**: System MUST calculate and display the output count for each transaction node
- **FR-004**: System MUST apply color coding to block nodes based on their transaction count
- **FR-005**: System MUST apply color coding to transaction nodes based on their input/output count
- **FR-006**: System MUST apply color coding to address nodes based on their UTxO count
- **FR-007**: System MUST identify transactions with unusually large values compared to other transactions in the loaded dataset
- **FR-008**: System MUST identify blocks with unusually high transaction counts compared to other blocks in the loaded dataset
- **FR-009**: System MUST visually highlight or flag nodes identified as anomalies
- **FR-010**: System MUST support clustering addresses that frequently interact within a configurable time window (default: last 30 blocks, configurable range: 20-50 blocks)
- **FR-011**: System MUST support clustering transactions that share common addresses within a configurable time window (default: last 30 blocks, configurable range: 20-50 blocks)
- **FR-012**: System MUST visually distinguish different clusters in the graph display
- **FR-013**: System MUST visualize transaction flow paths showing value movement from inputs through transactions to outputs when a user clicks a transaction node
- **FR-014**: System MUST highlight flow paths for recent transactions (e.g., last few blocks) in response to user click interaction
- **FR-015**: System MUST display value amounts along transaction flow paths
- **FR-016**: System MUST perform all analytics calculations locally on the loaded data subset
- **FR-017**: System MUST update analytics metrics when new data is loaded
- **FR-018**: System MUST provide visual feedback indicating activity levels through color intensity or hue gradients
- **FR-019**: System MUST display a loading indicator (spinner/progress message) during analytics calculations to inform users of processing status

### Key Entities *(include if feature involves data)*

- **Block Node Degree**: The count of transactions contained within a block. Used to identify "busy" blocks with high activity.

- **Transaction Node Degree**: The count of inputs and outputs for a transaction. Used to identify high-activity transactions with many connections.

- **Address Node Degree**: The count of UTxOs associated with an address. Used to identify addresses with high activity or value.

- **Activity Metric**: A calculated value representing the activity level of a node (transaction count, input/output count, UTxO count). Used for color coding and anomaly detection.

- **Anomaly**: A node (block or transaction) that exhibits unusual characteristics compared to other nodes in the loaded dataset. Detected using percentile-based method: flagged if value exceeds 95th percentile or falls below 5th percentile (requires minimum 10 nodes for detection).

- **Cluster**: A group of addresses or transactions that frequently interact with each other within a specified time window (default: last 30 blocks, configurable: 20-50 blocks). Identified through relationship analysis of the loaded data.

- **Transaction Flow Path**: A sequence of connections showing how value moves from input addresses through transactions to output addresses. Represents the movement of ADA or tokens through the graph. Visualized when user clicks a transaction node.

- **Color Mapping**: A visual encoding scheme that maps activity metrics to colors using heatmap scheme (red → yellow → green), enabling users to quickly identify activity levels through visual inspection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify blocks with the highest transaction counts within 5 seconds of viewing the graph
- **SC-002**: Users can identify transactions with the most inputs/outputs within 5 seconds of viewing the graph
- **SC-003**: Color coding enables users to distinguish high-activity nodes from low-activity nodes with 90% accuracy without reading numerical labels
- **SC-004**: Anomaly detection identifies at least 80% of transactions that are 3x larger than the average transaction value in the loaded dataset
- **SC-005**: Anomaly detection identifies at least 80% of blocks that contain 2x more transactions than the average block in the loaded dataset
- **SC-006**: Clustering successfully groups at least 70% of addresses that interact 3+ times within the specified time window
- **SC-007**: Users can trace transaction flow paths through at least 5 connected transactions without the interface becoming unresponsive
- **SC-008**: Analytics calculations complete within 2 seconds for datasets containing up to 1000 nodes
- **SC-009**: Analytics metrics update automatically when new data is loaded, completing within 3 seconds
- **SC-010**: Users can understand activity patterns through visual indicators alone (without reading detailed metrics) for 90% of use cases

## Assumptions

- Users have already loaded blockchain data into the system (analytics operate on loaded data subset)
- The loaded data subset contains at least a few blocks and transactions to enable meaningful analytics
- Users understand basic graph analytics concepts (node degree, clustering, flow paths)
- Color coding uses heatmap scheme: Red (low activity) → Yellow (medium) → Green (high activity) for all node types
- Anomaly detection uses percentile-based method: flags nodes above 95th percentile or below 5th percentile, requiring minimum 10 nodes in dataset for statistical validity
- Clustering algorithms can operate efficiently on small to medium-sized graphs (up to several thousand nodes)
- Transaction flow visualization focuses on recent blocks (e.g., last 5-10 blocks) to maintain performance
- Clustering uses default time window of last 30 blocks (configurable range: 20-50 blocks) for optimal balance of coverage and performance
- Analytics calculations are performed synchronously and update the visualization when complete, with loading indicators shown during calculation periods (typically 2-3 seconds)
- The system can handle datasets with varying activity levels (some blocks/transactions much more active than others)

## Dependencies

- Existing graph visualization system with loaded blockchain data
- Node and edge data structures that support degree calculations
- Transaction value data available for anomaly detection
- Address and transaction relationship data for clustering
- Input/output connection data for flow visualization

## Out of Scope

- Advanced graph algorithms (e.g., PageRank, community detection beyond simple clustering)
- Historical analytics across long time periods (focusing on recently loaded data)
- Predictive analytics or forecasting
- Real-time streaming analytics (operating on loaded data subset)
- Export of analytics results to external formats
- Comparative analytics across different time periods
- User-configurable anomaly detection thresholds (using reasonable defaults)
- Machine learning-based pattern detection
- Analytics on data not yet loaded into the system
- Performance optimization for very large graphs (thousands of nodes)

