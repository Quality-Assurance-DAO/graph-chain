"""Unit tests for analytics engine."""

import pytest
from datetime import datetime
from src.analytics_engine import AnalyticsEngine
from src.graph_builder import GraphBuilder
from src.models import Block, Transaction, TransactionInput, TransactionOutput, Address


@pytest.fixture
def graph_builder():
    """Create a GraphBuilder instance for testing."""
    return GraphBuilder()


@pytest.fixture
def analytics_engine(graph_builder):
    """Create an AnalyticsEngine instance for testing."""
    return AnalyticsEngine(graph_builder)


@pytest.fixture
def sample_block():
    """Create a sample block for testing."""
    return Block(
        block_hash="abc123",
        block_height=100,
        timestamp=datetime.now(),
        tx_count=5
    )


@pytest.fixture
def sample_transaction():
    """Create a sample transaction for testing."""
    return Transaction(
        tx_hash="tx123",
        block_hash="abc123",
        block_height=100,
        inputs=[TransactionInput(tx_hash="prev_tx", index=0, address="addr1")],
        outputs=[TransactionOutput(address="addr2", amount=1000000)],
        fee=1000,
        timestamp=datetime.now()
    )


def test_analytics_engine_initialization(analytics_engine, graph_builder):
    """Test AnalyticsEngine initialization."""
    assert analytics_engine.graph_builder == graph_builder
    assert analytics_engine.graph == graph_builder.graph
    assert analytics_engine._dirty_flags['degree'] is True


def test_calculate_node_degrees_empty_graph(analytics_engine):
    """Test degree calculation on empty graph."""
    degrees = analytics_engine.calculate_node_degrees()
    assert degrees == {}


def test_calculate_node_degrees_with_nodes(analytics_engine, sample_block, sample_transaction):
    """Test degree calculation with nodes."""
    analytics_engine.graph_builder.add_block(sample_block)
    analytics_engine.graph_builder.add_transaction(sample_transaction)
    
    degrees = analytics_engine.calculate_node_degrees()
    
    assert len(degrees) > 0
    block_id = f"block_{sample_block.block_hash}"
    assert block_id in degrees
    assert 'in_degree' in degrees[block_id]
    assert 'out_degree' in degrees[block_id]
    assert 'total_degree' in degrees[block_id]


def test_calculate_type_specific_degree_block(analytics_engine, sample_block, sample_transaction):
    """Test type-specific degree for block."""
    analytics_engine.graph_builder.add_block(sample_block)
    analytics_engine.graph_builder.add_transaction(sample_transaction)
    
    block_id = f"block_{sample_block.block_hash}"
    type_degree = analytics_engine.calculate_type_specific_degree(block_id)
    
    # Block should have at least 1 transaction
    assert type_degree >= 1


def test_get_degree_metrics_filtering(analytics_engine, sample_block):
    """Test degree metrics filtering by node type."""
    analytics_engine.graph_builder.add_block(sample_block)
    
    block_metrics = analytics_engine.get_degree_metrics(node_type='block')
    assert len(block_metrics) > 0
    assert all(m['node_type'] == 'block' for m in block_metrics)


def test_calculate_activity_metrics(analytics_engine, sample_block, sample_transaction):
    """Test activity metrics calculation."""
    analytics_engine.graph_builder.add_block(sample_block)
    analytics_engine.graph_builder.add_transaction(sample_transaction)
    
    activity = analytics_engine.calculate_activity_metrics()
    assert len(activity) > 0


def test_normalize_activity_values(analytics_engine, sample_block):
    """Test activity value normalization."""
    analytics_engine.graph_builder.add_block(sample_block)
    
    activity = analytics_engine.calculate_activity_metrics()
    normalized = analytics_engine.normalize_activity_values(activity)
    
    assert len(normalized) > 0
    for node_id, metrics in normalized.items():
        assert 'normalized_value' in metrics
        assert 0 <= metrics['normalized_value'] <= 100


def test_apply_color_coding(analytics_engine, sample_block):
    """Test color coding application."""
    analytics_engine.graph_builder.add_block(sample_block)
    
    activity = analytics_engine.calculate_activity_metrics()
    normalized = analytics_engine.normalize_activity_values(activity)
    colored = analytics_engine.apply_color_coding(normalized, color_scheme='heatmap')
    
    assert len(colored) > 0
    for node_id, metrics in colored.items():
        assert 'color_hex' in metrics
        assert metrics['color_hex'].startswith('#')


def test_get_activity_metrics(analytics_engine, sample_block):
    """Test getting activity metrics."""
    analytics_engine.graph_builder.add_block(sample_block)
    
    metrics = analytics_engine.get_activity_metrics(node_type='block', color_scheme='heatmap')
    assert len(metrics) > 0
    assert all('color_hex' in m for m in metrics)


def test_calculate_statistics(analytics_engine, sample_block):
    """Test statistics calculation."""
    analytics_engine.graph_builder.add_block(sample_block)
    
    stats = analytics_engine.calculate_statistics('block', 'transaction_count')
    assert 'mean' in stats
    assert 'std' in stats
    assert 'percentile_5' in stats
    assert 'percentile_95' in stats


def test_detect_anomalies_insufficient_data(analytics_engine):
    """Test anomaly detection with insufficient data."""
    anomalies = analytics_engine.detect_anomalies(node_type='block', method='percentile')
    # Should return empty list if < 10 nodes
    assert isinstance(anomalies, list)


def test_get_recent_blocks(analytics_engine, sample_block):
    """Test getting recent blocks."""
    analytics_engine.graph_builder.add_block(sample_block)
    
    recent = analytics_engine.get_recent_blocks(time_window_blocks=10)
    assert isinstance(recent, set)


def test_cluster_addresses(analytics_engine):
    """Test address clustering."""
    clusters = analytics_engine.cluster_addresses(time_window_blocks=30)
    assert isinstance(clusters, dict)


def test_cluster_transactions(analytics_engine):
    """Test transaction clustering."""
    clusters = analytics_engine.cluster_transactions(time_window_blocks=30)
    assert isinstance(clusters, dict)


def test_get_clusters(analytics_engine):
    """Test getting clusters."""
    result = analytics_engine.get_clusters('address', time_window_blocks=30)
    assert 'clusters' in result
    assert 'cluster_type' in result
    assert result['cluster_type'] == 'address'


def test_get_flow_paths_empty(analytics_engine):
    """Test flow paths on empty graph."""
    paths = analytics_engine.get_flow_paths(max_depth=5, max_blocks=5)
    assert isinstance(paths, list)

