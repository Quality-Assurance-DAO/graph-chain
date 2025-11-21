"""Integration tests for end-to-end data flow."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.graph_builder import GraphBuilder
from src.data_fetcher import DataFetcher
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

