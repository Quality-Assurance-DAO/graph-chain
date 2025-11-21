# graph-chain

Cardano Blockchain Graph Visualization - A proof-of-concept system for visualizing Cardano blockchain data as an interactive graph.

## Overview

This project provides a real-time visualization of Cardano blockchain activity, displaying blocks, transactions, and addresses as nodes in a connected graph. The system fetches data from Cardano networks (mainnet, preview, or preprod) via Blockfrost API and renders it using PyVis in a Flask web application.

## Features

- **Real-time Visualization**: See new blocks and transactions appear automatically as they occur on the blockchain
- **Transaction Flow Tracking**: Trace how value moves between addresses through transaction connections
- **Graceful Error Handling**: Automatic recovery from API rate limits and network issues
- **Interactive Graph**: Explore blockchain relationships with an interactive network visualization
- **Graph Analytics**: Lightweight local analytics on loaded data including:
  - **Node Degree Metrics**: View transaction counts per block, input/output counts per transaction
  - **Color-Coded Activity**: Visual heatmaps showing activity levels (heatmap, activity, grayscale schemes)
  - **Anomaly Detection**: Identify unusually large transactions or blocks with high transaction counts
  - **Clustering**: Discover clusters of related addresses or transactions
  - **Flow Path Visualization**: Click transactions to see value flow paths through the graph

## Quick Start

For detailed setup instructions, see the [Quickstart Guide](specs/001-cardano-graph-visualization/quickstart.md).

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Blockfrost API key ([Get one here](https://blockfrost.io/))
  - For mainnet: Use mainnet API key
  - For testing: Use preview or preprod API key (testnet is decommissioned)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd graph-chain

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip3 install -r requirements.txt
# Or use: python3 -m pip install -r requirements.txt

# Configure environment
cp config/.env.example .env
# Edit .env and add your BLOCKFROST_API_KEY

# Run the application (make sure virtual environment is activated)
python3 src/web_server.py
# Or: python src/web_server.py (if venv is activated)
```

Then open your browser to `http://localhost:5000` to see the visualization.

## Project Structure

```
graph-chain/
├── src/
│   ├── models/          # Data models (Block, Transaction, Address)
│   ├── api/             # Blockfrost API client
│   ├── data_fetcher.py  # Data ingestion and polling
│   ├── graph_builder.py # Graph structure management
│   ├── analytics_engine.py # Analytics calculations (degree, color, anomaly, clustering, flow)
│   └── web_server.py    # Flask web server
├── static/
│   └── index.html       # Frontend visualization with analytics UI
├── tests/
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── config/
│   └── .env.example     # Environment variable template
└── specs/               # Feature specifications and documentation
```

## Configuration

See `config/.env.example` for available configuration options:

- `BLOCKFROST_API_KEY`: Your Blockfrost API key (required)
- `NETWORK`: Network to use - `mainnet`, `preview`, or `preprod` (default: `mainnet`)
  - `mainnet`: Production Cardano network
  - `preview`: Preview testnet (for early-stage testing)
  - `preprod`: Pre-production testnet (for late-stage testing)
  - Note: `testnet` is decommissioned but kept for compatibility
- `POLLING_INTERVAL`: Seconds between API polls (default: 2)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)
- `RATE_LIMIT_BACKOFF`: Base seconds for exponential backoff (default: 1)
- `SERVER_PORT`: Web server port (default: 5001)

## API Endpoints

### Core Endpoints

- `GET /` - Main visualization page
- `GET /api/graph` - Get current graph state (JSON)
- `GET /api/graph/updates` - Server-Sent Events stream for real-time updates
- `GET /api/status` - System status information
- `GET /api/nodes` - Browse and search nodes

### Analytics Endpoints

- `GET /api/analytics/degrees` - Get node degree metrics (transaction counts, input/output counts)
  - Query params: `node_type` (optional), `node_id` (optional)
- `GET /api/analytics/activity` - Get activity metrics and color mappings
  - Query params: `node_type` (optional), `color_scheme` (heatmap|activity|grayscale, default: heatmap)
- `GET /api/analytics/anomalies` - Detect anomalies in loaded data
  - Query params: `node_type` (optional), `method` (zscore|percentile|threshold, default: percentile), `threshold` (default: 2.0)
  - Requires minimum 10 nodes for statistical validity
- `GET /api/analytics/clusters` - Perform clustering analysis
  - Query params: `cluster_type` (address|transaction, required), `time_window_blocks` (20-50, default: 30)
- `GET /api/analytics/flow` - Get transaction flow paths
  - Query params: `transaction_id` (optional), `start_address` (optional), `max_depth` (1-10, default: 5), `max_blocks` (1-10, default: 5)
- `POST /api/analytics/recalculate` - Force recalculation of all analytics metrics

See `specs/001-cardano-graph-visualization/contracts/api.yaml` and `specs/002-graph-analytics/contracts/api.yaml` for full API documentation.

## Testing

Run tests with pytest:

```bash
pytest tests/
```

## Documentation

### Core Visualization

- [Feature Specification](specs/001-cardano-graph-visualization/spec.md)
- [Implementation Plan](specs/001-cardano-graph-visualization/plan.md)
- [Data Model](specs/001-cardano-graph-visualization/data-model.md)
- [Quickstart Guide](specs/001-cardano-graph-visualization/quickstart.md)
- [API Contracts](specs/001-cardano-graph-visualization/contracts/api.yaml)

### Graph Analytics

- [Analytics Feature Specification](specs/002-graph-analytics/spec.md)
- [Analytics Implementation Plan](specs/002-graph-analytics/plan.md)
- [Analytics API Contracts](specs/002-graph-analytics/contracts/api.yaml)

## Usage Examples

### Using Analytics API

```python
import requests

# Get degree metrics for all blocks
response = requests.get('http://localhost:5000/api/analytics/degrees?node_type=block')
data = response.json()
for metric in data['metrics']:
    print(f"Block {metric['node_id']}: {metric['type_degree']} transactions")

# Get activity metrics with heatmap color scheme
response = requests.get('http://localhost:5000/api/analytics/activity?color_scheme=heatmap')
data = response.json()
for metric in data['metrics']:
    print(f"Node {metric['node_id']}: activity={metric['normalized_value']:.1f}, color={metric['color_hex']}")

# Detect anomalies using percentile method
response = requests.get('http://localhost:5000/api/analytics/anomalies?method=percentile')
data = response.json()
for anomaly in data['anomalies']:
    print(f"Anomaly: {anomaly['node_id']} ({anomaly['anomaly_type']}) - score: {anomaly['anomaly_score']:.1f}")

# Cluster addresses from last 30 blocks
response = requests.get('http://localhost:5000/api/analytics/clusters?cluster_type=address&time_window_blocks=30')
data = response.json()
print(f"Found {data['total_clusters']} clusters with {data['nodes_clustered']} addresses")

# Get flow paths for a transaction
response = requests.get('http://localhost:5000/api/analytics/flow?transaction_id=tx_abc123&max_depth=5')
data = response.json()
for path in data['paths']:
    print(f"Path: {path['path_nodes']} - Value: {path['total_value']}")
```

### Frontend Usage

The web interface includes:
- **Color Scheme Selector**: Switch between heatmap, activity, and grayscale color schemes
- **Degree Metrics Display**: Node labels show transaction counts (blocks) and input/output counts (transactions)
- **Flow Path Visualization**: Click any transaction node to highlight its flow paths
- **Recalculate Button**: Force recalculation of analytics metrics after loading new data

## Notes

- This is a proof-of-concept - not production-ready
- Data is stored in-memory only (lost on restart)
- Supports mainnet, preview, and preprod networks
- Designed for single-user, local development use
- Analytics operate only on loaded data subset (not historical data)
- Anomaly detection requires minimum 10 nodes for statistical validity

## License

[Add license information here]