import pandas as pd
import yfinance as yf
import nsepy
import requests
from bs4 import BeautifulSoup
import datetime
import json
import time
import logging
import calendar

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketDataCollector:
    def __init__(self, config_path='config/data_sources.json'):
        """Initialize the market data collector with configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def get_stock_price_yahoo(self, symbol, start_date, end_date=None, interval='1d'):
        """Collect historical stock price data from Yahoo Finance."""
        try:
            # Add .NS suffix for NSE stocks if not present
            if not symbol.endswith(('.NS', '.BO')):
                symbol = f"{symbol}.NS"
                
            # Get data from yfinance
            stock_data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
            
            if stock_data.empty:
                logger.warning(f"No data found for {symbol} on Yahoo Finance")
                return None
                
            # Add symbol column
            stock_data['Symbol'] = symbol
            
            # Reset index to make date a column
            stock_data = stock_data.reset_index()
            
            logger.info(f"Successfully collected {len(stock_data)} records for {symbol} from Yahoo Finance")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error collecting data for {symbol} from Yahoo Finance: {str(e)}")
            return None
    
    def get_stock_price_nse(self, symbol, start_date, end_date=None):
        """Collect historical stock price data from NSE Python library."""
        try:
            if end_date is None:
                end_date = datetime.datetime.now().date()
                
            # Convert string dates to datetime if needed
            if isinstance(start_date, str):
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
                
            # Get data from nsepy
            stock_data = nsepy.get_history(symbol=symbol, start=start_date, end=end_date)
            
            if stock_data.empty:
                logger.warning(f"No data found for {symbol} on NSE")
                return None
                
            # Add symbol column
            stock_data['Symbol'] = symbol
            
            # Reset index to make date a column
            stock_data = stock_data.reset_index()
            
            logger.info(f"Successfully collected {len(stock_data)} records for {symbol} from NSE")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error collecting data for {symbol} from NSE: {str(e)}")
            return None
    
    def get_stock_price_bse(self, symbol, start_date, end_date=None):
        """Scrape historical stock price data from BSE website."""
        # Implementation for BSE scraping...
        pass
    
    def get_stock_price_moneycontrol(self, symbol):
        """Scrape stock price data from MoneyControl."""
        try:
            # Map stock symbol to MoneyControl URL
            symbol_map = self.config.get('moneycontrol_symbols', {})
            mc_symbol = symbol_map.get(symbol)
            
            if not mc_symbol:
                logger.warning(f"No mapping found for {symbol} in MoneyControl")
                return None
                
            url = f"https://www.moneycontrol.com/india/stockpricequote/{mc_symbol}"
            
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to fetch data from MoneyControl for {symbol}: Status code {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract stock data from the page
            price_div = soup.find('div', {'class': 'inprice1'})
            if not price_div:
                logger.warning(f"Could not find price data for {symbol} on MoneyControl")
                return None
                
            current_price = price_div.find('span').text.strip()
            
            # Extract other data points as needed
            data = {
                'Symbol': symbol,
                'CurrentPrice': current_price,
                # Add other extracted data
            }
            
            logger.info(f"Successfully collected data for {symbol} from MoneyControl")
            return pd.DataFrame([data])
            
        except Exception as e:
            logger.error(f"Error collecting data for {symbol} from MoneyControl: {str(e)}")
            return None
    
    def get_derivatives_data(self, symbol, expiry_date=None):
        """Collect derivatives data (options, futures) for a stock."""
        try:
            # If no expiry date is provided, get the nearest expiry
            if expiry_date is None:
                # Get current date
                current_date = datetime.datetime.now().date()
                # Get the last Thursday of the current month
                last_day = calendar.monthrange(current_date.year, current_date.month)[1]
                last_date = datetime.date(current_date.year, current_date.month, last_day)
                while last_date.weekday() != 3:  # 3 is Thursday
                    last_date -= datetime.timedelta(days=1)
                expiry_date = last_date
                
            # Get options chain from NSE
            options_data = nsepy.get_option_chain(symbol=symbol, expiry=expiry_date)
            
            if options_data.empty:
                logger.warning(f"No derivatives data found for {symbol}")
                return None
                
            logger.info(f"Successfully collected derivatives data for {symbol} with expiry {expiry_date}")
            return options_data
            
        except Exception as e:
            logger.error(f"Error collecting derivatives data for {symbol}: {str(e)}")
            return None
    
    def save_data(self, data, file_path):
        """Save collected data to a CSV file."""
        try:
            data.to_csv(file_path, index=False)
            logger.info(f"Data saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving data to {file_path}: {str(e)}")
            return False 