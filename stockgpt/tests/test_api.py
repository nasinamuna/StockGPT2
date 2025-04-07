import pytest
from fastapi.testclient import TestClient
from src.api.app import app
from src.data_collection.market_data import MarketData
from src.analysis.technical_analysis import TechnicalAnalysis
from src.analysis.fundamental_analysis import FundamentalAnalysis
from src.analysis.sentiment_analysis import SentimentAnalysis
from src.prediction.price_prediction import PricePrediction

client = TestClient(app)

@pytest.fixture
def mock_market_data(monkeypatch):
    def mock_get_stock_data(symbol):
        return {
            'price': 150.0,
            'volume': 1000000,
            'timestamp': '2023-01-01T00:00:00'
        }
    monkeypatch.setattr(MarketData, 'get_stock_data', mock_get_stock_data)

@pytest.fixture
def mock_technical_analysis(monkeypatch):
    def mock_analyze(symbol):
        return {
            'indicators': {
                'sma': [150.0, 151.0, 152.0],
                'rsi': 65.0,
                'macd': 1.5
            },
            'signals': {
                'buy': True,
                'sell': False
            }
        }
    monkeypatch.setattr(TechnicalAnalysis, 'analyze', mock_analyze)

@pytest.fixture
def mock_fundamental_analysis(monkeypatch):
    def mock_analyze(symbol):
        return {
            'metrics': {
                'pe_ratio': 25.0,
                'pb_ratio': 3.0,
                'dividend_yield': 0.02
            },
            'valuation': 'fair'
        }
    monkeypatch.setattr(FundamentalAnalysis, 'analyze', mock_analyze)

@pytest.fixture
def mock_sentiment_analysis(monkeypatch):
    def mock_analyze(symbol):
        return {
            'sentiment': {
                'news': 0.7,
                'social': 0.6
            },
            'overall': 'bullish'
        }
    monkeypatch.setattr(SentimentAnalysis, 'analyze', mock_analyze)

@pytest.fixture
def mock_price_prediction(monkeypatch):
    def mock_predict(symbol):
        return {
            'prediction': [155.0, 156.0, 157.0],
            'confidence': 0.85
        }
    monkeypatch.setattr(PricePrediction, 'predict', mock_predict)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to StockGPT API"}

def test_get_stocks(mock_market_data):
    response = client.get("/stocks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_stock_data(mock_market_data):
    response = client.get("/stocks/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert 'price' in data
    assert 'volume' in data
    assert 'timestamp' in data

def test_analyze_stock_technical(mock_technical_analysis):
    response = client.post("/api/stock", json={
        "symbol": "AAPL",
        "analysis_type": "technical"
    })
    assert response.status_code == 200
    data = response.json()
    assert 'indicators' in data
    assert 'signals' in data

def test_analyze_stock_fundamental(mock_fundamental_analysis):
    response = client.post("/api/stock", json={
        "symbol": "AAPL",
        "analysis_type": "fundamental"
    })
    assert response.status_code == 200
    data = response.json()
    assert 'metrics' in data
    assert 'valuation' in data

def test_analyze_stock_sentiment(mock_sentiment_analysis):
    response = client.post("/api/stock", json={
        "symbol": "AAPL",
        "analysis_type": "sentiment"
    })
    assert response.status_code == 200
    data = response.json()
    assert 'sentiment' in data
    assert 'overall' in data

def test_get_stock_prediction(mock_price_prediction):
    response = client.post("/api/stock/prediction", json={
        "symbol": "AAPL"
    })
    assert response.status_code == 200
    data = response.json()
    assert 'prediction' in data
    assert 'confidence' in data

def test_rate_limiting():
    # Test rate limiting by making multiple requests
    for _ in range(5):
        response = client.get("/")
        assert response.status_code == 200
    
    # Next request should be rate limited
    response = client.get("/")
    assert response.status_code == 429

def test_invalid_symbol():
    response = client.get("/stocks/INVALID")
    assert response.status_code == 404

def test_invalid_analysis_type():
    response = client.post("/api/stock", json={
        "symbol": "AAPL",
        "analysis_type": "invalid"
    })
    assert response.status_code == 400 