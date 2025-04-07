import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
from typing import Dict, List, Any, Optional
import os

logger = logging.getLogger(__name__)

class MarketData:
    def __init__(self, cache_dir: str = "data/processed/market_data"):
        """
        Initialize the MarketData class.
        
        Args:
            cache_dir (str): Directory to store cached data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)  # Cache TTL of 1 hour
        
    def get_data(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch stock data from Yahoo Finance with caching.
        
        Args:
            symbol (str): Stock symbol
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
            
        Returns:
            dict: Stock data including price history and basic info
        """
        try:
            # Set default dates if not provided
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            if not start_date:
                # Default to 1 year of data
                start = datetime.now() - timedelta(days=365)
                start_date = start.strftime('%Y-%m-%d')
            
            # Check cache first
            cache_key = f"{symbol}_{start_date}_{end_date}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Fetch data from Yahoo Finance
            ticker = yf.Ticker(symbol)
            
            # Validate symbol exists
            if not ticker.info:
                raise ValueError(f"Invalid symbol: {symbol}")
            
            # Get historical data
            history = ticker.history(start=start_date, end=end_date)
            
            # Validate data
            if history.empty:
                raise ValueError(f"No data available for {symbol} in the specified date range")
            
            # Calculate additional metrics
            history['Daily_Return'] = history['Close'].pct_change()
            history['20d_MA'] = history['Close'].rolling(window=20).mean()
            history['50d_MA'] = history['Close'].rolling(window=50).mean()
            
            # Convert to dict format
            price_data = history.reset_index().to_dict(orient='records')
            
            # Get basic info
            info = ticker.info
            
            # Validate required info fields
            required_fields = ['longName', 'sector', 'industry', 'marketCap']
            missing_fields = [field for field in required_fields if field not in info]
            if missing_fields:
                logger.warning(f"Missing required fields for {symbol}: {missing_fields}")
            
            result = {
                'symbol': symbol,
                'price_history': price_data,
                'info': {
                    'name': info.get('longName', 'Unknown'),
                    'sector': info.get('sector', 'Unknown'),
                    'industry': info.get('industry', 'Unknown'),
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('trailingPE', 0),
                    'dividend_yield': info.get('dividendYield', 0),
                    'beta': info.get('beta', 0),
                    'current_price': info.get('currentPrice', 0)
                },
                'metrics': {
                    'avg_volume': history['Volume'].mean(),
                    'volatility': history['Daily_Return'].std() * (252 ** 0.5),  # Annualized volatility
                    'avg_daily_return': history['Daily_Return'].mean(),
                    'sharpe_ratio': self._calculate_sharpe_ratio(history['Daily_Return'])
                }
            }
            
            # Cache the result
            self._save_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            # Return mock data for development
            return self._get_mock_data(symbol)
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if it exists and is not expired."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is expired
                cache_time = datetime.fromisoformat(cached_data['cache_time'])
                if datetime.now() - cache_time < self.cache_ttl:
                    return cached_data['data']
                
                # Cache expired, delete the file
                cache_file.unlink()
                
            except Exception as e:
                logger.error(f"Error reading cache for {cache_key}: {str(e)}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Save data to cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cache_data = {
                'cache_time': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
                
        except Exception as e:
            logger.error(f"Error saving cache for {cache_key}: {str(e)}")
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio for the given returns."""
        if len(returns) < 2:
            return 0.0
            
        excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
        return (excess_returns.mean() / excess_returns.std()) * (252 ** 0.5)
    
    def _get_mock_data(self, symbol: str) -> Dict[str, Any]:
        """Generate mock data for development."""
        end_date = datetime.now()
        dates = [(end_date - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(365, 0, -1)]
        
        import random
        base_price = random.uniform(100, 1000)
        price_history = []
        
        for i, date in enumerate(dates):
            daily_change = random.uniform(-0.03, 0.03)
            price = base_price * (1 + daily_change)
            base_price = price
            
            volume = random.randint(100000, 10000000)
            
            price_history.append({
                'Date': date,
                'Open': price * 0.99,
                'High': price * 1.02,
                'Low': price * 0.98,
                'Close': price,
                'Volume': volume,
                'Daily_Return': daily_change,
                '20d_MA': price * random.uniform(0.98, 1.02),
                '50d_MA': price * random.uniform(0.97, 1.03)
            })
        
        return {
            'symbol': symbol,
            'price_history': price_history,
            'info': {
                'name': f"{symbol} Corporation",
                'sector': "Technology",
                'industry': "Software",
                'market_cap': 10000000000,
                'pe_ratio': 20.5,
                'dividend_yield': 0.02,
                'beta': 1.2,
                'current_price': price_history[-1]['Close']
            },
            'metrics': {
                'avg_volume': sum(p['Volume'] for p in price_history) / len(price_history),
                'volatility': 0.25,  # Mock volatility
                'avg_daily_return': 0.001,  # Mock daily return
                'sharpe_ratio': 1.5  # Mock Sharpe ratio
            }
        } 