"""Flask web server for Cardano graph visualization."""

import sys
import os
from pathlib import Path

# Add project root to Python path to allow absolute imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
import threading
import json
import logging
import socket
from flask import Flask, jsonify, Response, send_from_directory, request
from src.graph_builder import GraphBuilder
from src.data_fetcher import DataFetcher
from src.config import validate_config, SERVER_PORT

# Setup logging (T040)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate configuration on import
try:
    validate_config()
except ValueError as e:
    print(f"Configuration error: {e}")

# Initialize Flask app
# Use absolute path for static folder since we're running from src/
static_folder_path = project_root / 'static'
app = Flask(__name__, static_folder=str(static_folder_path))

# Initialize graph and data fetcher
graph_builder = GraphBuilder()
data_fetcher = DataFetcher(graph_builder)

# Store update events for SSE
update_queue = []
update_lock = threading.Lock()


def on_graph_update(update_data):
    """Callback for graph updates to queue SSE events."""
    try:
        with update_lock:
            update_queue.append(update_data)
    except Exception as e:
        logger.error(f"Error in graph update callback: {e}")


# Register update callback
graph_builder.register_update_callback(on_graph_update)

# Start polling in background thread
polling_thread = None


def start_background_polling():
    """Start data fetching in background thread."""
    global polling_thread
    if polling_thread is None or not polling_thread.is_alive():
        polling_thread = threading.Thread(target=data_fetcher.start_polling, daemon=True)
        polling_thread.start()


@app.route('/')
def index():
    """Serve the main visualization page."""
    return send_from_directory(str(static_folder_path), 'index.html')


@app.route('/api/graph')
def get_graph():
    """Get current graph state as JSON."""
    try:
        graph_data = graph_builder.to_json()
        return jsonify(graph_data)
    except Exception as e:
        logger.error(f"Error getting graph: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/graph/updates')
def stream_updates():
    """Stream graph updates via Server-Sent Events."""
    def generate():
        last_index = 0
        while True:
            with update_lock:
                if last_index < len(update_queue):
                    for update in update_queue[last_index:]:
                        yield f"event: graph_update\n"
                        yield f"data: {json.dumps(update)}\n\n"
                    last_index = len(update_queue)
            time.sleep(1)  # Check for updates every second
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/status')
def get_status():
    """Get system status information."""
    try:
        # Get status from data_fetcher (T036, T037)
        fetcher_status = data_fetcher.get_status()
        
        # Determine overall status
        if data_fetcher.error_state and data_fetcher.consecutive_errors > 5:
            overall_status = 'error'
        elif data_fetcher.rate_limit_status.get('limited'):
            overall_status = 'paused'
        elif data_fetcher.running:
            overall_status = 'active'
        else:
            overall_status = 'stopped'
        
        status = {
            'status': overall_status,
            'api_status': fetcher_status.get('api_status', 'unknown'),
            'polling_status': fetcher_status.get('polling_status', 'stopped'),
            'rate_limit_status': fetcher_status.get('rate_limit_status', {'limited': False, 'retry_after': None}),
            'graph_stats': graph_builder.to_json().get('metadata', {}),
            'last_block_fetched': fetcher_status.get('last_block_fetched'),
            'polling_interval': data_fetcher.polling_interval,
            'error_message': fetcher_status.get('error_state'),  # T040
            'consecutive_errors': fetcher_status.get('consecutive_errors', 0),
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors gracefully."""
    # If it's an API request, return JSON
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not Found', 'path': request.path}), 404
    # Otherwise, redirect to index (for SPA-like behavior)
    return send_from_directory(str(static_folder_path), 'index.html'), 200


def find_free_port(start_port: int, max_attempts: int = 10) -> int:
    """Find a free port starting from start_port."""
    for i in range(max_attempts):
        port = start_port + i
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            sock.close()
            continue
    raise RuntimeError(f"Could not find a free port starting from {start_port}")


if __name__ == '__main__':
    # Start background polling
    start_background_polling()
    
    # Find an available port
    port = find_free_port(SERVER_PORT)
    if port != SERVER_PORT:
        logger.info(f"Port {SERVER_PORT} is in use, using port {port} instead")
    
    # Run Flask app
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

