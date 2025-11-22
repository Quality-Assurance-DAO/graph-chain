# graph-chain

Cardano Blockchain Graph Visualization - A proof-of-concept system for visualizing Cardano blockchain data as an interactive graph.

## Overview

This project provides a real-time visualization of Cardano blockchain activity, displaying blocks, transactions, and addresses as nodes in a connected graph. The system fetches data from Cardano networks (mainnet, preview, or preprod) via Blockfrost API and renders it using PyVis in a Flask web application.

## Features

### Real-time Visualization

The system continuously polls the Cardano blockchain via Blockfrost API and automatically adds new blocks, transactions, and addresses to the graph as they appear on-chain. New nodes animate into view, and the graph updates in real-time using Server-Sent Events (SSE) for seamless updates without page refreshes. This allows you to watch blockchain activity unfold live, seeing blocks being created and transactions being processed as they happen.

### Transaction Flow Tracking

Visualize how value (ADA and tokens) moves through the blockchain by following connections between addresses and transactions. Each transaction node connects to its input addresses (sources of funds) and output addresses (destinations). The graph structure makes it easy to trace value flow paths, understand transaction relationships, and identify patterns in how addresses interact with each other. Edge labels show transaction amounts, making it clear how much value moves along each connection.

### Graceful Error Handling

The system handles API limitations and network issues gracefully. When rate limits are encountered, it automatically implements exponential backoff and pauses polling until the rate limit window expires. If the API becomes temporarily unavailable, the system continues displaying existing graph data while attempting to reconnect. Status indicators show the current system state (active, paused, error) and provide clear feedback about any issues without disrupting the user experience.

### Interactive Graph

Explore blockchain relationships through an interactive network visualization powered by PyVis. Features include:
- **Zoom and Pan**: Navigate large graphs smoothly
- **Node Interaction**: Hover over nodes to highlight connected nodes and edges
- **Click to Focus**: Click any node to center the view and highlight its connections
- **Browse Panel**: Search and filter nodes by type (blocks, transactions, addresses)
- **Theme Toggle**: Switch between light and dark themes
- **View Modes**: Toggle between Block View (high-level block chain) and Transaction View (detailed transaction flows)

### Graph Analytics

Perform lightweight local analytics on the loaded data subset to gain insights into blockchain patterns:

#### Node Degree Metrics

Understand activity levels by viewing connection counts for each node:
- **Block Nodes**: Display the number of transactions contained in each block, helping identify "busy" blocks with high transaction volumes
- **Transaction Nodes**: Show input and output counts, revealing transactions with many inputs/outputs
- **Address Nodes**: Display UTxO (Unspent Transaction Output) counts, indicating address activity

Metrics appear in node labels and detailed tooltips, making it easy to identify high-activity nodes at a glance.

#### Color-Coded Activity

Visual heatmaps use color intensity to represent activity levels without reading numerical values:
- **Heatmap Scheme** (default): Red (low activity) → Yellow (medium) → Green (high activity)
- **Activity Scheme**: Blue (low) → Purple (medium) → Red (high)
- **Grayscale Scheme**: Black (low) → Gray → White (high) - useful for printing or colorblind accessibility

Colors are calculated based on:
- **Blocks**: Transaction count per block
- **Transactions**: Total input/output count
- **Addresses**: UTxO count

Switch between color schemes using the dropdown selector in the analytics panel.

#### Anomaly Detection

Identify unusual patterns in blockchain data using statistical methods:
- **Percentile Method** (default): Flags nodes above the 95th percentile or below the 5th percentile
- **Z-Score Method**: Detects nodes where values deviate significantly from the mean (|value - mean| > 2 * std)
- **Threshold Method**: Flags nodes exceeding a configurable threshold multiplier of the average

Anomalous nodes are visually highlighted with:
- Thick red borders
- Glow/shadow effects
- Anomaly count display in the analytics panel

**Note**: Requires minimum 10 nodes for statistical validity. Useful for spotting unusually large transactions, blocks with abnormally high transaction counts, or other outliers that might warrant investigation.

#### Clustering

Discover groups of related addresses or transactions that frequently interact:
- **Address Clustering**: Groups addresses that frequently transact with each other within a time window (default: last 30 blocks, configurable: 20-50 blocks)
- **Transaction Clustering**: Groups transactions that share common addresses, revealing transaction patterns

Clusters are identified using NetworkX's community detection algorithms (greedy modularity communities). Each cluster is assigned a unique color, making it easy to visually distinguish different groups. This helps identify:
- Related wallet addresses
- Transaction patterns
- Repeated interaction groups
- Potential address relationships

#### Flow Path Visualization

Trace how value flows through the blockchain by clicking on any transaction node:
- **Path Highlighting**: Green edges highlight the complete flow path from input addresses through the transaction to output addresses
- **Path Discovery**: Automatically finds paths up to 5-10 hops deep through recent blocks (last 5-10 blocks)
- **Value Aggregation**: Shows total value flowing along each path
- **Interactive Exploration**: Click anywhere else to clear the visualization and explore different transactions

This feature helps understand:
- How value moves through multiple transactions
- Common flow patterns in recent blocks
- Transaction relationships and dependencies
- Value routing through the network

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