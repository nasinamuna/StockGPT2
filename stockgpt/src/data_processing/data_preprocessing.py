import pandas as pd
import numpy as np
import logging
from pathlib import Path
import os
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataPreprocessor:
    def __init__(self, raw_data_dir='data/raw', processed_data_dir='data/processed'):
        """Initialize the data preprocessor with directory paths."""
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_data_dir = Path(processed_data_dir)
        os.makedirs(self.processed_data_dir, exist_ok=True)
        
    def preprocess_market_data(self, symbol):
        """Clean and preprocess market data for a stock."""
        try:
            # Load raw market data
            file_path = self.raw_data_dir / 'market_data' / f"{symbol}_price_data.csv"
            if not file_path.exists():
                logger.error(f"Market data file not found for {symbol}")
                return None
                
            df = pd.read_csv(file_path)
            
            # Convert date column to datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
            
            # Handle missing values
            if df.isnull().sum().sum() > 0:
                logger.info(f"Handling missing values in market data for {symbol}")
                
                # Forward fill for most columns
                df.fillna(method='ffill', inplace=True)
                
                # For volume data, use 0 for missing values
                if 'Volume' in df.columns and df['Volume'].isnull().any():
                    df['Volume'].fillna(0, inplace=True)
            
            # Remove duplicate dates
            if df.index.duplicated().any():
                logger.warning(f"Removing duplicate dates in market data for {symbol}")
                df = df[~df.index.duplicated(keep='first')]
            
            # Sort by date
            df.sort_index(inplace=True)
            
            # Calculate additional columns (e.g., returns)
            df['Daily_Return'] = df['Close'].pct_change()
            
            # Calculate rolling metrics
            df['20d_MA'] = df['Close'].rolling(window=20).mean()
            df['50d_MA'] = df['Close'].rolling(window=50).mean()
            df['200d_MA'] = df['Close'].rolling(window=200).mean()
            
            # Calculate volatility (20-day rolling standard deviation of returns)
            df['20d_Volatility'] = df['Daily_Return'].rolling(window=20).std() * np.sqrt(20)
            
            # Save preprocessed data
            output_path = self.processed_data_dir / 'market_data' / f"{symbol}_processed.csv"
            os.makedirs(output_path.parent, exist_ok=True)
            df.to_csv(output_path)
            
            logger.info(f"Successfully preprocessed market data for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing market data for {symbol}: {str(e)}")
            return None
    
    def preprocess_financial_statements(self, symbol):
        """Clean and preprocess financial statement data for a company."""
        try:
            # Process each type of financial statement
            statements = {}
            
            # Balance Sheet
            bs_path = self.raw_data_dir / 'financial_statements' / f"{symbol}_balance_sheet.csv"
            if bs_path.exists():
                bs_df = pd.read_csv(bs_path)
                statements['balance_sheet'] = self._clean_financial_statement(bs_df)
            
            # Income Statement
            is_path = self.raw_data_dir / 'financial_statements' / f"{symbol}_income_statement.csv"
            if is_path.exists():
                is_df = pd.read_csv(is_path)
                statements['income_statement'] = self._clean_financial_statement(is_df)
            
            # Cash Flow Statement
            cf_path = self.raw_data_dir / 'financial_statements' / f"{symbol}_cash_flow.csv"
            if cf_path.exists():
                cf_df = pd.read_csv(cf_path)
                statements['cash_flow'] = self._clean_financial_statement(cf_df)
            
            # Calculate financial ratios if we have both balance sheet and income statement
            if 'balance_sheet' in statements and 'income_statement' in statements:
                ratios = self._calculate_financial_ratios(statements['balance_sheet'], statements['income_statement'])
                statements['financial_ratios'] = ratios
            
            # Save preprocessed statements
            for statement_type, df in statements.items():
                output_path = self.processed_data_dir / 'financial_statements' / f"{symbol}_{statement_type}.csv"
                os.makedirs(output_path.parent, exist_ok=True)
                df.to_csv(output_path)
            
            logger.info(f"Successfully preprocessed financial statements for {symbol}")
            return statements
            
        except Exception as e:
            logger.error(f"Error preprocessing financial statements for {symbol}: {str(e)}")
            return None
    
    def _clean_financial_statement(self, df):
        """Clean and standardize a financial statement DataFrame."""
        try:
            # Handle common preprocessing tasks for financial statements
            
            # Remove any duplicate columns
            df = df.loc[:, ~df.columns.duplicated()]
            
            # Convert string numbers to float (handle commas, etc.)
            for col in df.columns:
                if col == 'Symbol' or col == 'Year' or col == 'Quarter':
                    continue
                    
                if df[col].dtype == 'object':
                    df[col] = df[col].replace('[\₹,]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Handle missing values
            df.fillna(0, inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error cleaning financial statement: {str(e)}")
            return df
    
    def _calculate_financial_ratios(self, balance_sheet, income_statement):
        """Calculate key financial ratios from balance sheet and income statement."""
        try:
            ratios = pd.DataFrame()
            
            # Get common time periods
            common_periods = set(balance_sheet['Year']) & set(income_statement['Year'])
            
            # Initialize ratios DataFrame
            ratios_data = []
            
            for period in common_periods:
                bs = balance_sheet[balance_sheet['Year'] == period].iloc[0]
                is_ = income_statement[income_statement['Year'] == period].iloc[0]
                
                period_ratios = {
                    'Year': period,
                    # Profitability Ratios
                    'Gross_Margin': is_['Gross Profit'] / is_['Revenue'] if 'Gross Profit' in is_ and 'Revenue' in is_ and is_['Revenue'] != 0 else None,
                    'Operating_Margin': is_['Operating Profit'] / is_['Revenue'] if 'Operating Profit' in is_ and 'Revenue' in is_ and is_['Revenue'] != 0 else None,
                    'Net_Margin': is_['Net Profit'] / is_['Revenue'] if 'Net Profit' in is_ and 'Revenue' in is_ and is_['Revenue'] != 0 else None,
                    
                    # Liquidity Ratios
                    'Current_Ratio': bs['Current Assets'] / bs['Current Liabilities'] if 'Current Assets' in bs and 'Current Liabilities' in bs and bs['Current Liabilities'] != 0 else None,
                    'Quick_Ratio': (bs['Current Assets'] - bs['Inventory']) / bs['Current Liabilities'] if 'Current Assets' in bs and 'Inventory' in bs and 'Current Liabilities' in bs and bs['Current Liabilities'] != 0 else None,
                    
                    # Solvency Ratios
                    'Debt_to_Equity': bs['Total Debt'] / bs['Shareholders Equity'] if 'Total Debt' in bs and 'Shareholders Equity' in bs and bs['Shareholders Equity'] != 0 else None,
                    'Interest_Coverage': is_['Operating Profit'] / is_['Interest Expense'] if 'Operating Profit' in is_ and 'Interest Expense' in is_ and is_['Interest Expense'] != 0 else None,
                    
                    # Efficiency Ratios
                    'Asset_Turnover': is_['Revenue'] / bs['Total Assets'] if 'Revenue' in is_ and 'Total Assets' in bs and bs['Total Assets'] != 0 else None,
                    
                    # Valuation Ratios
                    'ROA': is_['Net Profit'] / bs['Total Assets'] if 'Net Profit' in is_ and 'Total Assets' in bs and bs['Total Assets'] != 0 else None,
                    'ROE': is_['Net Profit'] / bs['Shareholders Equity'] if 'Net Profit' in is_ and 'Shareholders Equity' in bs and bs['Shareholders Equity'] != 0 else None
                }
                
                ratios_data.append(period_ratios)
            
            ratios = pd.DataFrame(ratios_data)
            
            return ratios
            
        except Exception as e:
            logger.error(f"Error calculating financial ratios: {str(e)}")
            return pd.DataFrame()
    
    def preprocess_news_data(self, symbol):
        """Clean and preprocess news data for sentiment analysis."""
        try:
            # Load raw news data
            file_path = self.raw_data_dir / 'news_social' / f"{symbol}_news.csv"
            if not file_path.exists():
                logger.error(f"News data file not found for {symbol}")
                return None
                
            df = pd.read_csv(file_path)
            
            # Convert date column to datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                
            # Remove duplicate articles
            if df.duplicated(subset=['Headline']).any():
                logger.warning(f"Removing duplicate news articles for {symbol}")
                df = df[~df.duplicated(subset=['Headline'], keep='first')]
            
            # Clean text content
            if 'Content' in df.columns:
                df['Clean_Content'] = df['Content'].apply(self._clean_text)
            
            # Sort by date
            df.sort_values('Date', inplace=True)
            
            # Save preprocessed data
            output_path = self.processed_data_dir / 'news_social' / f"{symbol}_news_processed.csv"
            os.makedirs(output_path.parent, exist_ok=True)
            df.to_csv(output_path, index=False)
            
            logger.info(f"Successfully preprocessed news data for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error preprocessing news data for {symbol}: {str(e)}")
            return None
    
    def _clean_text(self, text):
        """Clean and normalize text data for NLP processing."""
        if pd.isna(text) or text is None:
            return ""
            
        # Convert to string if not already
        text = str(text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters (keep alphanumeric, spaces, basic punctuation)
        text = re.sub(r'[^\w\s.,!?]', '', text)
        
        return text 