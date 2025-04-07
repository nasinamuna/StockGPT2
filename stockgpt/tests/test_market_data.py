import pytest
from datetime import datetime, timedelta
from src.data_collection.market_data import MarketData
from src.data_collection.data_collector import DataCollector

@pytest.fixture
def market_data():
    return MarketData()

@pytest.fixture
def mock_data():
    return {
        'AAPL': {
            'price': 150.0,
            'volume': 1000000,
            'timestamp': datetime.now().isoformat()
        }
    }

def test_get_stock_data(market_data, mock_data):
    # Test successful data retrieval
    data = market_data.get_stock_data('AAPL')
    assert isinstance(data, dict)
    assert 'price' in data
    assert 'volume' in data
    assert 'timestamp' in data

def test_get_stock_data_invalid_symbol(market_data):
    # Test invalid symbol handling
    with pytest.raises(ValueError):
        market_data.get_stock_data('INVALID')

def test_get_stock_data_caching(market_data, mock_data):
    # Test caching functionality
    # First call should fetch from API
    data1 = market_data.get_stock_data('AAPL')
    # Second call should use cache
    data2 = market_data.get_stock_data('AAPL')
    assert data1 == data2

def test_get_stock_data_cache_expiry(market_data, mock_data):
    # Test cache expiry
    # Set cache TTL to 1 second
    market_data.cache_ttl = 1
    # First call
    data1 = market_data.get_stock_data('AAPL')
    # Wait for cache to expire
    import time
    time.sleep(2)
    # Second call should fetch fresh data
    data2 = market_data.get_stock_data('AAPL')
    assert data1 != data2

def test_get_stock_data_error_handling(market_data):
    # Test error handling
    with pytest.raises(Exception):
        market_data.get_stock_data('ERROR') 