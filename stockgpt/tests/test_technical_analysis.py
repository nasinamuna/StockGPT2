import pytest
import numpy as np
from src.analysis.technical_analysis import TechnicalAnalysis
import pandas as pd

@pytest.fixture
def technical_analysis():
    return TechnicalAnalysis()

@pytest.fixture
def sample_data():
    # Create sample price data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    prices = np.random.normal(100, 10, 100).cumsum()  # Random walk
    volumes = np.random.randint(1000000, 2000000, 100)
    return pd.DataFrame({
        'Date': dates,
        'Close': prices,
        'Volume': volumes
    })

def test_calculate_sma(technical_analysis, sample_data):
    # Test SMA calculation
    sma = technical_analysis.calculate_sma(sample_data['Close'], window=20)
    assert len(sma) == len(sample_data)
    assert not sma.isna().all()  # Should have some valid values
    assert sma.iloc[19] == sample_data['Close'].iloc[:20].mean()  # First complete window

def test_calculate_rsi(technical_analysis, sample_data):
    # Test RSI calculation
    rsi = technical_analysis.calculate_rsi(sample_data['Close'], window=14)
    assert len(rsi) == len(sample_data)
    assert not rsi.isna().all()
    assert all(0 <= rsi <= 100 for rsi in rsi.dropna())  # RSI should be between 0 and 100

def test_calculate_macd(technical_analysis, sample_data):
    # Test MACD calculation
    macd, signal, hist = technical_analysis.calculate_macd(sample_data['Close'])
    assert len(macd) == len(sample_data)
    assert len(signal) == len(sample_data)
    assert len(hist) == len(sample_data)
    assert not macd.isna().all()
    assert not signal.isna().all()
    assert not hist.isna().all()

def test_calculate_bollinger_bands(technical_analysis, sample_data):
    # Test Bollinger Bands calculation
    upper, middle, lower = technical_analysis.calculate_bollinger_bands(sample_data['Close'])
    assert len(upper) == len(sample_data)
    assert len(middle) == len(sample_data)
    assert len(lower) == len(sample_data)
    assert not upper.isna().all()
    assert not middle.isna().all()
    assert not lower.isna().all()
    assert all(upper >= middle)  # Upper band should be above middle
    assert all(middle >= lower)  # Lower band should be below middle

def test_identify_patterns(technical_analysis, sample_data):
    # Test pattern identification
    patterns = technical_analysis.identify_patterns(sample_data)
    assert isinstance(patterns, dict)
    assert 'support_levels' in patterns
    assert 'resistance_levels' in patterns
    assert 'trend_lines' in patterns

def test_generate_signals(technical_analysis, sample_data):
    # Test signal generation
    signals = technical_analysis.generate_signals(sample_data)
    assert isinstance(signals, dict)
    assert 'buy_signals' in signals
    assert 'sell_signals' in signals
    assert 'hold_signals' in signals 