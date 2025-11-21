# graph-chain

Cardano Blockchain Graph Visualization - A proof-of-concept system for visualizing Cardano blockchain data as an interactive graph.

## Overview

This project provides a real-time visualization of Cardano blockchain activity, displaying blocks, transactions, and addresses as nodes in a connected graph. The system fetches data from Cardano networks (mainnet, preview, or preprod) via Blockfrost API and renders it using PyVis in a Flask web application.

## Features

- **Real-time Visualization**: See new blocks and transactions appear automatically as they occur on the blockchain
- **Transaction Flow Tracking**: Trace how value moves between addresses through transaction connections
- **Graceful Error Handling**: Automatic recovery from API rate limits and network issues
- **Interactive Graph**: Explore blockchain relationships with an interactive network visualization

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
│   └── web_server.py    # Flask web server
├── static/
│   └── index.html       # Frontend visualization
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

- `GET /` - Main visualization page
- `GET /api/graph` - Get current graph state (JSON)
- `GET /api/graph/updates` - Server-Sent Events stream for real-time updates
- `GET /api/status` - System status information

See `specs/001-cardano-graph-visualization/contracts/api.yaml` for full API documentation.

## Testing

Run tests with pytest:

```bash
pytest tests/
```

## Documentation

- [Feature Specification](specs/001-cardano-graph-visualization/spec.md)
- [Implementation Plan](specs/001-cardano-graph-visualization/plan.md)
- [Data Model](specs/001-cardano-graph-visualization/data-model.md)
- [Quickstart Guide](specs/001-cardano-graph-visualization/quickstart.md)
- [API Contracts](specs/001-cardano-graph-visualization/contracts/api.yaml)

## Notes

- This is a proof-of-concept - not production-ready
- Data is stored in-memory only (lost on restart)
- Supports mainnet, preview, and preprod networks
- Designed for single-user, local development use

## License

[Add license information here]