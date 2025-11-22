"""Unit tests for GraphBuilder."""

import pytest
from datetime import datetime
from src.graph_builder import GraphBuilder
from src.models import Block, Transaction, TransactionInput, TransactionOutput, Address


@pytest.fixture
def graph_builder():
    """Create a GraphBuilder instance."""
    return GraphBuilder()


@pytest.fixture
def sample_block():
    """Create a sample Block instance."""
    return Block(
        block_hash='test_block_hash',
        block_height=12345,
        timestamp=datetime.now(),
        slot=1000,
        tx_count=5
    )


@pytest.fixture
def sample_transaction():
    """Create a sample Transaction instance."""
    return Transaction(
        tx_hash='test_tx_hash',
        block_hash='test_block_hash',
        block_height=12345,
        inputs=[
            TransactionInput(tx_hash='prev_tx1', index=0, address='addr1'),
            TransactionInput(tx_hash='prev_tx2', index=1, address='addr2'),
        ],
        outputs=[
            TransactionOutput(address='addr3', amount=1000000),
            TransactionOutput(address='addr4', amount=500000),
        ],
        fee=170000,
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_address():
    """Create a sample Address instance."""
    return Address(
        address='addr_test123',
        first_seen=datetime.now(),
        total_received=1000000,
        total_sent=500000,
        transaction_count=2
    )


def test_add_block(graph_builder, sample_block):
    """Test adding a block to the graph."""
    graph_builder.add_block(sample_block)
    
    node_id = f"block_{sample_block.block_hash}"
    assert graph_builder.graph.has_node(node_id)
    
    node_data = graph_builder.graph.nodes[node_id]
    assert node_data['type'] == 'block'
    assert node_data['data']['block_height'] == 12345


def test_add_transaction(graph_builder, sample_block, sample_transaction):
    """Test adding a transaction to the graph."""
    # Add block first
    graph_builder.add_block(sample_block)
    
    # Add transaction
    graph_builder.add_transaction(sample_transaction)
    
    tx_id = f"tx_{sample_transaction.tx_hash}"
    assert graph_builder.graph.has_node(tx_id)
    
    # Check block-transaction edge
    block_id = f"block_{sample_block.block_hash}"
    assert graph_builder.graph.has_edge(block_id, tx_id)


def test_add_address(graph_builder, sample_address):
    """Test adding an address to the graph."""
    graph_builder.add_address(sample_address)
    
    addr_id = f"addr_{sample_address.address}"
    assert graph_builder.graph.has_node(addr_id)
    
    node_data = graph_builder.graph.nodes[addr_id]
    assert node_data['type'] == 'address'


def test_address_aggregation(graph_builder):
    """Test address statistics aggregation."""
    addr1 = Address(address='addr_test', first_seen=datetime.now(), total_received=1000000, transaction_count=1)
    addr2 = Address(address='addr_test', first_seen=datetime.now(), total_received=500000, transaction_count=1)
    
    graph_builder.add_address(addr1)
    graph_builder.add_address(addr2)
    
    addr_id = f"addr_{addr1.address}"
    node_data = graph_builder.graph.nodes[addr_id]['data']
    
    # Should aggregate statistics
    assert node_data['total_received'] == 1500000
    assert node_data['transaction_count'] == 2


def test_get_neighbors(graph_builder, sample_block, sample_transaction):
    """Test getting neighbor nodes."""
    graph_builder.add_block(sample_block)
    graph_builder.add_transaction(sample_transaction)
    
    tx_id = f"tx_{sample_transaction.tx_hash}"
    neighbors = graph_builder.get_neighbors(tx_id)
    
    # Should have block as neighbor
    block_id = f"block_{sample_block.block_hash}"
    assert block_id in neighbors


def test_to_json(graph_builder, sample_block):
    """Test converting graph to JSON format."""
    graph_builder.add_block(sample_block)
    
    json_data = graph_builder.to_json()
    
    assert 'nodes' in json_data
    assert 'edges' in json_data
    assert 'metadata' in json_data
    assert json_data['metadata']['node_count'] == 1


def test_to_pyvis(graph_builder, sample_block):
    """Test converting graph to PyVis format."""
    graph_builder.add_block(sample_block)
    
    pyvis_data = graph_builder.to_pyvis()
    
    assert 'nodes' in pyvis_data
    assert 'edges' in pyvis_data
    assert len(pyvis_data['nodes']) == 1


