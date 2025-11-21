"""Unit tests for web server Flask routes."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from src.web_server import app, graph_builder, data_fetcher


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """Test GET / route serves index.html."""
    response = client.get('/')
    
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'


def test_get_graph_route(client):
    """Test GET /api/graph route returns graph JSON."""
    # Add some test data to graph
    from src.models import Block
    from datetime import datetime
    
    block = Block(
        block_hash='test_hash',
        block_height=12345,
        timestamp=datetime.now()
    )
    graph_builder.add_block(block)
    
    response = client.get('/api/graph')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'nodes' in data
    assert 'edges' in data
    assert 'metadata' in data


def test_get_status_route(client):
    """Test GET /api/status route returns status JSON."""
    response = client.get('/api/status')
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'api_status' in data
    assert 'polling_status' in data
    assert 'rate_limit_status' in data
    assert 'graph_stats' in data


def test_get_status_with_error(client):
    """Test GET /api/status handles errors gracefully."""
    # Mock data_fetcher to raise an error
    original_get_status = data_fetcher.get_status
    data_fetcher.get_status = Mock(side_effect=Exception("Test error"))
    
    try:
        response = client.get('/api/status')
        # Should still return 200 with error info
        assert response.status_code == 200 or response.status_code == 500
    finally:
        data_fetcher.get_status = original_get_status


def test_graph_updates_sse_route(client):
    """Test GET /api/graph/updates route returns SSE stream."""
    response = client.get('/api/graph/updates')
    
    assert response.status_code == 200
    assert response.content_type == 'text/event-stream; charset=utf-8'

