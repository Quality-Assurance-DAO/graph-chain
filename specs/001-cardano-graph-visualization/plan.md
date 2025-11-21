# Implementation Plan: Cardano Blockchain Graph Visualization

**Branch**: `001-cardano-graph-visualization` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-cardano-graph-visualization/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a lightweight Python proof-of-concept that visualizes Cardano blockchain data as a dynamic graph. The system fetches blocks and transactions from Cardano testnet via Blockfrost API, parses them into a NetworkX graph structure, and renders them using PyVis in a Flask web application with real-time updates via Server-Sent Events. Architecture is minimal: `data_fetcher.py` for API polling, `graph_builder.py` for graph management, and `web_server.py` for Flask web server. Uses Python 3.10+, Flask 3.x, NetworkX, PyVis, and blockfrost-python SDK.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: Flask 3.x (web server), NetworkX (graph structure), PyVis (visualization), blockfrost-python (Cardano API), requests (HTTP), tenacity (retry logic)  
**Storage**: In-memory graph structure using NetworkX (no persistent storage for POC)  
**Testing**: pytest with Flask test client, unittest.mock for API mocking, pytest-asyncio if needed  
**Target Platform**: Cross-platform (Linux/macOS/Windows), modern web browser for visualization  
**Project Type**: web (Flask backend + browser frontend)  
**Performance Goals**: Update latency < 3 seconds, support 100-1000 nodes, polling interval 1-3 seconds (configurable), memory < 500MB  
**Constraints**: Blockfrost API rate limits (10 req/s free tier), exponential backoff for rate limit handling, browser rendering performance for large graphs  
**Scale/Scope**: POC scope - 100-1000 nodes, single user, Cardano testnet only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file at `.specify/memory/constitution.md` appears to be a template. No specific gates can be evaluated until constitution is defined. Proceeding with plan assuming standard development practices.

**Gates to evaluate** (once constitution is defined):
- [ ] Technology stack compliance
- [ ] Architecture simplicity requirements
- [ ] Testing requirements
- [ ] Documentation requirements

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
├── data_fetcher.py      # Data ingestion: polls Cardano API, fetches blocks/transactions
├── graph_builder.py     # Graph handling: parses blockchain data into graph structure
└── web_server.py        # Flask app: serves visualization and WebSocket/SSE updates

static/
└── index.html           # Frontend: graph visualization UI (may include embedded JS)

tests/
├── unit/
│   ├── test_data_fetcher.py
│   ├── test_graph_builder.py
│   └── test_web_server.py
└── integration/
    └── test_end_to_end.py

config/
└── .env.example         # Environment variable template for API keys
```

**Structure Decision**: Simple single-project structure with minimal separation. Three core Python modules (data_fetcher, graph_builder, web_server) as specified in requirements. Static HTML/JS for frontend visualization. Tests organized by unit/integration. Configuration via environment variables.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
