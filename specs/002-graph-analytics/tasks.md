# Tasks: Lightweight Local Graph Analytics

**Feature**: Lightweight Local Graph Analytics  
**Branch**: `002-graph-analytics`  
**Generated**: 2025-01-27  
**Total Tasks**: 58

## Summary

This document provides an actionable, dependency-ordered task list for implementing lightweight graph analytics capabilities on the Cardano blockchain visualization system. Tasks are organized by phase, with each user story implemented as an independently testable increment.

**Task Breakdown**:
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 8 tasks
- **Phase 3 (User Story 1 - P1)**: 10 tasks
- **Phase 4 (User Story 2 - P1)**: 8 tasks
- **Phase 5 (User Story 3 - P2)**: 9 tasks
- **Phase 6 (User Story 4 - P2)**: 8 tasks
- **Phase 7 (User Story 5 - P3)**: 7 tasks
- **Phase 8 (Polish)**: 5 tasks

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1) + Phase 4 (User Story 2) - enables core analytics functionality with node degree metrics and color-coded activity visualization.

**Parallel Opportunities**: Many tasks within phases can be executed in parallel, especially analytics calculation methods, API endpoints, and frontend UI components.

---

## Phase 1: Setup

**Goal**: Prepare project structure and dependencies for analytics feature.

**Dependencies**: None (foundational setup)

### Tasks

- [ ] T001 Verify existing project structure (src/, static/, tests/unit/, tests/integration/) supports analytics extensions
- [ ] T002 Verify requirements.txt includes NetworkX 3.0+ and Flask 3.x (no new dependencies required per plan.md)
- [ ] T003 Create feature branch `002-graph-analytics` from main branch if not already created

---

## Phase 2: Foundational

**Goal**: Implement core analytics engine infrastructure that all user stories depend on.

**Dependencies**: Phase 1 must be complete

**Independent Test**: Can be tested by creating an AnalyticsEngine instance and verifying it can wrap/extend GraphBuilder and provide basic analytics methods.

### Tasks

- [ ] T004 Create src/analytics_engine.py with AnalyticsEngine class skeleton that wraps GraphBuilder instance
- [ ] T005 [P] Implement graph update listener in src/analytics_engine.py to register callbacks for node/edge additions and mark metrics as dirty
- [ ] T006 [P] Implement caching infrastructure in src/analytics_engine.py with dirty flags for degree, activity, anomaly, cluster, and flow metrics
- [ ] T007 [P] Implement incremental update tracking in src/analytics_engine.py to track which nodes/edges changed since last calculation
- [ ] T008 Implement statistics calculation helper methods in src/analytics_engine.py for mean, std, percentiles using Python standard library or NumPy if available
- [ ] T009 [P] Implement HSL to RGB color conversion utility in src/analytics_engine.py for color scheme mapping
- [ ] T010 [P] Implement color scheme mapping logic in src/analytics_engine.py supporting heatmap, activity, and grayscale schemes
- [ ] T011 Create tests/unit/test_analytics_engine.py with test fixtures for AnalyticsEngine initialization and GraphBuilder mocking

---

## Phase 3: User Story 1 - Identify High-Activity Blocks and Transactions (P1)

**Goal**: Users can quickly identify which blocks contain the most transactions and which transactions have the most inputs/outputs through node degree metrics.

**Independent Test**: Can be fully tested by loading blockchain data and verifying that block nodes display transaction counts and transaction nodes display input/output counts. The test passes when users can visually identify blocks with high transaction counts and transactions with many inputs/outputs.

**Acceptance Criteria**:
- Each block node displays the count of transactions it contains
- Each transaction node displays the count of inputs and outputs it has
- Users can identify which blocks have unusually high transaction counts compared to others
- Users can identify which transactions have unusually many inputs or outputs

**Dependencies**: Phase 2 must be complete

### Tasks

- [ ] T012 [US1] Implement calculate_node_degrees() method in src/analytics_engine.py to compute in_degree, out_degree, total_degree for all nodes using NetworkX G.degree(), G.in_degree(), G.out_degree()
- [ ] T013 [US1] Implement calculate_type_specific_degree() method in src/analytics_engine.py to compute type-specific degrees (block_tx edges for blocks, tx_input/tx_output edges for transactions, UTxO count for addresses)
- [ ] T014 [US1] Implement store_degree_metrics() method in src/analytics_engine.py to store degree metrics as node attributes (degree, in_degree, out_degree, type_degree) in NetworkX graph
- [ ] T015 [US1] Implement get_degree_metrics() API method in src/analytics_engine.py to return degree metrics filtered by node_type or node_id
- [ ] T016 [US1] Implement GET /api/analytics/degrees endpoint in src/web_server.py to return degree metrics JSON response per contracts/api.yaml schema
- [ ] T017 [US1] Add degree metrics display to static/index.html to show transaction counts on block nodes and input/output counts on transaction nodes in node labels or tooltips
- [ ] T018 [US1] Integrate AnalyticsEngine with GraphBuilder in src/web_server.py by creating AnalyticsEngine instance wrapping graph_builder
- [ ] T019 [US1] Add unit tests for calculate_node_degrees() in tests/unit/test_analytics_engine.py with sample graph data
- [ ] T020 [US1] Add unit tests for get_degree_metrics() filtering in tests/unit/test_analytics_engine.py
- [ ] T021 [US1] Add integration test for GET /api/analytics/degrees endpoint in tests/integration/test_end_to_end.py

---

## Phase 4: User Story 2 - Visualize Activity Through Color Coding (P1)

**Goal**: Users can quickly understand activity levels across the graph through visual color indicators without reading numerical values.

**Independent Test**: Can be fully tested by loading blockchain data and verifying that node colors reflect activity levels (transaction counts, UTxO counts). The test passes when users can distinguish high-activity nodes from low-activity nodes based on color intensity or hue.

**Acceptance Criteria**:
- Block nodes are colored using heatmap scheme (red for low, yellow for medium, green for high transaction counts)
- Transaction nodes are colored according to their input/output count
- Address nodes are colored according to their UTxO count
- Users can immediately identify the most active nodes without reading labels

**Dependencies**: Phase 3 must be complete

### Tasks

- [ ] T022 [US2] Implement calculate_activity_metrics() method in src/analytics_engine.py to compute raw activity values (tx_count for blocks, input+output count for transactions, UTxO count for addresses)
- [ ] T023 [US2] Implement normalize_activity_values() method in src/analytics_engine.py to normalize activity values to 0-100 scale per metric type independently
- [ ] T024 [US2] Implement apply_color_coding() method in src/analytics_engine.py to map normalized activity values to HSL colors using heatmap scheme (red → yellow → green) and convert to hex
- [ ] T025 [US2] Implement store_color_attributes() method in src/analytics_engine.py to store color_hex and color_scheme as node attributes in NetworkX graph
- [ ] T026 [US2] Implement get_activity_metrics() API method in src/analytics_engine.py to return activity metrics and color mappings filtered by node_type and color_scheme
- [ ] T027 [US2] Implement GET /api/analytics/activity endpoint in src/web_server.py to return activity metrics JSON response per contracts/api.yaml schema with color_scheme parameter support
- [ ] T028 [US2] Add color coding visualization to static/index.html to apply node colors from activity metrics API response using PyVis node color attribute
- [ ] T029 [US2] Add color scheme selector UI control to static/index.html allowing users to switch between heatmap, activity, and grayscale schemes

---

## Phase 5: User Story 3 - Detect Anomalies in Loaded Data (P2)

**Goal**: Users can identify unusual patterns in blockchain data such as transactions with unusually large values or blocks with abnormally high transaction counts.

**Independent Test**: Can be fully tested by loading blockchain data and verifying that unusually large transactions or blocks with unusually many transactions are visually highlighted or flagged. The test passes when users can identify anomalies through visual indicators or explicit flags.

**Acceptance Criteria**:
- Transactions with unusually large values compared to others are visually highlighted or flagged as anomalies
- Blocks with unusually high transaction counts compared to others are visually highlighted or flagged as anomalies
- Users can see which nodes are flagged as unusual
- Users can understand why a node was flagged (e.g., "transaction value 10x higher than average")

**Dependencies**: Phase 4 must be complete

### Tasks

- [ ] T030 [US3] Implement calculate_statistics() method in src/analytics_engine.py to compute mean, std, percentiles for transaction values and block transaction counts
- [ ] T031 [US3] Implement detect_anomalies_zscore() method in src/analytics_engine.py to flag nodes where |value - mean| > 2 * std for normally distributed metrics
- [ ] T032 [US3] Implement detect_anomalies_percentile() method in src/analytics_engine.py to flag nodes above 95th percentile or below 5th percentile for skewed distributions
- [ ] T033 [US3] Implement detect_anomalies_threshold() method in src/analytics_engine.py to flag nodes where value > threshold * average for small datasets
- [ ] T034 [US3] Implement detect_anomalies() unified method in src/analytics_engine.py to select appropriate detection method and calculate anomaly scores (0-100)
- [ ] T035 [US3] Implement store_anomaly_attributes() method in src/analytics_engine.py to store is_anomaly, anomaly_score, anomaly_type as node attributes in NetworkX graph
- [ ] T036 [US3] Implement get_anomalies() API method in src/analytics_engine.py to return anomaly detection results filtered by node_type and method parameter
- [ ] T037 [US3] Implement GET /api/analytics/anomalies endpoint in src/web_server.py to return anomaly detection JSON response per contracts/api.yaml schema with method and threshold parameters, returning 400 error if < 10 nodes
- [ ] T038 [US3] Add anomaly highlighting visualization to static/index.html to visually distinguish anomalous nodes using border, glow effect, or distinct styling

---

## Phase 6: User Story 4 - Cluster Related Addresses and Transactions (P2)

**Goal**: Users can identify clusters of addresses or transactions that frequently interact with each other within a recent time window (default: last 30 blocks, configurable: 20-50 blocks).

**Independent Test**: Can be fully tested by loading data from the last N blocks and verifying that addresses or transactions that frequently interact are grouped into clusters. The test passes when users can visually identify clusters of related nodes.

**Acceptance Criteria**:
- Addresses that frequently interact with each other are grouped into a cluster
- Transactions that share common addresses are grouped into a cluster
- Users can visually distinguish different clusters
- Users can see which addresses or transactions belong to a cluster

**Dependencies**: Phase 5 must be complete

### Tasks

- [ ] T039 [US4] Implement get_recent_blocks() method in src/analytics_engine.py to filter graph to nodes from last N blocks (configurable time_window_blocks parameter)
- [ ] T040 [US4] Implement create_address_subgraph() method in src/analytics_engine.py to create undirected subgraph of address-address connections for address clustering
- [ ] T041 [US4] Implement create_transaction_subgraph() method in src/analytics_engine.py to create undirected subgraph of transaction-transaction connections for transaction clustering
- [ ] T042 [US4] Implement cluster_addresses() method in src/analytics_engine.py using NetworkX nx.community.greedy_modularity_communities() algorithm on address subgraph
- [ ] T043 [US4] Implement cluster_transactions() method in src/analytics_engine.py using NetworkX nx.community.greedy_modularity_communities() algorithm on transaction subgraph
- [ ] T044 [US4] Implement store_cluster_attributes() method in src/analytics_engine.py to assign cluster_id, cluster_type, cluster_color as node attributes in NetworkX graph
- [ ] T045 [US4] Implement get_clusters() API method in src/analytics_engine.py to return cluster assignments filtered by cluster_type and time_window_blocks parameter
- [ ] T046 [US4] Implement GET /api/analytics/clusters endpoint in src/web_server.py to return cluster JSON response per contracts/api.yaml schema with cluster_type and time_window_blocks parameters

---

## Phase 7: User Story 5 - Visualize Transaction Flow Paths (P3)

**Goal**: Users can see how value (ADA or tokens) flows from input addresses through transactions to output addresses when clicking a transaction node.

**Independent Test**: Can be fully tested by loading recent transaction data and verifying that paths showing value flow from inputs to outputs are visually highlighted. The test passes when users can trace value movement through connected transactions.

**Acceptance Criteria**:
- When a user clicks a transaction node, they can see the flow path from input addresses through the transaction to output addresses
- Users can see highlighted paths showing value flow through multiple connected transactions
- Users can see the value amounts at each step
- Users can identify common flow patterns in recent blocks

**Dependencies**: Phase 6 must be complete

### Tasks

- [ ] T047 [US5] Implement find_flow_paths_from_address() method in src/analytics_engine.py using NetworkX nx.all_simple_paths() to find paths from input addresses through transactions to output addresses
- [ ] T048 [US5] Implement find_flow_paths_from_transaction() method in src/analytics_engine.py to find flow paths when user clicks a transaction node
- [ ] T049 [US5] Implement aggregate_path_values() method in src/analytics_engine.py to sum edge weights (transaction output amounts) along flow paths
- [ ] T050 [US5] Implement limit_path_depth() method in src/analytics_engine.py to limit paths to max_depth (5-10 hops) and filter to recent blocks (last 5-10 blocks)
- [ ] T051 [US5] Implement get_flow_paths() API method in src/analytics_engine.py to return flow paths filtered by start_address, transaction_id, max_depth, and max_blocks parameters
- [ ] T052 [US5] Implement GET /api/analytics/flow endpoint in src/web_server.py to return flow paths JSON response per contracts/api.yaml schema with query parameters
- [ ] T053 [US5] Add flow path visualization to static/index.html to highlight flow paths when user clicks a transaction node, showing path edges with distinct colors and widths

---

## Phase 8: Polish & Cross-Cutting Concerns

**Goal**: Finalize implementation with recalculation endpoint, comprehensive testing, error handling improvements, and code quality enhancements.

**Dependencies**: Phases 3, 4, 5, 6, and 7 should be complete

### Tasks

- [ ] T054 Implement POST /api/analytics/recalculate endpoint in src/web_server.py to trigger recalculation of all analytics metrics asynchronously, returning 202 Accepted response
- [ ] T055 Add comprehensive unit tests for all analytics calculation methods in tests/unit/test_analytics_engine.py covering edge cases (empty graphs, single node, identical values, etc.)
- [ ] T056 Add integration tests for all analytics API endpoints in tests/integration/test_end_to_end.py verifying end-to-end data flow
- [ ] T057 Add loading indicator UI component to static/index.html to show spinner/progress message during analytics calculations
- [ ] T058 Update README.md with analytics feature documentation including API usage examples and quickstart guide reference

---

## Dependencies

### User Story Completion Order

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ↓
Phase 3 (User Story 1 - P1) ──┐
    ↓                          │
Phase 4 (User Story 2 - P1)   │ (can be parallel after Phase 3)
    ↓                          │
Phase 5 (User Story 3 - P2) ───┤
    ↓                          │
Phase 6 (User Story 4 - P2) ───┤ (can be parallel after Phase 4)
    ↓                          │
Phase 7 (User Story 5 - P3) ───┘
    ↓
Phase 8 (Polish)
```

**Notes**:
- Phase 1 and Phase 2 are sequential prerequisites
- Phase 3 (US1) must complete before Phase 4 (US2)
- Phase 4 (US2) must complete before Phase 5 (US3) and Phase 6 (US4)
- Phase 5 (US3) and Phase 6 (US4) can be developed in parallel after Phase 4
- Phase 7 (US5) depends on Phase 6
- Phase 8 depends on all user story phases

### Task Dependencies Within Phases

**Phase 2**:
- T005-T007 (infrastructure) can be parallel
- T008-T010 (utilities) can be parallel
- T011 (tests) depends on T004

**Phase 3**:
- T012-T014 (degree calculation) are sequential
- T015-T016 (API) can be parallel after T014
- T017-T018 (integration) depend on T015-T016
- T019-T021 (tests) can be parallel after implementation

**Phase 4**:
- T022-T024 (activity calculation) are sequential
- T025-T026 (API) can be parallel after T024
- T027-T029 (frontend) can be parallel after T026

**Phase 5**:
- T030-T033 (detection methods) can be parallel
- T034-T035 (unified method) depend on T030-T033
- T036-T038 (API and frontend) can be parallel after T035

**Phase 6**:
- T039-T041 (subgraph creation) can be parallel
- T042-T043 (clustering) can be parallel after T040-T041
- T044-T046 (API) are sequential after T042-T043

**Phase 7**:
- T047-T050 (path finding) are sequential
- T051-T053 (API and frontend) can be parallel after T050

---

## Parallel Execution Examples

### Phase 2 - Foundational (Maximum Parallelism)

**Group 1** (Infrastructure - can run in parallel):
- T005, T006, T007

**Group 2** (Utilities - can run in parallel):
- T008, T009, T010

**Group 3** (Depends on T004):
- T011

### Phase 3 - User Story 1 (Parallel Opportunities)

**Group 1** (Degree Calculation - sequential):
- T012 → T013 → T014

**Group 2** (API Layer - can run in parallel after Group 1):
- T015, T016

**Group 3** (Integration - depends on Group 2):
- T017 → T018

**Group 4** (Tests - can run in parallel):
- T019, T020, T021

### Phase 4 - User Story 2 (Parallel Opportunities)

**Group 1** (Activity Calculation - sequential):
- T022 → T023 → T024

**Group 2** (API & Storage - can run in parallel after Group 1):
- T025, T026

**Group 3** (Frontend - can run in parallel after Group 2):
- T027, T028, T029

### Phase 5 - User Story 3 (Parallel Opportunities)

**Group 1** (Detection Methods - can run in parallel):
- T030, T031, T032, T033

**Group 2** (Unified Method - depends on Group 1):
- T034 → T035

**Group 3** (API & Frontend - can run in parallel after Group 2):
- T036, T037, T038

### Phase 6 - User Story 4 (Parallel Opportunities)

**Group 1** (Subgraph Creation - can run in parallel):
- T039, T040, T041

**Group 2** (Clustering - can run in parallel after Group 1):
- T042, T043

**Group 3** (API - sequential after Group 2):
- T044 → T045 → T046

### Phase 7 - User Story 5 (Parallel Opportunities)

**Group 1** (Path Finding - sequential):
- T047 → T048 → T049 → T050

**Group 2** (API & Frontend - can run in parallel after Group 1):
- T051, T052, T053

---

## Implementation Strategy

### MVP First Approach

**MVP Scope**: Phases 1, 2, 3 (User Story 1), and 4 (User Story 2)
- **Deliverable**: Working analytics system with node degree metrics and color-coded activity visualization
- **Test**: Load blockchain data, verify block nodes show transaction counts, transaction nodes show input/output counts, and nodes are color-coded by activity
- **Value**: Core analytics functionality - users can identify high-activity blocks/transactions and understand activity patterns through visual indicators

### Incremental Delivery

1. **Increment 1 (MVP)**: Phases 1-4
   - Node degree metrics
   - Color-coded activity visualization
   - Basic analytics API endpoints

2. **Increment 2**: Phase 5 (User Story 3)
   - Anomaly detection
   - Statistical analysis
   - Anomaly highlighting

3. **Increment 3**: Phase 6 (User Story 4)
   - Address clustering
   - Transaction clustering
   - Cluster visualization

4. **Increment 4**: Phase 7 (User Story 5)
   - Transaction flow paths
   - Path visualization
   - Value flow tracing

5. **Increment 5**: Phase 8 (Polish)
   - Recalculation endpoint
   - Comprehensive testing
   - Documentation

### Testing Strategy

- **Unit Tests**: Test individual analytics calculation methods (degree, activity, anomaly, clustering, flow) in isolation with mocked graph data
- **Integration Tests**: Test API endpoints with real graph data, verifying end-to-end data flow from graph → analytics → API → frontend
- **Performance Tests**: Verify analytics calculations complete within performance targets (< 2 seconds for 1000 nodes)
- **Edge Case Tests**: Test with empty graphs, single nodes, identical values, insufficient data for anomaly detection

### Risk Mitigation

- **Performance**: Implement caching and incremental updates to maintain performance targets
- **Insufficient Data**: Handle edge cases where anomaly detection requires minimum 10 nodes
- **Large Graphs**: Limit clustering time windows and flow path depths to prevent exponential explosion
- **Color Coding Edge Cases**: Handle identical activity levels using grayscale gradient or small random variation

---

## Notes

- All file paths are relative to repository root
- Analytics operate only on loaded data subset (not historical data)
- AnalyticsEngine wraps/extends existing GraphBuilder instance
- NetworkX graph stores analytics metrics as node/edge attributes
- Color schemes: heatmap (red-yellow-green), activity (blue-purple-red), grayscale
- Anomaly detection requires minimum 10 nodes for statistical validity
- Clustering default time window: 30 blocks (configurable: 20-50 blocks)
- Flow paths limited to max_depth=5-10 hops and max_blocks=5-10 blocks
- Analytics calculations use lazy evaluation (calculate on-demand, not on every graph update)
- Incremental updates mark metrics as dirty and recalculate only affected metrics

---

## Validation Checklist

- [x] All tasks follow format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
- [x] Each user story has independent test criteria
- [x] Tasks are organized by user story phase
- [x] Dependencies are clearly identified
- [x] Parallel execution opportunities are documented
- [x] MVP scope is defined
- [x] File paths are specified for each task
- [x] Task IDs are sequential (T001-T058)
- [x] User story labels ([US1], [US2], [US3], [US4], [US5]) are present for story phase tasks
- [x] Parallelizable tasks are marked with [P]

