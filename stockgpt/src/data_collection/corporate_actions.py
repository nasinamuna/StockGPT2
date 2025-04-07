import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import logging
import os
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CorporateActionsCollector:
    def __init__(self, config_path='config/data_sources.json'):
        """Initialize the corporate actions collector with configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.data_dir = Path('data/raw/corporate_actions')
        os.makedirs(self.data_dir, exist_ok=True)
        
    def get_corporate_actions(self, symbol):
        """Collect corporate actions data for a company."""
        try:
            actions = {}
            
            # Get dividends
            dividends = self._get_dividends(symbol)
            if dividends is not None:
                actions['dividends'] = dividends
            
            # Get stock splits
            splits = self._get_stock_splits(symbol)
            if splits is not None:
                actions['splits'] = splits
            
            # Get rights issues
            rights = self._get_rights_issues(symbol)
            if rights is not None:
                actions['rights'] = rights
            
            # Get bonus issues
            bonus = self._get_bonus_issues(symbol)
            if bonus is not None:
                actions['bonus'] = bonus
            
            if actions:
                logger.info(f"Successfully collected corporate actions for {symbol}")
                return actions
            else:
                logger.warning(f"No corporate actions found for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error collecting corporate actions for {symbol}: {str(e)}")
            return None
    
    def _get_dividends(self, symbol):
        """Get dividend history for a company."""
        try:
            # Map stock symbol to NSE symbol
            symbol_map = self.config.get('nse_symbols', {})
            nse_symbol = symbol_map.get(symbol, symbol)
            
            url = f"https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol={nse_symbol}&category=Corporate%20Actions"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch dividends from NSE for {symbol}: Status code {response.status_code}")
                return None
                
            # The data is likely in JSON format in the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # This is a placeholder for the actual parsing logic
            # The exact implementation will depend on the structure of the NSE page
            dividends = []
            
            # Convert to DataFrame
            if dividends:
                dividends_df = pd.DataFrame(dividends)
                return dividends_df
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error collecting dividends for {symbol}: {str(e)}")
            return None
    
    def _get_stock_splits(self, symbol):
        """Get stock split history for a company."""
        # Similar implementation for stock splits
        # ...
        return None
    
    def _get_rights_issues(self, symbol):
        """Get rights issue history for a company."""
        # Similar implementation for rights issues
        # ...
        return None
    
    def _get_bonus_issues(self, symbol):
        """Get bonus issue history for a company."""
        # Similar implementation for bonus issues
        # ...
        return None
    
    def save_corporate_actions(self, data, symbol, file_format='json'):
        """Save corporate actions data to a file."""
        try:
            file_path = self.data_dir / f"{symbol}_corporate_actions.{file_format}"
            
            if file_format == 'json':
                with open(file_path, 'w') as f:
                    json.dump(data, f)
            elif file_format == 'csv':
                # Convert each action type to CSV
                for action_type, action_data in data.items():
                    if isinstance(action_data, pd.DataFrame):
                        action_path = self.data_dir / f"{symbol}_{action_type}.csv"
                        action_data.to_csv(action_path, index=False)
            else:
                logger.error(f"Unsupported file format: {file_format}")
                return False
                
            logger.info(f"Corporate actions data saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving corporate actions data: {str(e)}")
            return False 