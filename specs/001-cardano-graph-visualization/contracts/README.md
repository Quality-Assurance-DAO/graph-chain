# API Contracts

This directory contains API contract specifications for the Cardano Graph Visualization system.

## Files

- **api.yaml**: OpenAPI 3.0.3 specification defining all REST endpoints and data models

## Endpoints Overview

### Visualization
- `GET /` - Main HTML page with interactive graph visualization

### Graph API
- `GET /api/graph` - Get current graph state as JSON
- `GET /api/graph/updates` - Server-Sent Events stream for real-time updates

### Status
- `GET /api/status` - Get system status (API connection, polling, rate limits, graph stats)

## Data Models

### GraphNode
Represents a node in the graph (block, transaction, or address).

### GraphEdge
Represents an edge/relationship between nodes (block→transaction, address→transaction, transaction→address).

### GraphState
Complete graph state including all nodes, edges, and metadata.

### SystemStatus
System health and operational status information.

## Usage

The API contracts can be used to:
- Generate client SDKs
- Validate API responses
- Document API behavior
- Generate mock servers for testing

## Implementation Notes

- All timestamps use ISO 8601 format (UTC)
- Server-Sent Events (SSE) used for real-time updates (one-way server→client)
- JSON responses for all API endpoints
- Error responses follow consistent Error schema

## Testing

API contracts can be validated using:
- OpenAPI validators
- Contract testing tools (e.g., Pact, Schemathesis)
- Generated mock servers for integration testing


