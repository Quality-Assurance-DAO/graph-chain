# Tasks: Cardano Blockchain Graph Visualization

**Feature**: Cardano Blockchain Graph Visualization  
**Branch**: `001-cardano-graph-visualization`  
**Generated**: 2025-01-27  
**Total Tasks**: 45

## Summary

This document provides an actionable, dependency-ordered task list for implementing the Cardano blockchain graph visualization proof-of-concept. Tasks are organized by phase, with each user story implemented as an independently testable increment.

**Task Breakdown**:
- **Phase 1 (Setup)**: 6 tasks
- **Phase 2 (Foundational)**: 8 tasks
- **Phase 3 (User Story 1 - P1)**: 12 tasks
- **Phase 4 (User Story 2 - P2)**: 6 tasks
- **Phase 5 (User Story 3 - P3)**: 8 tasks
- **Phase 6 (Polish)**: 5 tasks

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1) - enables core real-time visualization functionality.

**Parallel Opportunities**: Many tasks within phases can be executed in parallel, especially model/service implementations and frontend/backend work.

---

## Phase 1: Setup

**Goal**: Initialize project structure, dependencies, and basic configuration.

**Dependencies**: None (foundational setup)

### Tasks

- [X] T001 Create project directory structure (src/, static/, tests/unit/, tests/integration/, config/)
- [X] T002 Create requirements.txt with Flask 3.x, NetworkX, PyVis, blockfrost-python, requests, tenacity, python-dotenv, pytest, pytest-asyncio
- [X] T003 Create config/.env.example with BLOCKFROST_API_KEY, POLLING_INTERVAL, MAX_RETRIES, RATE_LIMIT_BACKOFF placeholders
- [X] T004 Create README.md with project overview, setup instructions, and quickstart guide reference
- [X] T005 Create .gitignore with Python patterns, venv/, .env, __pycache__/, *.pyc
- [X] T006 Create pytest.ini or pyproject.toml with pytest configuration for tests/ directory

---

## Phase 2: Foundational

**Goal**: Implement core data models, graph structure, and API client foundation that all user stories depend on.

**Dependencies**: Phase 1 must be complete

**Independent Test**: Can be tested by creating Block, Transaction, and Address instances and verifying they can be added to a NetworkX graph structure.

### Tasks

- [X] T007 [P] Create src/models/__init__.py for models package
- [X] T008 [P] Implement Block model class in src/models/block.py with block_hash, block_height, timestamp, slot, tx_count attributes
- [X] T009 [P] Implement Transaction model class in src/models/transaction.py with tx_hash, block_hash, inputs, outputs, fee attributes and nested TransactionInput/TransactionOutput classes
- [X] T010 [P] Implement Address model class in src/models/address.py with address, first_seen, total_received, total_sent, transaction_count attributes
- [X] T011 Create src/graph_builder.py with GraphBuilder class using NetworkX DiGraph, implementing add_block(), add_transaction(), add_address() methods
- [X] T012 [P] Create src/api/__init__.py for API package
- [X] T013 [P] Create src/api/blockfrost_client.py with BlockfrostClient class using blockfrost-python SDK, implementing get_latest_block(), get_block_transactions() methods with basic error handling
- [X] T014 Create src/config.py module to load environment variables using python-dotenv, providing BLOCKFROST_API_KEY, POLLING_INTERVAL, MAX_RETRIES, RATE_LIMIT_BACKOFF configuration values

---

## Phase 3: User Story 1 - View Real-Time Blockchain Activity (P1)

**Goal**: Users can visualize Cardano blockchain activity as it happens, seeing new blocks and transactions appear in real-time as a connected graph.

**Independent Test**: Launch the visualization system and observe new blockchain data appear automatically in the graph interface. Test passes when users see blocks, transactions, and addresses appear and connect as new activity occurs on the blockchain.

**Acceptance Criteria**:
- New blocks appear as nodes within 3 seconds of creation
- New transactions appear as nodes connected to input/output addresses
- Users can see relationships between addresses through transaction flows
- Graph updates incrementally showing progression of blockchain activity

**Dependencies**: Phase 2 must be complete

### Tasks

- [X] T015 [US1] Implement data polling loop in src/data_fetcher.py with DataFetcher class, polling Blockfrost API at configured interval for latest blocks
- [X] T016 [US1] Implement block parsing in src/data_fetcher.py to convert Blockfrost API responses to Block model instances
- [X] T017 [US1] Implement transaction parsing in src/data_fetcher.py to convert Blockfrost API transaction data to Transaction model instances with inputs and outputs
- [X] T018 [US1] Integrate DataFetcher with GraphBuilder in src/data_fetcher.py to automatically add fetched blocks and transactions to graph structure
- [X] T019 [US1] Create Flask app structure in src/web_server.py with Flask application initialization and basic route setup
- [X] T020 [US1] Implement GET / route in src/web_server.py to serve static/index.html visualization page
- [X] T021 [US1] Implement GET /api/graph route in src/web_server.py to return current graph state as JSON with nodes, edges, and metadata
- [X] T022 [US1] Create static/index.html with PyVis network visualization, embedded JavaScript for graph rendering, and basic styling
- [X] T023 [US1] Implement graph state serialization in src/graph_builder.py to convert NetworkX graph to JSON format compatible with PyVis (nodes array, edges array)
- [X] T024 [US1] Implement GET /api/graph/updates route in src/web_server.py with Server-Sent Events (SSE) streaming for real-time graph updates
- [X] T025 [US1] Implement graph update event generation in src/graph_builder.py to emit node_added and edge_added events when graph is updated
- [X] T026 [US1] Integrate DataFetcher polling loop with Flask app in src/web_server.py using background thread or async task to continuously fetch and update graph

---

## Phase 4: User Story 2 - Understand Transaction Flows (P2)

**Goal**: Users can trace how value moves between addresses by following connections in the graph, seeing input addresses connect to transactions and transactions connect to output addresses.

**Independent Test**: Examine a transaction in the graph and verify that input addresses connect to the transaction node, and the transaction node connects to output addresses, accurately representing the blockchain data structure.

**Acceptance Criteria**:
- Users can see all input addresses connected to a transaction
- Users can see all output addresses connected from a transaction
- Users can see all transactions connected to an address node
- Users can trace value movement from one address through transactions to another address

**Dependencies**: Phase 3 must be complete

### Tasks

- [X] T027 [US2] Enhance graph edge creation in src/graph_builder.py to ensure all transaction input addresses connect to transaction node with tx_input edge type
- [X] T028 [US2] Enhance graph edge creation in src/graph_builder.py to ensure all transaction output addresses connect from transaction node with tx_output edge type
- [X] T029 [US2] Implement address node aggregation in src/graph_builder.py to update address statistics (transaction_count, total_received, total_sent) when address appears in multiple transactions
- [X] T030 [US2] Enhance PyVis visualization in static/index.html to display edge labels showing transaction amounts and edge types (input/output) for better flow understanding
- [X] T031 [US2] Implement node interaction handlers in static/index.html JavaScript to highlight connected nodes when hovering or clicking on transactions/addresses
- [X] T032 [US2] Add visual distinction in static/index.html for different node types (blocks, transactions, addresses) using different colors, shapes, or sizes in PyVis network

---

## Phase 5: User Story 3 - Handle API Limitations Gracefully (P3)

**Goal**: System encounters rate limits or temporary API unavailability. Users experience minimal disruption, with automatic recovery and status feedback.

**Independent Test**: Simulate API rate limit errors or network failures and verify that the system handles these gracefully without crashing, displays appropriate status information, and automatically resumes data collection when possible.

**Acceptance Criteria**:
- System pauses requests appropriately when rate limited and resumes after rate limit period
- System continues operating and attempts to reconnect automatically when API becomes unavailable
- Users see clear status indication without losing previously displayed graph data
- System provides clear feedback about issues without crashing when it cannot recover automatically

**Dependencies**: Phase 3 must be complete (can be developed in parallel with Phase 4)

### Tasks

- [X] T033 [US3] Implement exponential backoff retry logic in src/api/blockfrost_client.py using tenacity library to handle 429 rate limit responses
- [X] T034 [US3] Implement API error handling in src/data_fetcher.py to catch and log API errors, continue polling loop without crashing on temporary failures
- [X] T035 [US3] Add rate limit detection and backoff logic in src/data_fetcher.py to pause polling when rate limited, resume after backoff period
- [X] T036 [US3] Implement system status tracking in src/web_server.py to track API connection status, polling status, rate limit status, and error state
- [X] T037 [US3] Implement GET /api/status route in src/web_server.py to return system status JSON with api_status, polling_status, rate_limit_status, graph_stats, last_block_fetched
- [X] T038 [US3] Add status display UI component in static/index.html to show system status (active/paused/error), API connection status, and rate limit warnings
- [X] T039 [US3] Implement graceful degradation in src/data_fetcher.py to continue displaying existing graph data when API is unavailable, with clear status indication
- [X] T040 [US3] Add error logging and user feedback in src/web_server.py to log errors to console and include error messages in status endpoint responses

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Finalize implementation with testing, documentation, error handling improvements, and code quality enhancements.

**Dependencies**: Phases 3, 4, and 5 should be complete

### Tasks

- [X] T041 Create tests/unit/test_data_fetcher.py with unit tests for DataFetcher using mocked Blockfrost API responses
- [X] T042 Create tests/unit/test_graph_builder.py with unit tests for GraphBuilder using sample Block, Transaction, Address instances
- [X] T043 Create tests/unit/test_web_server.py with Flask test client tests for GET /, GET /api/graph, GET /api/status routes
- [X] T044 Create tests/integration/test_end_to_end.py with integration test simulating full data flow from API fetch to graph visualization
- [X] T045 Update README.md with complete setup instructions, configuration details, troubleshooting guide, and usage examples

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
Phase 4 (User Story 2 - P2)    │ (can be parallel)
    ↓                          │
Phase 5 (User Story 3 - P3) ───┘
    ↓
Phase 6 (Polish)
```

**Notes**:
- Phase 1 and Phase 2 are sequential prerequisites
- Phase 3 (US1) must complete before Phase 4 (US2) and Phase 5 (US3)
- Phase 4 and Phase 5 can be developed in parallel after Phase 3
- Phase 6 depends on all user story phases

### Task Dependencies Within Phases

**Phase 2**:
- T007-T010 (models) can be parallel
- T011 depends on T008-T010 (needs model classes)
- T012-T013 (API client) can be parallel with models
- T014 is independent

**Phase 3**:
- T015-T018 (data fetcher) are sequential
- T019-T021 (Flask routes) can be parallel with data fetcher
- T022-T023 (frontend) can be parallel with backend
- T024-T026 (SSE integration) depend on T019-T021 and T015-T018

**Phase 4**:
- T027-T029 (graph enhancements) are sequential
- T030-T032 (UI enhancements) can be parallel

**Phase 5**:
- T033-T035 (error handling) are sequential
- T036-T040 (status/UI) can be parallel after T033-T035

---

## Parallel Execution Examples

### Phase 2 - Foundational (Maximum Parallelism)

**Group 1** (Models - can run in parallel):
- T007, T008, T009, T010

**Group 2** (API & Config - can run in parallel):
- T012, T013, T014

**Group 3** (Depends on Group 1):
- T011

### Phase 3 - User Story 1 (Parallel Opportunities)

**Group 1** (Data Layer - sequential):
- T015 → T016 → T017 → T018

**Group 2** (Backend Routes - can run in parallel):
- T019, T020, T021

**Group 3** (Frontend - can run in parallel with Group 2):
- T022, T023

**Group 4** (Integration - depends on Groups 1, 2, 3):
- T024 → T025 → T026

### Phase 4 - User Story 2 (Parallel Opportunities)

**Group 1** (Backend Graph Logic - sequential):
- T027 → T028 → T029

**Group 2** (Frontend Enhancements - can run in parallel):
- T030, T031, T032

### Phase 5 - User Story 3 (Parallel Opportunities)

**Group 1** (Error Handling - sequential):
- T033 → T034 → T035

**Group 2** (Status & UI - can run in parallel after Group 1):
- T036, T037, T038, T039, T040

---

## Implementation Strategy

### MVP First Approach

**MVP Scope**: Phases 1, 2, and 3 (User Story 1)
- **Deliverable**: Working real-time blockchain visualization showing blocks, transactions, and addresses appearing automatically
- **Test**: Launch system, verify new blockchain data appears in graph within 3 seconds
- **Value**: Core functionality - users can see blockchain activity in real-time

### Incremental Delivery

1. **Increment 1 (MVP)**: Phases 1-3
   - Basic real-time visualization
   - Core graph structure
   - Simple UI

2. **Increment 2**: Phase 4 (User Story 2)
   - Enhanced transaction flow visualization
   - Better node/edge labeling
   - Interactive exploration

3. **Increment 3**: Phase 5 (User Story 3)
   - Robust error handling
   - Status monitoring
   - Graceful degradation

4. **Increment 4**: Phase 6 (Polish)
   - Test coverage
   - Documentation
   - Code quality

### Testing Strategy

- **Unit Tests**: Test individual components (models, graph builder, API client) in isolation
- **Integration Tests**: Test data flow from API → graph → visualization
- **Manual Testing**: Verify real-time updates, transaction flows, error handling with actual Cardano testnet

### Risk Mitigation

- **API Rate Limits**: Implemented in Phase 5 (US3) with exponential backoff
- **Graph Performance**: Monitor node count, implement pruning if needed (future enhancement)
- **Browser Compatibility**: Test PyVis visualization in multiple browsers during Phase 3
- **API Availability**: Graceful degradation implemented in Phase 5

---

## Notes

- All file paths are relative to repository root
- Environment variables should be loaded from `.env` file (not committed to git)
- Blockfrost API key required for testnet access (free tier available)
- PyVis generates standalone HTML - can be served statically or via Flask
- NetworkX graph is in-memory only (no persistence for POC)
- Polling interval configurable via environment variable (default: 2 seconds)
- SSE updates can fallback to polling if browser compatibility issues arise

---

## Validation Checklist

- [x] All tasks follow format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
- [x] Each user story has independent test criteria
- [x] Tasks are organized by user story phase
- [x] Dependencies are clearly identified
- [x] Parallel execution opportunities are documented
- [x] MVP scope is defined
- [x] File paths are specified for each task
- [x] Task IDs are sequential (T001-T045)
- [x] User story labels ([US1], [US2], [US3]) are present for story phase tasks
- [x] Parallelizable tasks are marked with [P]

