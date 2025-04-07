import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import logging
import os
import re
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinancialStatementsCollector:
    def __init__(self, config_path='config/data_sources.json'):
        """Initialize the financial statements collector with configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.data_dir = Path('data/raw/financial_statements')
        os.makedirs(self.data_dir, exist_ok=True)
        
    def get_balance_sheet(self, symbol, consolidated=True, years=5):
        """Collect balance sheet data for a company."""
        try:
            # Map stock symbol to ScreenerAPI URL
            symbol_map = self.config.get('screener_symbols', {})
            screener_symbol = symbol_map.get(symbol)
            
            if not screener_symbol:
                logger.warning(f"No mapping found for {symbol} in Screener")
                return None
                
            # Determine URL based on whether we want consolidated or standalone
            statement_type = 'consolidated' if consolidated else 'standalone'
            url = f"https://www.screener.in/api/company/{screener_symbol}/balance-sheet/?statement_type={statement_type}"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch balance sheet from Screener for {symbol}: Status code {response.status_code}")
                return None
                
            data = response.json()
            
            # Process the JSON data into a pandas DataFrame
            balance_sheet = pd.DataFrame(data['rows'])
            
            # Set the first column as the index
            balance_sheet.set_index(balance_sheet.columns[0], inplace=True)
            
            # Transpose the data for easier analysis
            balance_sheet = balance_sheet.T
            
            # Add symbol column
            balance_sheet['Symbol'] = symbol
            
            logger.info(f"Successfully collected balance sheet for {symbol} from Screener")
            return balance_sheet
            
        except Exception as e:
            logger.error(f"Error collecting balance sheet for {symbol} from Screener: {str(e)}")
            return None
    
    def get_income_statement(self, symbol, consolidated=True, years=5):
        """Collect income statement data for a company."""
        try:
            # Map stock symbol to ScreenerAPI URL
            symbol_map = self.config.get('screener_symbols', {})
            screener_symbol = symbol_map.get(symbol)
            
            if not screener_symbol:
                logger.warning(f"No mapping found for {symbol} in Screener")
                return None
                
            # Determine URL based on whether we want consolidated or standalone
            statement_type = 'consolidated' if consolidated else 'standalone'
            url = f"https://www.screener.in/api/company/{screener_symbol}/profit-loss/?statement_type={statement_type}"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch income statement from Screener for {symbol}: Status code {response.status_code}")
                return None
                
            data = response.json()
            
            # Process the JSON data into a pandas DataFrame
            income_statement = pd.DataFrame(data['rows'])
            
            # Set the first column as the index
            income_statement.set_index(income_statement.columns[0], inplace=True)
            
            # Transpose the data for easier analysis
            income_statement = income_statement.T
            
            # Add symbol column
            income_statement['Symbol'] = symbol
            
            logger.info(f"Successfully collected income statement for {symbol} from Screener")
            return income_statement
            
        except Exception as e:
            logger.error(f"Error collecting income statement for {symbol}: {str(e)}")
            return None
    
    def get_cash_flow_statement(self, symbol, consolidated=True, years=5):
        """Collect cash flow statement data for a company."""
        try:
            # Map stock symbol to ScreenerAPI URL
            symbol_map = self.config.get('screener_symbols', {})
            screener_symbol = symbol_map.get(symbol)
            
            if not screener_symbol:
                logger.warning(f"No mapping found for {symbol} in Screener")
                return None
                
            # Determine URL based on whether we want consolidated or standalone
            statement_type = 'consolidated' if consolidated else 'standalone'
            url = f"https://www.screener.in/api/company/{screener_symbol}/cash-flow/?statement_type={statement_type}"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch cash flow statement from Screener for {symbol}: Status code {response.status_code}")
                return None
                
            data = response.json()
            
            # Process the JSON data into a pandas DataFrame
            cash_flow = pd.DataFrame(data['rows'])
            
            # Set the first column as the index
            cash_flow.set_index(cash_flow.columns[0], inplace=True)
            
            # Transpose the data for easier analysis
            cash_flow = cash_flow.T
            
            # Add symbol column
            cash_flow['Symbol'] = symbol
            
            logger.info(f"Successfully collected cash flow statement for {symbol} from Screener")
            return cash_flow
            
        except Exception as e:
            logger.error(f"Error collecting cash flow statement for {symbol}: {str(e)}")
            return None
    
    def get_quarterly_results(self, symbol, consolidated=True, quarters=20):
        """Collect quarterly financial results for a company."""
        try:
            # Map stock symbol to ScreenerAPI URL
            symbol_map = self.config.get('screener_symbols', {})
            screener_symbol = symbol_map.get(symbol)
            
            if not screener_symbol:
                logger.warning(f"No mapping found for {symbol} in Screener")
                return None
                
            # Determine URL based on whether we want consolidated or standalone
            statement_type = 'consolidated' if consolidated else 'standalone'
            url = f"https://www.screener.in/api/company/{screener_symbol}/quarterly-results/?statement_type={statement_type}"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch quarterly results from Screener for {symbol}: Status code {response.status_code}")
                return None
                
            data = response.json()
            
            # Process the JSON data into a pandas DataFrame
            quarterly_results = pd.DataFrame(data['rows'])
            
            # Set the first column as the index
            quarterly_results.set_index(quarterly_results.columns[0], inplace=True)
            
            # Transpose the data for easier analysis
            quarterly_results = quarterly_results.T
            
            # Add symbol column
            quarterly_results['Symbol'] = symbol
            
            logger.info(f"Successfully collected quarterly results for {symbol} from Screener")
            return quarterly_results
            
        except Exception as e:
            logger.error(f"Error collecting quarterly results for {symbol}: {str(e)}")
            return None
    
    def calculate_financial_ratios(self, balance_sheet, income_statement, cash_flow=None):
        """Calculate key financial ratios based on collected financial statements."""
        try:
            if balance_sheet is None or income_statement is None:
                logger.error("Missing required financial statements for ratio calculation")
                return None
                
            # Calculate various financial ratios
            ratios = {}
            
            # Profitability Ratios
            if 'Revenue' in income_statement.index and 'Net Profit' in income_statement.index:
                ratios['Net Profit Margin'] = income_statement.loc['Net Profit'] / income_statement.loc['Revenue']
            
            if 'Total Assets' in balance_sheet.index and 'Net Profit' in income_statement.index:
                ratios['Return on Assets'] = income_statement.loc['Net Profit'] / balance_sheet.loc['Total Assets']
            
            if 'Total Equity' in balance_sheet.index and 'Net Profit' in income_statement.index:
                ratios['Return on Equity'] = income_statement.loc['Net Profit'] / balance_sheet.loc['Total Equity']
            
            # Liquidity Ratios
            if 'Current Assets' in balance_sheet.index and 'Current Liabilities' in balance_sheet.index:
                ratios['Current Ratio'] = balance_sheet.loc['Current Assets'] / balance_sheet.loc['Current Liabilities']
            
            # Leverage Ratios
            if 'Total Debt' in balance_sheet.index and 'Total Equity' in balance_sheet.index:
                ratios['Debt to Equity'] = balance_sheet.loc['Total Debt'] / balance_sheet.loc['Total Equity']
            
            # Convert ratios to DataFrame
            ratios_df = pd.DataFrame(ratios)
            
            logger.info(f"Successfully calculated financial ratios")
            return ratios_df
            
        except Exception as e:
            logger.error(f"Error calculating financial ratios: {str(e)}")
            return None
    
    def save_financial_data(self, data, symbol, statement_type, file_format='csv'):
        """Save financial statement data to a file."""
        try:
            file_path = self.data_dir / f"{symbol}_{statement_type}.{file_format}"
            
            if file_format == 'csv':
                data.to_csv(file_path)
            elif file_format == 'json':
                data.to_json(file_path, orient='records')
            else:
                logger.error(f"Unsupported file format: {file_format}")
                return False
                
            logger.info(f"Financial data saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving financial data: {str(e)}")
            return False 