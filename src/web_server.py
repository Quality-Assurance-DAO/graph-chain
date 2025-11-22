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
from src.analytics_engine import AnalyticsEngine
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
analytics_engine = AnalyticsEngine(graph_builder)

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
        # Get max_blocks parameter for dynamic collapsing
        max_blocks = request.args.get('max_blocks', type=int)
        graph_data = graph_builder.to_json(max_blocks=max_blocks)
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


@app.route('/api/nodes')
def browse_nodes():
    """Browse and search nodes in the graph."""
    try:
        search_query = request.args.get('q', '').lower()
        node_type = request.args.get('type', '')  # 'block', 'transaction', 'address', or '' for all
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        graph_data = graph_builder.to_json()
        all_nodes = graph_data.get('nodes', [])
        
        # Filter nodes
        filtered_nodes = []
        for node in all_nodes:
            # Type filter
            if node_type and node.get('type') != node_type:
                continue
            
            # Search filter
            if search_query:
                node_data = node.get('data', {})
                label = node.get('label', '').lower()
                node_id = node.get('id', '').lower()
                
                # Search in label, id, and data fields
                matches = (
                    search_query in label or
                    search_query in node_id or
                    search_query in str(node_data.get('block_hash', '')).lower() or
                    search_query in str(node_data.get('tx_hash', '')).lower() or
                    search_query in str(node_data.get('address', '')).lower() or
                    search_query in str(node_data.get('block_height', '')).lower()
                )
                if not matches:
                    continue
            
            filtered_nodes.append(node)
        
        # Apply pagination
        total = len(filtered_nodes)
        paginated_nodes = filtered_nodes[offset:offset + limit]
        
        return jsonify({
            'nodes': paginated_nodes,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total
        })
    except Exception as e:
        logger.error(f"Error browsing nodes: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/nodes/<node_id>')
def get_node(node_id):
    """Get detailed information about a specific node."""
    try:
        graph_data = graph_builder.to_json()
        nodes = graph_data.get('nodes', [])
        
        # Find the node
        node = next((n for n in nodes if n.get('id') == node_id), None)
        if not node:
            return jsonify({'error': 'Node not found'}), 404
        
        # Get connected nodes and edges
        edges = graph_data.get('edges', [])
        connected_edges = [e for e in edges if e.get('from') == node_id or e.get('to') == node_id]
        connected_node_ids = set()
        for edge in connected_edges:
            if edge.get('from') == node_id:
                connected_node_ids.add(edge.get('to'))
            if edge.get('to') == node_id:
                connected_node_ids.add(edge.get('from'))
        
        connected_nodes = [n for n in nodes if n.get('id') in connected_node_ids]
        
        return jsonify({
            'node': node,
            'connected_nodes': connected_nodes,
            'connected_edges': connected_edges,
            'connection_count': len(connected_node_ids)
        })
    except Exception as e:
        logger.error(f"Error getting node: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/degrees')
def get_analytics_degrees():
    """Get node degree metrics."""
    try:
        node_type = request.args.get('node_type')
        node_id = request.args.get('node_id')
        
        metrics = analytics_engine.get_degree_metrics(node_type=node_type, node_id=node_id)
        
        # Calculate statistics
        total_nodes = len(analytics_engine.graph.nodes())
        nodes_by_type = {}
        for node_id in analytics_engine.graph.nodes():
            node_type = analytics_engine.graph.nodes[node_id].get('type', 'unknown')
            nodes_by_type[node_type] = nodes_by_type.get(node_type, 0) + 1
        
        return jsonify({
            'metrics': metrics,
            'statistics': {
                'total_nodes': total_nodes,
                'nodes_by_type': nodes_by_type,
            }
        })
    except Exception as e:
        logger.error(f"Error getting degree metrics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/activity')
def get_analytics_activity():
    """Get activity metrics and color mappings."""
    try:
        node_type = request.args.get('node_type')
        color_scheme = request.args.get('color_scheme', 'heatmap')
        
        if color_scheme not in ['heatmap', 'activity', 'grayscale']:
            color_scheme = 'heatmap'
        
        metrics = analytics_engine.get_activity_metrics(node_type=node_type, color_scheme=color_scheme)
        
        # Calculate normalization stats
        normalization_stats = {}
        if metrics:
            raw_values = [m['raw_value'] for m in metrics]
            if raw_values:
                normalization_stats = {
                    'min_value': min(raw_values),
                    'max_value': max(raw_values),
                    'mean_value': sum(raw_values) / len(raw_values),
                }
        
        return jsonify({
            'metrics': metrics,
            'color_scheme': color_scheme,
            'normalization_stats': normalization_stats,
        })
    except Exception as e:
        logger.error(f"Error getting activity metrics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/anomalies')
def get_analytics_anomalies():
    """Detect anomalies in loaded data."""
    try:
        node_type = request.args.get('node_type')
        method = request.args.get('method', 'percentile')
        threshold = float(request.args.get('threshold', '2.0'))
        
        if method not in ['zscore', 'percentile', 'threshold']:
            method = 'percentile'
        
        # Check minimum node count
        if node_type:
            node_count = sum(1 for nid in analytics_engine.graph.nodes() 
                           if analytics_engine.graph.nodes[nid].get('type') == node_type)
        else:
            node_count = len(analytics_engine.graph.nodes())
        
        if node_count < 10:
            return jsonify({
                'error': 'INSUFFICIENT_DATA',
                'message': 'Anomaly detection requires at least 10 nodes',
                'details': {'node_count': node_count}
            }), 400
        
        anomalies = analytics_engine.get_anomalies(node_type=node_type, method=method, threshold=threshold)
        
        # Get statistics for response
        statistics = {}
        if node_type == 'block' or not node_type:
            stats = analytics_engine.calculate_statistics('block', 'transaction_count')
            statistics['block'] = stats
        if node_type == 'transaction' or not node_type:
            stats = analytics_engine.calculate_statistics('transaction', 'value')
            statistics['transaction'] = stats
        
        return jsonify({
            'anomalies': anomalies,
            'method': method,
            'statistics': statistics,
            'total_nodes_analyzed': node_count,
        })
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/clusters')
def get_analytics_clusters():
    """Perform clustering analysis."""
    try:
        cluster_type = request.args.get('cluster_type')
        time_window_blocks = int(request.args.get('time_window_blocks', '30'))
        
        if not cluster_type:
            return jsonify({
                'error': 'MISSING_PARAMETER',
                'message': 'cluster_type parameter is required'
            }), 400
        
        if cluster_type not in ['address', 'transaction']:
            return jsonify({
                'error': 'INVALID_PARAMETER',
                'message': 'cluster_type must be "address" or "transaction"'
            }), 400
        
        if time_window_blocks < 20 or time_window_blocks > 50:
            return jsonify({
                'error': 'INVALID_PARAMETER',
                'message': 'time_window_blocks must be between 20 and 50'
            }), 400
        
        result = analytics_engine.get_clusters(cluster_type, time_window_blocks)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting clusters: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/flow')
def get_analytics_flow():
    """Get transaction flow paths."""
    try:
        start_address = request.args.get('start_address')
        transaction_id = request.args.get('transaction_id')
        max_depth = int(request.args.get('max_depth', '5'))
        max_blocks = int(request.args.get('max_blocks', '5'))
        
        if max_depth < 1 or max_depth > 10:
            max_depth = 5
        if max_blocks < 1 or max_blocks > 10:
            max_blocks = 5
        
        # Check if nodes exist
        if start_address and not analytics_engine.graph.has_node(start_address):
            return jsonify({
                'error': 'NODE_NOT_FOUND',
                'message': f'Start address {start_address} not found'
            }), 404
        
        if transaction_id and not analytics_engine.graph.has_node(transaction_id):
            return jsonify({
                'error': 'NODE_NOT_FOUND',
                'message': f'Transaction {transaction_id} not found'
            }), 404
        
        paths = analytics_engine.get_flow_paths(
            start_address=start_address,
            transaction_id=transaction_id,
            max_depth=max_depth,
            max_blocks=max_blocks
        )
        
        return jsonify({
            'paths': paths,
            'total_paths': len(paths),
            'max_depth': max_depth,
            'blocks_analyzed': max_blocks,
        })
    except Exception as e:
        logger.error(f"Error getting flow paths: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/recalculate', methods=['POST'])
def recalculate_analytics():
    """Recalculate all analytics metrics."""
    try:
        # Mark all metrics as dirty to force recalculation
        for key in analytics_engine._dirty_flags:
            analytics_engine._dirty_flags[key] = True
        
        # Clear caches
        analytics_engine._degree_cache.clear()
        analytics_engine._activity_cache.clear()
        analytics_engine._anomaly_cache.clear()
        analytics_engine._cluster_cache.clear()
        
        return jsonify({
            'status': 'recalculating',
            'message': 'Analytics recalculation started'
        }), 202
    except Exception as e:
        logger.error(f"Error recalculating analytics: {e}")
        return jsonify({'error': str(e)}), 500


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

