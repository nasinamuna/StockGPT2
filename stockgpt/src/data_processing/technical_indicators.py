import pandas as pd
import numpy as np
import logging
import ta
from pathlib import Path
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechnicalIndicators:
    def __init__(self, processed_data_dir='data/processed'):
        """Initialize the technical indicators calculator."""
        self.processed_data_dir = Path(processed_data_dir)
        
    def calculate_indicators(self, symbol, save=True):
        """Calculate technical indicators for a stock and optionally save results."""
        try:
            # Load preprocessed market data
            file_path = self.processed_data_dir / 'market_data' / f"{symbol}_processed.csv"
            if not file_path.exists():
                logger.error(f"Processed market data file not found for {symbol}")
                return None
                
            df = pd.read_csv(file_path)
            
            # Convert date column to datetime if needed
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
            
            # Calculate trend indicators
            self._add_trend_indicators(df)
            
            # Calculate momentum indicators
            self._add_momentum_indicators(df)
            
            # Calculate volatility indicators
            self._add_volatility_indicators(df)
            
            # Calculate volume indicators
            self._add_volume_indicators(df)
            
            # Calculate other custom indicators
            self._add_custom_indicators(df)
            
            if save:
                # Save the data with technical indicators
                output_path = self.processed_data_dir / 'technical_indicators' / f"{symbol}_indicators.csv"
                os.makedirs(output_path.parent, exist_ok=True)
                df.to_csv(output_path)
                logger.info(f"Technical indicators saved to {output_path}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {str(e)}")
            return None
    
    def _add_trend_indicators(self, df):
        """Add trend indicators to the DataFrame."""
        try:
            # Simple Moving Averages (already added in preprocessing)
            if '20d_MA' not in df.columns:
                df['20d_MA'] = df['Close'].rolling(window=20).mean()
            if '50d_MA' not in df.columns:
                df['50d_MA'] = df['Close'].rolling(window=50).mean()
            if '200d_MA' not in df.columns:
                df['200d_MA'] = df['Close'].rolling(window=200).mean()
            
            # Exponential Moving Averages
            df['20d_EMA'] = df['Close'].ewm(span=20, adjust=False).mean()
            df['50d_EMA'] = df['Close'].ewm(span=50, adjust=False).mean()
            df['200d_EMA'] = df['Close'].ewm(span=200, adjust=False).mean()
            
            # MACD
            macd = ta.trend.MACD(df['Close'])
            df['MACD_Line'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Histogram'] = macd.macd_diff()
            
            # Average Directional Index (ADX)
            adx = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'])
            df['ADX'] = adx.adx()
            df['DI_Positive'] = adx.adx_pos()
            df['DI_Negative'] = adx.adx_neg()
            
            # Parabolic SAR
            df['PSAR'] = ta.trend.PSARIndicator(df['High'], df['Low'], df['Close']).psar()
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding trend indicators: {str(e)}")
            return df
    
    def _add_momentum_indicators(self, df):
        """Add momentum indicators to the DataFrame."""
        try:
            # Relative Strength Index (RSI)
            df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
            
            # Stochastic Oscillator
            stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
            df['Stoch_K'] = stoch.stoch()
            df['Stoch_D'] = stoch.stoch_signal()
            
            # Commodity Channel Index (CCI)
            df['CCI'] = ta.trend.CCIIndicator(df['High'], df['Low'], df['Close']).cci()
            
            # Williams %R
            df['Williams_R'] = ta.momentum.WilliamsRIndicator(df['High'], df['Low'], df['Close']).williams_r()
            
            # Rate of Change (ROC)
            df['ROC'] = ta.momentum.ROCIndicator(df['Close']).roc()
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding momentum indicators: {str(e)}")
            return df
    
    def _add_volatility_indicators(self, df):
        """Add volatility indicators to the DataFrame."""
        try:
            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(df['Close'])
            df['BB_High'] = bollinger.bollinger_hband()
            df['BB_Mid'] = bollinger.bollinger_mavg()
            df['BB_Low'] = bollinger.bollinger_lband()
            df['BB_Width'] = bollinger.bollinger_wband()
            
            # Average True Range (ATR)
            df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close']).average_true_range()
            
            # Keltner Channels
            keltner = ta.volatility.KeltnerChannel(df['High'], df['Low'], df['Close'])
            df['KC_High'] = keltner.keltner_channel_hband()
            df['KC_Mid'] = keltner.keltner_channel_mband()
            df['KC_Low'] = keltner.keltner_channel_lband()
            df['KC_Width'] = df['KC_High'] - df['KC_Low']
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding volatility indicators: {str(e)}")
            return df
    
    def _add_volume_indicators(self, df):
        """Add volume indicators to the DataFrame."""
        try:
            # Ensure Volume column exists
            if 'Volume' not in df.columns:
                logger.warning("Volume data not available, skipping volume indicators")
                return df
                
            # On-Balance Volume (OBV)
            df['OBV'] = ta.volume.OnBalanceVolumeIndicator(df['Close'], df['Volume']).on_balance_volume()
            
            # Volume Weighted Average Price (VWAP)
            # Note: VWAP is typically calculated on intraday data, but we'll use a daily approximation
            df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
            
            # Chaikin Money Flow (CMF)
            df['CMF'] = ta.volume.ChaikinMoneyFlowIndicator(df['High'], df['Low'], df['Close'], df['Volume']).chaikin_money_flow()
            
            # Money Flow Index (MFI)
            df['MFI'] = ta.volume.MFIIndicator(df['High'], df['Low'], df['Close'], df['Volume']).money_flow_index()
            
            # Ease of Movement (EoM)
            df['EoM'] = ta.volume.EaseOfMovementIndicator(df['High'], df['Low'], df['Volume']).ease_of_movement()
            
            # Volume Price Trend (VPT)
            df['VPT'] = ta.volume.VolumePriceTrendIndicator(df['Close'], df['Volume']).volume_price_trend()
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding volume indicators: {str(e)}")
            return df
    
    def _add_custom_indicators(self, df):
        """Add custom technical indicators to the DataFrame."""
        try:
            # Price Rate of Change
            df['Price_ROC_5'] = ((df['Close'] / df['Close'].shift(5)) - 1) * 100
            df['Price_ROC_10'] = ((df['Close'] / df['Close'].shift(10)) - 1) * 100
            df['Price_ROC_20'] = ((df['Close'] / df['Close'].shift(20)) - 1) * 100
            
            # Linear Regression Slope (over 20 days)
            for i in range(20, len(df)):
                prices = df['Close'].iloc[i-20:i].values
                x = np.arange(20)
                slope, _, _, _, _ = np.polyfit(x, prices, 1, full=True)
                df.loc[df.index[i], 'Linear_Reg_Slope'] = slope[0]
            
            # Moving Average Convergence/Divergence (MACD) Signal Line Crossover
            if 'MACD_Line' in df.columns and 'MACD_Signal' in df.columns:
                df['MACD_Crossover'] = np.where(
                    df['MACD_Line'] > df['MACD_Signal'], 1,
                    np.where(df['MACD_Line'] < df['MACD_Signal'], -1, 0)
                )
            
            # Golden Cross / Death Cross
            if '50d_MA' in df.columns and '200d_MA' in df.columns:
                df['Golden_Cross'] = np.where(
                    (df['50d_MA'] > df['200d_MA']) & (df['50d_MA'].shift(1) <= df['200d_MA'].shift(1)), 1,
                    np.where((df['50d_MA'] < df['200d_MA']) & (df['50d_MA'].shift(1) >= df['200d_MA'].shift(1)), -1, 0)
                )
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding custom indicators: {str(e)}")
            return df 