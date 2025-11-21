# Implementation Plan: Lightweight Local Graph Analytics

**Branch**: `002-graph-analytics` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-graph-analytics/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add lightweight graph analytics capabilities to the existing Cardano blockchain visualization system. Analytics operate locally on the loaded data subset using NetworkX algorithms. Features include: node degree calculation (block/transaction/address), color-coded activity visualization (heatmap scheme), percentile-based anomaly detection, community clustering for addresses/transactions, and transaction flow path visualization. Implementation extends the existing `GraphBuilder` with an `AnalyticsEngine` class that computes metrics incrementally, caches results, and provides API endpoints for querying analytics. Uses NetworkX built-in algorithms (degree methods, community detection, path finding) and HSL color space for activity visualization. No new dependencies required.

## Technical Context

**Language/Version**: Python 3.10+ (matches existing project)  
**Primary Dependencies**: NetworkX 3.0+ (graph algorithms), Flask 3.x (API endpoints), NumPy (statistical calculations - optional enhancement)  
**Storage**: In-memory analytics metrics stored as NetworkX node/edge attributes (no persistent storage)  
**Testing**: pytest with Flask test client, unittest.mock for analytics calculations, integration tests for API endpoints  
**Target Platform**: Cross-platform (Linux/macOS/Windows), modern web browser for visualization  
**Project Type**: web (extends existing Flask backend + browser frontend)  
**Performance Goals**: Analytics calculations complete within 2 seconds for datasets up to 1000 nodes, degree calculation < 10ms for 1000 nodes, color coding < 50ms for 1000 nodes, anomaly detection < 100ms for 1000 nodes, clustering < 500ms for 500 nodes  
**Constraints**: Analytics operate only on loaded data subset (not historical data), minimum 10 nodes required for statistical anomaly detection, clustering limited to recent blocks (20-50 block window), flow paths limited to max_depth=5-10 hops  
**Scale/Scope**: Supports datasets up to 1000 nodes, single user, operates on loaded blockchain data subset

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file at `.specify/memory/constitution.md` appears to be a template. No specific gates can be evaluated until constitution is defined. Proceeding with plan assuming standard development practices.

**Gates to evaluate** (once constitution is defined):
- [ ] Technology stack compliance (using existing NetworkX/Flask stack)
- [ ] Architecture simplicity requirements (extending existing GraphBuilder vs new service)
- [ ] Testing requirements (unit tests for analytics calculations, integration tests for API)
- [ ] Documentation requirements (API contracts, quickstart guide)

## Project Structure

### Documentation (this feature)

```text
specs/002-graph-analytics/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── api.yaml         # OpenAPI specification for analytics endpoints
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── graph_builder.py     # Existing: Graph structure management (extends with analytics)
├── analytics_engine.py  # NEW: Analytics calculations (degree, color, anomaly, clustering, flow)
├── web_server.py        # Existing: Flask app (extends with analytics API endpoints)
├── data_fetcher.py      # Existing: Data ingestion
└── models/              # Existing: Block, Transaction, Address models

static/
└── index.html           # Existing: Frontend visualization (extends with analytics UI)

tests/
├── unit/
│   ├── test_graph_builder.py      # Existing
│   ├── test_analytics_engine.py   # NEW: Analytics calculation tests
│   └── test_web_server.py          # Existing (extends with analytics endpoint tests)
└── integration/
    └── test_end_to_end.py         # Existing (extends with analytics integration tests)
```

**Structure Decision**: Extends existing single-project structure. New `analytics_engine.py` module wraps/extends `GraphBuilder` to provide analytics functionality. Analytics API endpoints added to existing `web_server.py`. Frontend `index.html` extended with analytics visualization controls. Tests follow existing unit/integration structure.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
