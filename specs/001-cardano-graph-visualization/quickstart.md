# Quickstart Guide: Cardano Graph Visualization

**Date**: 2025-01-27  
**Feature**: Cardano Blockchain Graph Visualization

This guide will help you get the Cardano blockchain graph visualization POC running quickly.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Blockfrost API key for Cardano testnet (free tier available)
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Step 1: Get Blockfrost API Key

1. Visit [Blockfrost.io](https://blockfrost.io/)
2. Sign up for a free account
3. Navigate to your project dashboard
4. Create a new project for **Cardano Testnet**
5. Copy your API key (starts with `testnet...`)

## Step 2: Clone and Setup

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd graph-chain

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask networkx pyvis blockfrost-python requests tenacity python-dotenv
```

## Step 3: Configure Environment

Create a `.env` file in the project root:

```bash
# Copy example file
cp config/.env.example .env

# Edit .env and add your API key
BLOCKFROST_API_KEY=testnet_your_api_key_here
POLLING_INTERVAL=2
MAX_RETRIES=3
RATE_LIMIT_BACKOFF=1
```

Or set environment variables directly:

```bash
export BLOCKFROST_API_KEY=testnet_your_api_key_here
export POLLING_INTERVAL=2
```

## Step 4: Run the Application

```bash
# Start the Flask web server
python src/web_server.py
```

Or if using Flask CLI:

```bash
export FLASK_APP=src/web_server.py
flask run
```

The server will start on `http://localhost:5000` by default.

## Step 5: View the Visualization

1. Open your web browser
2. Navigate to `http://localhost:5000`
3. You should see the graph visualization interface
4. New blocks and transactions will appear automatically as they occur on the Cardano testnet

## What to Expect

- **Initial Load**: The graph may be empty initially. It will populate as new blocks are detected.
- **Real-Time Updates**: New nodes (blocks, transactions, addresses) will appear automatically.
- **Graph Structure**: 
  - Blocks appear as nodes
  - Transactions appear as nodes connected to blocks
  - Addresses appear as nodes connected to transactions
  - Edges show the flow: address → transaction → address

## Configuration Options

Edit constants in `src/data_fetcher.py` or `src/web_server.py`:

```python
# Polling interval (seconds)
POLLING_INTERVAL = 2  # Check for new blocks every 2 seconds

# Maximum retries for API calls
MAX_RETRIES = 3

# Rate limit backoff (base seconds)
RATE_LIMIT_BACKOFF = 1
```

## Troubleshooting

### API Key Issues

**Error**: "Invalid API key" or 401 Unauthorized
- Verify your API key is correct
- Ensure you're using the testnet API key (starts with `testnet`)
- Check that the API key is set in environment variables

### Rate Limit Issues

**Error**: "Rate limit exceeded" or 429 Too Many Requests
- The system will automatically back off and retry
- Increase `POLLING_INTERVAL` to reduce request frequency
- Check your Blockfrost tier limits

### No Data Appearing

**Issue**: Graph remains empty
- Verify Cardano testnet is active (check blockfrost.io status)
- Check console/logs for API errors
- Ensure network connectivity to Blockfrost API
- Wait a few minutes - blocks may not be created immediately on testnet

### Port Already in Use

**Error**: "Address already in use"
- Change the port in `src/web_server.py`:
  ```python
  app.run(host='0.0.0.0', port=5001)  # Use different port
  ```
- Or stop the process using port 5000

### Browser Compatibility

**Issue**: Visualization doesn't load
- Ensure JavaScript is enabled
- Try a different browser
- Check browser console for errors (F12)

## Project Structure

```
graph-chain/
├── src/
│   ├── data_fetcher.py    # Fetches data from Blockfrost API
│   ├── graph_builder.py   # Builds and manages graph structure
│   └── web_server.py      # Flask web server
├── static/
│   └── index.html         # Frontend visualization
├── config/
│   └── .env.example       # Environment variable template
└── tests/                 # Test files
```

## Next Steps

- **Explore the Code**: Review `src/data_fetcher.py`, `src/graph_builder.py`, and `src/web_server.py`
- **Customize Visualization**: Modify `static/index.html` to change graph appearance
- **Add Features**: See feature spec for ideas on expanding the POC
- **Run Tests**: Execute `pytest tests/` to verify functionality

## API Endpoints

- `GET /` - Main visualization page
- `GET /api/graph` - Get current graph state (JSON)
- `GET /api/graph/updates` - Server-Sent Events stream for updates
- `GET /api/status` - System status information

See `contracts/api.yaml` for full API documentation.

## Support

For issues or questions:
- Check the logs/console output for error messages
- Review the feature specification: `specs/001-cardano-graph-visualization/spec.md`
- Review the data model: `specs/001-cardano-graph-visualization/data-model.md`

## Notes

- This is a proof-of-concept - not production-ready
- Data is stored in-memory only (lost on restart)
- Focuses on Cardano testnet only
- Designed for single-user, local development use

