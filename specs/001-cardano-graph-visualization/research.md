# Research: Cardano Blockchain Graph Visualization

**Date**: 2025-01-27  
**Feature**: Cardano Blockchain Graph Visualization  
**Purpose**: Resolve technical decisions and clarify implementation choices

## Research Questions & Decisions

### 1. Python Version Selection

**Question**: What is the minimum Python version requirement?

**Decision**: Python 3.10+

**Rationale**: 
- Python 3.10 introduced structural pattern matching and improved type hints
- Flask 3.x requires Python 3.10+
- Most modern Python libraries support 3.10+
- 3.10 is widely available and stable

**Alternatives Considered**:
- Python 3.11+: Newer features but less universal availability
- Python 3.9: Older, may have compatibility issues with newer libraries
- Python 3.12+: Too new, may have library compatibility issues

---

### 2. Cardano API Provider Selection

**Question**: Should we use Blockfrost or Koios for Cardano testnet data?

**Decision**: Blockfrost

**Rationale**:
- Blockfrost provides official Python SDK (`blockfrost-python`)
- Well-documented REST API with clear rate limits
- Free tier available for testnet with reasonable limits
- Simple authentication via API key
- Active maintenance and community support
- Testnet endpoint readily available

**Alternatives Considered**:
- Koios: Community-maintained, may have less stable SDK support
- Direct node connection: Too complex for POC, requires running Cardano node

**Implementation Notes**:
- Use `blockfrost-python` SDK package
- API key stored in environment variable `BLOCKFROST_API_KEY`
- Testnet endpoint: `https://cardano-testnet.blockfrost.io/api/v0`
- Rate limits: Free tier typically 10 requests/second (need to verify)

---

### 3. Graph Visualization Library Selection

**Question**: Should we use PyVis, NetworkX with browser frontend, or D3.js?

**Decision**: PyVis

**Rationale**:
- PyVis generates interactive HTML/JavaScript visualizations automatically
- Minimal frontend code required - perfect for POC
- Built on vis.js, provides smooth animations
- Easy to update graph incrementally via Python
- Can export to standalone HTML file
- Supports real-time updates by regenerating HTML or using embedded JavaScript

**Alternatives Considered**:
- NetworkX + D3.js: More control but requires significant frontend development
- NetworkX + matplotlib: Static visualization, not suitable for real-time updates
- Pure D3.js: Requires extensive JavaScript development, defeats simplicity goal

**Implementation Notes**:
- Use `pyvis` Python package
- Generate HTML with embedded JavaScript for real-time updates
- Can use Flask to serve HTML and update via Server-Sent Events (SSE) or polling
- NetworkX can be used for graph structure management, PyVis for rendering

---

### 4. Real-Time Update Mechanism

**Question**: How should the web interface receive real-time graph updates?

**Decision**: Server-Sent Events (SSE) with periodic graph regeneration

**Rationale**:
- SSE is simpler than WebSockets for one-way server-to-client updates
- Flask supports SSE natively via `flask.Response` with `stream=True`
- PyVis can generate updated HTML/JSON that frontend can merge
- Fallback to polling if SSE has compatibility issues
- Minimal complexity for POC

**Alternatives Considered**:
- WebSockets: More complex, bidirectional communication not needed
- Polling: Simpler but less efficient, acceptable fallback
- GraphQL subscriptions: Overkill for POC

**Implementation Notes**:
- Flask route `/api/graph/updates` streams SSE events
- Frontend JavaScript listens for updates and merges new nodes/edges
- PyVis network can be updated via JavaScript API without full page reload

---

### 5. Testing Approach

**Question**: How should we test async polling and web server functionality?

**Decision**: pytest with pytest-asyncio and Flask test client

**Rationale**:
- pytest is standard Python testing framework
- Flask provides test client for web server testing
- Mock Cardano API responses to avoid rate limits in tests
- Use `unittest.mock` to mock API calls and time.sleep
- Integration tests can use test fixtures with sample blockchain data

**Alternatives Considered**:
- unittest: More verbose, pytest is more Pythonic
- Manual testing only: Not acceptable for maintainable code
- End-to-end tests with real API: Too slow and unreliable

**Implementation Notes**:
- Unit tests for data_fetcher.py with mocked API responses
- Unit tests for graph_builder.py with sample transaction data
- Integration tests for Flask routes using test client
- Mock time.sleep to speed up polling tests

---

### 6. Performance Benchmarks

**Question**: What are specific performance goals and constraints?

**Decision**: 
- Update latency: < 3 seconds from blockchain event to graph display
- Node capacity: 100-1000 nodes simultaneously (POC scope)
- Polling interval: 1-3 seconds (configurable)
- Memory: < 500MB for in-memory graph (reasonable for POC)
- API rate limit handling: Exponential backoff, max 30 second delay

**Rationale**:
- Based on success criteria SC-001 (3 second update requirement)
- Based on success criteria SC-002 (100+ nodes requirement)
- Memory constraint prevents unbounded growth
- Rate limit handling ensures graceful degradation

**Alternatives Considered**:
- Lower memory: Would require data pruning, adds complexity
- Faster updates: May hit API rate limits, not necessary for POC
- More nodes: Would require optimization beyond POC scope

---

### 7. API Rate Limit Handling

**Question**: How should we handle Blockfrost API rate limits?

**Decision**: Exponential backoff with jitter, configurable retry limits

**Rationale**:
- Blockfrost free tier typically has 10 requests/second limit
- Exponential backoff prevents overwhelming API
- Jitter prevents thundering herd if multiple instances
- Configurable limits allow tuning for different tiers

**Implementation Notes**:
- Use `tenacity` library for retry logic with exponential backoff
- Detect 429 (Too Many Requests) status codes
- Pause polling when rate limited, resume after backoff period
- Log rate limit events for monitoring
- Display status to user in web interface

---

### 8. Graph Structure Management

**Question**: Should we use NetworkX for graph structure or custom implementation?

**Decision**: Use NetworkX for graph structure, PyVis for visualization

**Rationale**:
- NetworkX provides robust graph data structures and algorithms
- Easy to add/remove nodes and edges
- Can query graph structure (neighbors, paths, etc.)
- PyVis can convert NetworkX graphs to interactive visualizations
- Separation of concerns: NetworkX for data, PyVis for rendering

**Alternatives Considered**:
- Custom graph structure: Reinventing the wheel, NetworkX is battle-tested
- PyVis only: Less flexible for graph operations and queries
- Pure dictionary-based: More error-prone, less maintainable

**Implementation Notes**:
- Use NetworkX `DiGraph` (directed graph) for transaction flows
- Nodes: blocks, transactions, addresses (with type attribute)
- Edges: block→transaction, transaction→address (input/output)
- Convert NetworkX graph to PyVis network for rendering

---

## Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.10+ | Core implementation |
| Web Framework | Flask | 3.x | Web server for visualization |
| Graph Library | NetworkX | Latest | Graph data structure |
| Visualization | PyVis | Latest | Interactive graph rendering |
| Cardano API | blockfrost-python | Latest | Blockchain data access |
| HTTP Client | requests | Latest | API calls (or use blockfrost SDK) |
| Testing | pytest | Latest | Unit and integration tests |
| Retry Logic | tenacity | Latest | Rate limit handling |

## Dependencies to Install

```bash
pip install flask networkx pyvis blockfrost-python requests tenacity python-dotenv
```

## Configuration Requirements

- `BLOCKFROST_API_KEY`: Blockfrost API key for testnet
- `POLLING_INTERVAL`: Seconds between API polls (default: 2)
- `MAX_RETRIES`: Maximum retry attempts for API calls (default: 3)
- `RATE_LIMIT_BACKOFF`: Base seconds for exponential backoff (default: 1)

## Open Questions Resolved

All "NEEDS CLARIFICATION" items from Technical Context have been addressed:
- ✅ Python version: 3.10+
- ✅ Primary dependencies: Flask, NetworkX, PyVis, blockfrost-python
- ✅ Testing: pytest with mocks
- ✅ Performance goals: Defined specific benchmarks
- ✅ Constraints: Defined memory and rate limit handling
- ✅ Scale/Scope: POC scope clarified

## Next Steps

Proceed to Phase 1: Design & Contracts
- Generate data-model.md from feature spec entities
- Create API contracts for Flask endpoints
- Generate quickstart.md with setup instructions


