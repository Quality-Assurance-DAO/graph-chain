# Implementation Plan: Lightweight Local Graph Analytics

**Branch**: `002-graph-analytics` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-graph-analytics/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add lightweight, local graph analytics capabilities to the Cardano blockchain visualization system. Analytics will operate on the loaded data subset and include: node degree calculations (block/transaction/address), color coding based on activity metrics, anomaly detection for unusual transactions/blocks, simple clustering for related addresses/transactions, and transaction flow visualization. All calculations performed locally using NetworkX graph algorithms, with visual feedback through color gradients and highlighting.

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: Flask 3.0+, NetworkX 3.0+, PyVis 0.3.2+, blockfrost-python 0.6.0+, pytest 7.4+  
**Storage**: In-memory (NetworkX DiGraph), no persistent storage required  
**Testing**: pytest with pytest-asyncio for async tests  
**Target Platform**: Web application (Flask backend + static HTML/JS frontend)  
**Project Type**: Web application (single project with backend API and frontend visualization)  
**Performance Goals**: Analytics calculations complete within 2 seconds for datasets up to 1000 nodes (SC-008)  
**Constraints**: 
  - Local analytics only (operates on loaded data subset, no external API calls for analytics)
  - Must update automatically when new data is loaded (within 3 seconds per SC-009)
  - Memory-efficient (current MAX_NODES=30, but should scale to 1000 nodes)
  - Synchronous calculation model (no async analytics processing)
**Scale/Scope**: 
  - Graph size: Up to 1000 nodes (blocks, transactions, addresses)
  - Time window: Last 20-50 blocks for clustering (configurable)
  - Recent blocks: Last 5-10 blocks for flow visualization
  - Analytics features: 5 core capabilities (degree metrics, color coding, anomaly detection, clustering, flow visualization)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file appears to be a template. Proceeding with standard development practices:
- Test-first development (pytest)
- Integration tests for API endpoints
- Code review and quality gates
- Simplicity and YAGNI principles

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── models/              # Data models (Block, Transaction, Address)
│   ├── __init__.py
│   ├── block.py
│   ├── transaction.py
│   └── address.py
├── api/                 # API client (Blockfrost)
│   └── blockfrost_client.py
├── graph_builder.py     # NetworkX graph management (existing)
├── data_fetcher.py      # Data polling and fetching (existing)
├── web_server.py        # Flask API server (existing)
├── analytics.py         # NEW: Analytics engine for calculations
└── config.py            # Configuration management

static/
└── index.html           # Frontend visualization (PyVis)

tests/
├── unit/
│   ├── test_data_fetcher.py
│   ├── test_graph_builder.py
│   ├── test_web_server.py
│   └── test_analytics.py        # NEW: Analytics unit tests
└── integration/
    └── test_end_to_end.py
```

**Structure Decision**: Single web application project. Analytics functionality will be added as a new `analytics.py` module that extends `GraphBuilder` capabilities. Analytics calculations will be integrated into the existing graph update flow and exposed via new API endpoints. Frontend will consume analytics data through existing `/api/graph` endpoint with enhanced node/edge metadata.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
