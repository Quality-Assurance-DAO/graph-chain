"""Unit tests for DataFetcher."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.data_fetcher import DataFetcher
from src.graph_builder import GraphBuilder
from src.models import Block, Transaction, TransactionInput, TransactionOutput, Address
from blockfrost import ApiError


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


def test_parse_block(data_fetcher):
    """Test parsing block data from API response."""
    block_data = {
        'hash': 'test_block_hash',
        'height': 12345,
        'time': '2025-01-27T12:00:00Z',
        'slot': 1000,
        'tx_count': 5
    }
    
    block = data_fetcher.parse_block(block_data)
    
    assert isinstance(block, Block)
    assert block.block_hash == 'test_block_hash'
    assert block.block_height == 12345
    assert block.slot == 1000
    assert block.tx_count == 5


def test_parse_transaction(data_fetcher):
    """Test parsing transaction data from API response."""
    tx_data = {
        'hash': 'test_tx_hash',
        'inputs': [
            {'tx_hash': 'prev_tx1', 'index': 0, 'address': 'addr1'},
            {'tx_hash': 'prev_tx2', 'index': 1, 'address': 'addr2'},
        ],
        'outputs': [
            {'address': 'addr3', 'amount': 1000000},
            {'address': 'addr4', 'amount': 500000},
        ],
        'fee': 170000
    }
    
    transaction = data_fetcher.parse_transaction(tx_data, 'block_hash', 12345)
    
    assert isinstance(transaction, Transaction)
    assert transaction.tx_hash == 'test_tx_hash'
    assert len(transaction.inputs) == 2
    assert len(transaction.outputs) == 2
    assert transaction.fee == 170000


def test_fetch_and_update_success(data_fetcher, mock_api_client):
    """Test successful fetch and update."""
    # Mock API responses
    mock_api_client.get_latest_block.return_value = {
        'hash': 'test_block_hash',
        'height': 12345,
        'time': '2025-01-27T12:00:00Z',
    }
    mock_api_client.get_block_transactions.return_value = [
        {
            'hash': 'test_tx_hash',
            'inputs': [{'tx_hash': 'prev_tx', 'index': 0, 'address': 'addr1'}],
            'outputs': [{'address': 'addr2', 'amount': 1000000}],
        }
    ]
    
    result = data_fetcher.fetch_and_update()
    
    assert result is True
    assert data_fetcher.last_block_height == 12345


def test_fetch_and_update_rate_limit(data_fetcher, mock_api_client):
    """Test handling of rate limit errors."""
    # Mock rate limit error
    rate_limit_error = ApiError()
    rate_limit_error.status_code = 429
    mock_api_client.get_latest_block.side_effect = rate_limit_error
    
    result = data_fetcher.fetch_and_update()
    
    assert result is False
    assert data_fetcher.api_status == 'rate_limited'
    assert data_fetcher.rate_limit_status['limited'] is True


def test_fetch_and_update_api_error(data_fetcher, mock_api_client):
    """Test handling of API errors."""
    # Mock API error
    api_error = ApiError()
    api_error.status_code = 500
    mock_api_client.get_latest_block.side_effect = api_error
    
    result = data_fetcher.fetch_and_update()
    
    assert result is False
    assert data_fetcher.api_status == 'disconnected'
    assert data_fetcher.error_state is not None


def test_fetch_and_update_skip_duplicate_block(data_fetcher, mock_api_client):
    """Test skipping already processed blocks."""
    data_fetcher.last_block_height = 12345
    
    mock_api_client.get_latest_block.return_value = {
        'hash': 'test_block_hash',
        'height': 12345,  # Same height
        'time': '2025-01-27T12:00:00Z',
    }
    
    result = data_fetcher.fetch_and_update()
    
    # Should return True (not an error, just no new data)
    assert result is True

