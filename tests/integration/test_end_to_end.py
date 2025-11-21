"""Integration tests for end-to-end data flow."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.graph_builder import GraphBuilder
from src.data_fetcher import DataFetcher
from src.analytics_engine import AnalyticsEngine
from src.models import Block, Transaction, TransactionInput, TransactionOutput


@pytest.fixture
def mock_api_client():
    """Create a mock BlockfrostClient."""
    client = Mock()
    return client


@pytest.fixture
def graph_builder():
    """Create a GraphBuilder instance."""
    return GraphBuilder()


@pytest.fixture
def data_fetcher(graph_builder, mock_api_client):
    """Create a DataFetcher instance with mocked API client."""
    with patch('src.data_fetcher.validate_config'):
        fetcher = DataFetcher(graph_builder, api_client=mock_api_client)
        return fetcher


def test_end_to_end_block_to_graph(graph_builder, data_fetcher, mock_api_client):
    """Test full flow from API fetch to graph update."""
    # Mock API responses
    mock_api_client.get_latest_block.return_value = {
        'hash': 'test_block_hash',
        'height': 12345,
        'time': '2025-01-27T12:00:00Z',
        'slot': 1000,
        'tx_count': 2
    }
    
    mock_api_client.get_block_transactions.return_value = [
        {
            'hash': 'tx1',
            'inputs': [
                {'tx_hash': 'prev_tx1', 'index': 0, 'address': 'addr_input1'}
            ],
            'outputs': [
                {'address': 'addr_output1', 'amount': 1000000}
            ],
            'fee': 170000
        },
        {
            'hash': 'tx2',
            'inputs': [
                {'tx_hash': 'prev_tx2', 'index': 0, 'address': 'addr_input2'}
            ],
            'outputs': [
                {'address': 'addr_output2', 'amount': 500000}
            ],
            'fee': 170000
        }
    ]
    
    # Execute fetch and update
    result = data_fetcher.fetch_and_update()
    
    assert result is True
    
    # Verify block was added
    block_id = 'block_test_block_hash'
    assert graph_builder.graph.has_node(block_id)
    
    # Verify transactions were added
    tx1_id = 'tx_tx1'
    tx2_id = 'tx_tx2'
    assert graph_builder.graph.has_node(tx1_id)
    assert graph_builder.graph.has_node(tx2_id)
    
    # Verify addresses were added
    assert graph_builder.graph.has_node('addr_addr_input1')
    assert graph_builder.graph.has_node('addr_addr_output1')
    assert graph_builder.graph.has_node('addr_addr_input2')
    assert graph_builder.graph.has_node('addr_addr_output2')
    
    # Verify edges were created
    assert graph_builder.graph.has_edge(block_id, tx1_id)
    assert graph_builder.graph.has_edge(block_id, tx2_id)
    assert graph_builder.graph.has_edge('addr_addr_input1', tx1_id)
    assert graph_builder.graph.has_edge(tx1_id, 'addr_addr_output1')


def test_end_to_end_graph_to_json(graph_builder, data_fetcher, mock_api_client):
    """Test graph serialization to JSON format."""
    # Add test data
    block = Block(
        block_hash='test_block',
        block_height=12345,
        timestamp=datetime.now()
    )
    graph_builder.add_block(block)
    
    transaction = Transaction(
        tx_hash='test_tx',
        block_hash='test_block',
        block_height=12345,
        inputs=[TransactionInput(tx_hash='prev', index=0, address='addr1')],
        outputs=[TransactionOutput(address='addr2', amount=1000000)],
    )
    graph_builder.add_transaction(transaction)
    
    # Convert to JSON
    json_data = graph_builder.to_json()
    
    # Verify structure
    assert 'nodes' in json_data
    assert 'edges' in json_data
    assert 'metadata' in json_data
    
    # Verify nodes
    node_ids = [node['id'] for node in json_data['nodes']]
    assert 'block_test_block' in node_ids
    assert 'tx_test_tx' in node_ids
    
    # Verify edges
    edge_pairs = [(edge['from'], edge['to']) for edge in json_data['edges']]
    assert ('block_test_block', 'tx_test_tx') in edge_pairs


def test_end_to_end_error_handling(graph_builder, data_fetcher, mock_api_client):
    """Test error handling in end-to-end flow."""
    # Mock API error
    mock_api_client.get_latest_block.side_effect = Exception("API Error")
    
    # Should not crash
    result = data_fetcher.fetch_and_update()
    
    assert result is False
    assert data_fetcher.error_state is not None
    assert data_fetcher.api_status == 'disconnected'
    
    # Graph should still be accessible (graceful degradation)
    json_data = graph_builder.to_json()
    assert json_data is not None


@pytest.fixture
def analytics_engine(graph_builder):
    """Create an AnalyticsEngine instance."""
    return AnalyticsEngine(graph_builder)


@pytest.fixture
def sample_graph_data(graph_builder):
    """Create sample graph data for analytics testing."""
    # Add multiple blocks and transactions for meaningful analytics
    for i in range(15):  # Add 15 blocks to meet minimum for anomaly detection
        block = Block(
            block_hash=f'block_{i}',
            block_height=1000 + i,
            timestamp=datetime.now(),
            tx_count=i + 1  # Varying transaction counts
        )
        graph_builder.add_block(block)
        
        # Add transactions to each block
        for j in range(i + 1):
            tx = Transaction(
                tx_hash=f'tx_{i}_{j}',
                block_hash=f'block_{i}',
                block_height=1000 + i,
                inputs=[TransactionInput(tx_hash=f'prev_{i}_{j}', index=0, address=f'addr_input_{i}_{j}')],
                outputs=[TransactionOutput(address=f'addr_output_{i}_{j}', amount=(j + 1) * 1000000)],
                fee=170000,
                timestamp=datetime.now()
            )
            graph_builder.add_transaction(tx)
    
    return graph_builder


def test_integration_analytics_degrees_endpoint(sample_graph_data, analytics_engine):
    """Test GET /api/analytics/degrees endpoint integration."""
    # Get degree metrics
    metrics = analytics_engine.get_degree_metrics()
    
    assert len(metrics) > 0
    assert all('node_id' in m for m in metrics)
    assert all('node_type' in m for m in metrics)
    assert all('in_degree' in m for m in metrics)
    assert all('out_degree' in m for m in metrics)
    assert all('total_degree' in m for m in metrics)
    assert all('type_degree' in m for m in metrics)
    
    # Test filtering by node type
    block_metrics = analytics_engine.get_degree_metrics(node_type='block')
    assert all(m['node_type'] == 'block' for m in block_metrics)
    
    # Test filtering by node_id
    if metrics:
        node_id = metrics[0]['node_id']
        specific_metrics = analytics_engine.get_degree_metrics(node_id=node_id)
        assert len(specific_metrics) == 1
        assert specific_metrics[0]['node_id'] == node_id


def test_integration_analytics_degrees_endpoint_http(sample_graph_data):
    """Test GET /api/analytics/degrees HTTP endpoint."""
    from src.web_server import app
    
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Test basic endpoint
        response = client.get('/api/analytics/degrees')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'metrics' in data
        assert 'statistics' in data
        
        metrics = data['metrics']
        assert len(metrics) > 0
        assert all('node_id' in m for m in metrics)
        assert all('node_type' in m for m in metrics)
        assert all('in_degree' in m for m in metrics)
        assert all('out_degree' in m for m in metrics)
        assert all('total_degree' in m for m in metrics)
        assert all('type_degree' in m for m in metrics)
        
        # Test filtering by node_type
        response = client.get('/api/analytics/degrees?node_type=block')
        assert response.status_code == 200
        data = response.get_json()
        assert all(m['node_type'] == 'block' for m in data['metrics'])
        
        # Test filtering by node_id
        if metrics:
            node_id = metrics[0]['node_id']
            response = client.get(f'/api/analytics/degrees?node_id={node_id}')
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['metrics']) == 1
            assert data['metrics'][0]['node_id'] == node_id


def test_integration_analytics_activity_endpoint(sample_graph_data, analytics_engine):
    """Test GET /api/analytics/activity endpoint integration."""
    # Get activity metrics with different color schemes
    for color_scheme in ['heatmap', 'activity', 'grayscale']:
        metrics = analytics_engine.get_activity_metrics(color_scheme=color_scheme)
        
        assert len(metrics) > 0
        assert all('node_id' in m for m in metrics)
        assert all('node_type' in m for m in metrics)
        assert all('raw_value' in m for m in metrics)
        assert all('normalized_value' in m for m in metrics)
        assert all('color_hex' in m for m in metrics)
        
        # Verify normalized values are in range
        assert all(0 <= m['normalized_value'] <= 100 for m in metrics)
        
        # Verify color hex format
        assert all(m['color_hex'].startswith('#') and len(m['color_hex']) == 7 for m in metrics)
    
    # Test filtering by node type
    block_metrics = analytics_engine.get_activity_metrics(node_type='block', color_scheme='heatmap')
    assert all(m['node_type'] == 'block' for m in block_metrics)


def test_integration_analytics_anomalies_endpoint(sample_graph_data, analytics_engine):
    """Test GET /api/analytics/anomalies endpoint integration."""
    # Test with sufficient data (15 blocks should be enough)
    anomalies = analytics_engine.get_anomalies(method='percentile')
    
    assert isinstance(anomalies, list)
    # May or may not have anomalies depending on data distribution
    
    # Test different methods
    for method in ['zscore', 'percentile', 'threshold']:
        anomalies = analytics_engine.get_anomalies(method=method, threshold=2.0)
        assert isinstance(anomalies, list)
        
        if anomalies:
            assert all('node_id' in a for a in anomalies)
            assert all('node_type' in a for a in anomalies)
            assert all('is_anomaly' in a for a in anomalies)
            assert all('anomaly_score' in a for a in anomalies)
            assert all('anomaly_type' in a for a in anomalies)
    
    # Test filtering by node type
    block_anomalies = analytics_engine.get_anomalies(node_type='block', method='percentile')
    assert all(a['node_type'] == 'block' for a in block_anomalies)


def test_integration_analytics_clusters_endpoint(sample_graph_data, analytics_engine):
    """Test GET /api/analytics/clusters endpoint integration."""
    # Test address clustering
    address_clusters = analytics_engine.get_clusters('address', time_window_blocks=30)
    
    assert 'clusters' in address_clusters
    assert 'cluster_type' in address_clusters
    assert address_clusters['cluster_type'] == 'address'
    assert 'time_window_blocks' in address_clusters
    assert 'total_clusters' in address_clusters
    assert 'nodes_clustered' in address_clusters
    
    # Test transaction clustering
    transaction_clusters = analytics_engine.get_clusters('transaction', time_window_blocks=30)
    
    assert 'clusters' in transaction_clusters
    assert transaction_clusters['cluster_type'] == 'transaction'
    
    # Verify cluster structure
    if address_clusters['clusters']:
        cluster = address_clusters['clusters'][0]
        assert 'cluster_id' in cluster
        assert 'node_ids' in cluster
        assert 'size' in cluster
        assert 'color_hex' in cluster


def test_integration_analytics_flow_endpoint(sample_graph_data, analytics_engine):
    """Test GET /api/analytics/flow endpoint integration."""
    # Get all flow paths
    paths = analytics_engine.get_flow_paths(max_depth=5, max_blocks=5)
    
    assert isinstance(paths, list)
    
    if paths:
        for path in paths:
            assert 'path_id' in path
            assert 'path_nodes' in path
            assert 'path_edges' in path
            assert 'total_value' in path
            assert 'path_length' in path
            assert 'is_complete' in path
    
    # Test with specific start address
    if sample_graph_data.graph.nodes():
        address_nodes = [nid for nid in sample_graph_data.graph.nodes() 
                         if sample_graph_data.graph.nodes[nid].get('type') == 'address']
        if address_nodes:
            start_address = address_nodes[0]
            paths = analytics_engine.get_flow_paths(start_address=start_address, max_depth=3, max_blocks=3)
            assert isinstance(paths, list)
    
    # Test with specific transaction
    transaction_nodes = [nid for nid in sample_graph_data.graph.nodes() 
                        if sample_graph_data.graph.nodes[nid].get('type') == 'transaction']
    if transaction_nodes:
        transaction_id = transaction_nodes[0]
        paths = analytics_engine.get_flow_paths(transaction_id=transaction_id, max_depth=3, max_blocks=3)
        assert isinstance(paths, list)


def test_integration_analytics_recalculate_endpoint(sample_graph_data, analytics_engine):
    """Test POST /api/analytics/recalculate endpoint integration."""
    # Calculate some metrics first
    metrics_before = analytics_engine.get_degree_metrics()
    
    # Mark as dirty and clear cache
    for key in analytics_engine._dirty_flags:
        analytics_engine._dirty_flags[key] = True
    analytics_engine._degree_cache.clear()
    
    # Recalculate should work
    metrics_after = analytics_engine.get_degree_metrics()
    
    # Should still return valid metrics
    assert len(metrics_after) > 0
    assert all('node_id' in m for m in metrics_after)


def test_integration_analytics_insufficient_data_anomalies(analytics_engine):
    """Test anomaly detection with insufficient data."""
    # Create graph with less than 10 nodes
    for i in range(5):
        block = Block(
            block_hash=f'block_{i}',
            block_height=1000 + i,
            timestamp=datetime.now(),
            tx_count=1
        )
        analytics_engine.graph_builder.add_block(block)
    
    # Should return empty list or handle gracefully
    anomalies = analytics_engine.get_anomalies(method='percentile')
    # With < 10 nodes, should return empty list
    assert isinstance(anomalies, list)

