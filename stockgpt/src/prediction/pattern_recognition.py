import pandas as pd
import numpy as np
import logging
from pathlib import Path
import os
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import mplfinance as mpf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PatternRecognition:
    def __init__(self, data_dir: str = "data/processed"):
        """
        Initialize the PatternRecognition class.
        
        Args:
            data_dir (str): Directory containing processed data
        """
        self.data_dir = Path(data_dir)
        self.logger = logging.getLogger(__name__)
        
        # Define candlestick patterns
        self.candlestick_patterns = {
            'doji': self._is_doji,
            'hammer': self._is_hammer,
            'shooting_star': self._is_shooting_star,
            'bullish_engulfing': self._is_bullish_engulfing,
            'bearish_engulfing': self._is_bearish_engulfing,
            'morning_star': self._is_morning_star,
            'evening_star': self._is_evening_star,
            'harami': self._is_harami,
            'marubozu': self._is_marubozu,
            'piercing_pattern': self._is_piercing_pattern,
            'dark_cloud_cover': self._is_dark_cloud_cover
        }
        
        # Define chart patterns
        self.chart_patterns = {
            'double_top': self._detect_double_top,
            'double_bottom': self._detect_double_bottom,
            'head_and_shoulders': self._detect_head_and_shoulders,
            'inverse_head_and_shoulders': self._detect_inverse_head_and_shoulders,
            'triangle': self._detect_triangle,
            'channel': self._detect_channel,
            'triple_top': self._detect_triple_top,
            'triple_bottom': self._detect_triple_bottom,
            'cup_and_handle': self._detect_cup_and_handle,
            'wedge': self._detect_wedge
        }

    def detect_candlestick_patterns(self, symbol, lookback=30):
        """Detect candlestick patterns in the stock's price data."""
        try:
            # Load processed market data
            file_path = self.data_dir / 'market_data' / f"{symbol}_processed.csv"
            if not file_path.exists():
                logger.error(f"Processed market data file not found for {symbol}")
                return None

            df = pd.read_csv(file_path)

            # Convert date column to datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)

            # Check for required OHLC columns
            required_columns = ['Open', 'High', 'Low', 'Close']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"Missing required OHLC columns for {symbol}")
                return None

            # Get the recent data based on lookback period
            recent_data = df.tail(lookback).copy()

            # Calculate necessary indicators for pattern detection
            recent_data['BodySize'] = abs(recent_data['Close'] - recent_data['Open'])
            recent_data['UpperShadow'] = recent_data['High'] - recent_data[['Open', 'Close']].max(axis=1)
            recent_data['LowerShadow'] = recent_data[['Open', 'Close']].min(axis=1) - recent_data['Low']
            recent_data['TotalRange'] = recent_data['High'] - recent_data['Low']
            recent_data['IsGreen'] = recent_data['Close'] > recent_data['Open']

            # Detect patterns
            detected_patterns = []
            for i in range(len(recent_data)):
                if i < 2:  # Skip first two rows as some patterns need 3 days of data
                    continue
                
                date = recent_data.index[i]
                patterns_for_day = []
                
                # Check each pattern
                for pattern_name, pattern_func in self.candlestick_patterns.items():
                    if pattern_func(recent_data, i):
                        patterns_for_day.append(pattern_name)
                
                if patterns_for_day:
                    detected_patterns.append({
                        'Date': date.strftime('%Y-%m-%d'),
                        'Patterns': patterns_for_day
                    })

            # Get most recent patterns (last 5 days)
            most_recent = detected_patterns[-5:] if detected_patterns else []

            # Generate insights
            insights = self._generate_pattern_insights(most_recent)

            # Organize results
            pattern_analysis = {
                'Symbol': symbol,
                'Analysis_Date': datetime.now().strftime('%Y-%m-%d'),
                'Detected_Patterns': detected_patterns,
                'Recent_Patterns': most_recent,
                'Insights': insights
            }

            # Save analysis
            output_path = self.data_dir / 'analysis' / f"{symbol}_pattern_analysis.json"
            os.makedirs(output_path.parent, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(pattern_analysis, f, indent=4)

            logger.info(f"Pattern analysis completed for {symbol}, found {len(detected_patterns)} patterns")
            return pattern_analysis

        except Exception as e:
            logger.error(f"Error detecting candlestick patterns for {symbol}: {str(e)}")
            return None

    def detect_chart_patterns(self, symbol, lookback=200):
        """Detect technical chart patterns (head and shoulders, double top, etc.)."""
        try:
            # Load processed market data
            file_path = self.data_dir / 'market_data' / f"{symbol}_processed.csv"
            if not file_path.exists():
                logger.error(f"Processed market data file not found for {symbol}")
                return None

            df = pd.read_csv(file_path)

            # Convert date column to datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)

            # Get the recent data based on lookback period
            recent_data = df.tail(lookback).copy()

            # Detect chart patterns
            chart_patterns = {
                'Double_Top': self._detect_double_top(recent_data),
                'Double_Bottom': self._detect_double_bottom(recent_data),
                'Head_And_Shoulders': self._detect_head_and_shoulders(recent_data),
                'Inverse_Head_And_Shoulders': self._detect_inverse_head_and_shoulders(recent_data),
                'Triangle': self._detect_triangle(recent_data),
                'Channel': self._detect_channel(recent_data)
            }

            # Filter out None values
            chart_patterns = {k: v for k, v in chart_patterns.items() if v is not None}

            # Generate insights
            insights = self._generate_chart_pattern_insights(chart_patterns)

            # Organize results
            pattern_analysis = {
                'Symbol': symbol,
                'Analysis_Date': datetime.now().strftime('%Y-%m-%d'),
                'Chart_Patterns': chart_patterns,
                'Insights': insights
            }

            # Save analysis
            output_path = self.data_dir / 'analysis' / f"{symbol}_chart_pattern_analysis.json"
            os.makedirs(output_path.parent, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(pattern_analysis, f, indent=4)

            logger.info(f"Chart pattern analysis completed for {symbol}, found {len(chart_patterns)} patterns")
            return pattern_analysis

        except Exception as e:
            logger.error(f"Error detecting chart patterns for {symbol}: {str(e)}")
            return None

    def _is_doji(self, open_price: float, high: float, low: float, close: float) -> Tuple[bool, float]:
        """
        Check if the candlestick is a Doji pattern.
        
        Args:
            open_price (float): Opening price
            high (float): High price
            low (float): Low price
            close (float): Closing price
            
        Returns:
            Tuple[bool, float]: (is_doji, strength)
        """
        body_size = abs(close - open_price)
        total_size = high - low
        if total_size == 0:
            return False, 0.0
            
        doji_ratio = body_size / total_size
        is_doji = doji_ratio < 0.1
        strength = 1.0 - doji_ratio if is_doji else 0.0
        return is_doji, strength

    def _is_hammer(self, open_price: float, high: float, low: float, close: float) -> Tuple[bool, float]:
        """
        Check if the candlestick is a Hammer pattern.
        
        Args:
            open_price (float): Opening price
            high (float): High price
            low (float): Low price
            close (float): Closing price
            
        Returns:
            Tuple[bool, float]: (is_hammer, strength)
        """
        body_size = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        total_size = high - low
        
        if total_size == 0:
            return False, 0.0
            
        is_hammer = (
            lower_shadow > 2 * body_size and
            upper_shadow < body_size and
            close > open_price
        )
        
        strength = (lower_shadow / total_size) if is_hammer else 0.0
        return is_hammer, strength

    def _is_shooting_star(self, open_price: float, high: float, low: float, close: float) -> Tuple[bool, float]:
        """
        Check if the candlestick is a Shooting Star pattern.
        
        Args:
            open_price (float): Opening price
            high (float): High price
            low (float): Low price
            close (float): Closing price
            
        Returns:
            Tuple[bool, float]: (is_shooting_star, strength)
        """
        body_size = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        total_size = high - low
        
        if total_size == 0:
            return False, 0.0
            
        is_shooting_star = (
            upper_shadow > 2 * body_size and
            lower_shadow < body_size and
            close < open_price
        )
        
        strength = (upper_shadow / total_size) if is_shooting_star else 0.0
        return is_shooting_star, strength

    def _is_bullish_engulfing(self, prev_open: float, prev_close: float, 
                            curr_open: float, curr_close: float) -> Tuple[bool, float]:
        """
        Check if the pattern is a Bullish Engulfing.
        
        Args:
            prev_open (float): Previous candle opening price
            prev_close (float): Previous candle closing price
            curr_open (float): Current candle opening price
            curr_close (float): Current candle closing price
            
        Returns:
            Tuple[bool, float]: (is_bullish_engulfing, strength)
        """
        is_bullish = (
            prev_close < prev_open and  # Previous candle is bearish
            curr_open < prev_close and  # Current candle opens below previous close
            curr_close > prev_open      # Current candle closes above previous open
        )
        
        if is_bullish:
            strength = min(1.0, (curr_close - prev_open) / prev_open)
        else:
            strength = 0.0
            
        return is_bullish, strength

    def _is_bearish_engulfing(self, prev_open: float, prev_close: float, 
                             curr_open: float, curr_close: float) -> Tuple[bool, float]:
        """
        Check if the pattern is a Bearish Engulfing.
        
        Args:
            prev_open (float): Previous candle opening price
            prev_close (float): Previous candle closing price
            curr_open (float): Current candle opening price
            curr_close (float): Current candle closing price
            
        Returns:
            Tuple[bool, float]: (is_bearish_engulfing, strength)
        """
        is_bearish = (
            prev_close > prev_open and  # Previous candle is bullish
            curr_open > prev_close and  # Current candle opens above previous close
            curr_close < prev_open      # Current candle closes below previous open
        )
        
        if is_bearish:
            strength = min(1.0, (prev_open - curr_close) / prev_open)
        else:
            strength = 0.0
            
        return is_bearish, strength

    def _is_morning_star(self, data: pd.DataFrame, i: int) -> Tuple[bool, float]:
        """
        Check if the pattern is a Morning Star.
        
        Args:
            data (pd.DataFrame): Price data
            i (int): Current index
            
        Returns:
            Tuple[bool, float]: (is_morning_star, strength)
        """
        if i < 2:
            return False, 0.0
            
        first = data.iloc[i-2]
        second = data.iloc[i-1]
        third = data.iloc[i]
        
        is_morning_star = (
            first['Close'] < first['Open'] and  # First candle is bearish
            abs(second['Close'] - second['Open']) < 0.1 * (first['High'] - first['Low']) and  # Second candle is small
            third['Close'] > third['Open'] and  # Third candle is bullish
            third['Close'] > (first['Open'] + first['Close']) / 2  # Third candle closes above midpoint of first candle
        )
        
        if is_morning_star:
            strength = min(1.0, (third['Close'] - first['Close']) / first['Close'])
        else:
            strength = 0.0
            
        return is_morning_star, strength

    def _is_evening_star(self, data: pd.DataFrame, i: int) -> Tuple[bool, float]:
        """
        Check if the pattern is an Evening Star.
        
        Args:
            data (pd.DataFrame): Price data
            i (int): Current index
            
        Returns:
            Tuple[bool, float]: (is_evening_star, strength)
        """
        if i < 2:
            return False, 0.0
            
        first = data.iloc[i-2]
        second = data.iloc[i-1]
        third = data.iloc[i]
        
        is_evening_star = (
            first['Close'] > first['Open'] and  # First candle is bullish
            abs(second['Close'] - second['Open']) < 0.1 * (first['High'] - first['Low']) and  # Second candle is small
            third['Close'] < third['Open'] and  # Third candle is bearish
            third['Close'] < (first['Open'] + first['Close']) / 2  # Third candle closes below midpoint of first candle
        )
        
        if is_evening_star:
            strength = min(1.0, (first['Close'] - third['Close']) / first['Close'])
        else:
            strength = 0.0
            
        return is_evening_star, strength

    def _is_harami(self, prev_open: float, prev_close: float, 
                  curr_open: float, curr_close: float) -> Tuple[bool, float]:
        """
        Check if the pattern is a Harami.
        
        Args:
            prev_open (float): Previous candle opening price
            prev_close (float): Previous candle closing price
            curr_open (float): Current candle opening price
            curr_close (float): Current candle closing price
            
        Returns:
            Tuple[bool, float]: (is_harami, strength)
        """
        prev_body = abs(prev_close - prev_open)
        curr_body = abs(curr_close - curr_open)
        
        is_harami = (
            prev_body > 2 * curr_body and  # Previous candle is much larger
            min(curr_open, curr_close) > min(prev_open, prev_close) and  # Current candle is within previous body
            max(curr_open, curr_close) < max(prev_open, prev_close)
        )
        
        if is_harami:
            strength = min(1.0, prev_body / curr_body)
        else:
            strength = 0.0
            
        return is_harami, strength

    def _is_marubozu(self, open_price: float, high: float, low: float, close: float) -> Tuple[bool, float]:
        """
        Check if the candlestick is a Marubozu pattern.
        
        Args:
            open_price (float): Opening price
            high (float): High price
            low (float): Low price
            close (float): Closing price
            
        Returns:
            Tuple[bool, float]: (is_marubozu, strength)
        """
        body_size = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        total_size = high - low
        
        if total_size == 0:
            return False, 0.0
            
        is_marubozu = (
            upper_shadow < 0.1 * body_size and
            lower_shadow < 0.1 * body_size
        )
        
        strength = (body_size / total_size) if is_marubozu else 0.0
        return is_marubozu, strength

    def _is_piercing_pattern(self, prev_open: float, prev_close: float, 
                           curr_open: float, curr_close: float) -> Tuple[bool, float]:
        """
        Check if the pattern is a Piercing Pattern.
        
        Args:
            prev_open (float): Previous candle opening price
            prev_close (float): Previous candle closing price
            curr_open (float): Current candle opening price
            curr_close (float): Current candle closing price
            
        Returns:
            Tuple[bool, float]: (is_piercing, strength)
        """
        prev_mid = (prev_open + prev_close) / 2
        
        is_piercing = (
            prev_close < prev_open and  # Previous candle is bearish
            curr_open < prev_close and  # Current candle opens below previous close
            curr_close > prev_mid and   # Current candle closes above previous midpoint
            curr_close < prev_open      # Current candle closes below previous open
        )
        
        if is_piercing:
            strength = min(1.0, (curr_close - prev_close) / prev_close)
        else:
            strength = 0.0
            
        return is_piercing, strength

    def _is_dark_cloud_cover(self, prev_open: float, prev_close: float, 
                           curr_open: float, curr_close: float) -> Tuple[bool, float]:
        """
        Check if the pattern is a Dark Cloud Cover.
        
        Args:
            prev_open (float): Previous candle opening price
            prev_close (float): Previous candle closing price
            curr_open (float): Current candle opening price
            curr_close (float): Current candle closing price
            
        Returns:
            Tuple[bool, float]: (is_dark_cloud, strength)
        """
        prev_mid = (prev_open + prev_close) / 2
        
        is_dark_cloud = (
            prev_close > prev_open and  # Previous candle is bullish
            curr_open > prev_close and  # Current candle opens above previous close
            curr_close < prev_mid and   # Current candle closes below previous midpoint
            curr_close > prev_open      # Current candle closes above previous open
        )
        
        if is_dark_cloud:
            strength = min(1.0, (prev_close - curr_close) / prev_close)
        else:
            strength = 0.0
            
        return is_dark_cloud, strength

    def _detect_double_top(self, data: pd.DataFrame, window: int = 20) -> Dict:
        """
        Detect Double Top pattern.
        
        Args:
            data (pd.DataFrame): Price data
            window (int): Lookback window
            
        Returns:
            Dict: Pattern information
        """
        pattern_info = {
            'detected': False,
            'strength': 0.0,
            'first_top': None,
            'second_top': None,
            'neckline': None
        }
        
        if len(data) < window:
            return pattern_info
            
        # Find local maxima
        highs = data['High'].rolling(window=window, center=True).max()
        peaks = data[data['High'] == highs]
        
        if len(peaks) < 2:
            return pattern_info
            
        # Find two significant peaks
        peaks = peaks.sort_values('High', ascending=False)
        first_top = peaks.iloc[0]
        second_top = peaks.iloc[1]
        
        # Check if peaks are within 2% of each other
        price_diff = abs(first_top['High'] - second_top['High']) / first_top['High']
        if price_diff > 0.02:
            return pattern_info
            
        # Find neckline (lowest point between peaks)
        between_peaks = data[
            (data.index > first_top.name) & 
            (data.index < second_top.name)
        ]
        if len(between_peaks) == 0:
            return pattern_info
            
        neckline = between_peaks['Low'].min()
        
        # Calculate pattern strength
        pattern_height = first_top['High'] - neckline
        strength = min(1.0, pattern_height / first_top['High'])
        
        pattern_info.update({
            'detected': True,
            'strength': strength,
            'first_top': {
                'price': first_top['High'],
                'date': first_top.name
            },
            'second_top': {
                'price': second_top['High'],
                'date': second_top.name
            },
            'neckline': {
                'price': neckline,
                'date': between_peaks['Low'].idxmin()
            }
        })
        
        return pattern_info

    def _detect_double_bottom(self, data: pd.DataFrame, window: int = 20) -> Dict:
        """
        Detect Double Bottom pattern.
        
        Args:
            data (pd.DataFrame): Price data
            window (int): Lookback window
            
        Returns:
            Dict: Pattern information
        """
        pattern_info = {
            'detected': False,
            'strength': 0.0,
            'first_bottom': None,
            'second_bottom': None,
            'neckline': None
        }
        
        if len(data) < window:
            return pattern_info
            
        # Find local minima
        lows = data['Low'].rolling(window=window, center=True).min()
        troughs = data[data['Low'] == lows]
        
        if len(troughs) < 2:
            return pattern_info
            
        # Find two significant troughs
        troughs = troughs.sort_values('Low')
        first_bottom = troughs.iloc[0]
        second_bottom = troughs.iloc[1]
        
        # Check if troughs are within 2% of each other
        price_diff = abs(first_bottom['Low'] - second_bottom['Low']) / first_bottom['Low']
        if price_diff > 0.02:
            return pattern_info
            
        # Find neckline (highest point between troughs)
        between_troughs = data[
            (data.index > first_bottom.name) & 
            (data.index < second_bottom.name)
        ]
        if len(between_troughs) == 0:
            return pattern_info
            
        neckline = between_troughs['High'].max()
        
        # Calculate pattern strength
        pattern_height = neckline - first_bottom['Low']
        strength = min(1.0, pattern_height / first_bottom['Low'])
        
        pattern_info.update({
            'detected': True,
            'strength': strength,
            'first_bottom': {
                'price': first_bottom['Low'],
                'date': first_bottom.name
            },
            'second_bottom': {
                'price': second_bottom['Low'],
                'date': second_bottom.name
            },
            'neckline': {
                'price': neckline,
                'date': between_troughs['High'].idxmax()
            }
        })
        
        return pattern_info

    def _detect_triple_top(self, data: pd.DataFrame, window: int = 30) -> Dict:
        """
        Detect Triple Top pattern.
        
        Args:
            data (pd.DataFrame): Price data
            window (int): Lookback window
            
        Returns:
            Dict: Pattern information
        """
        pattern_info = {
            'detected': False,
            'strength': 0.0,
            'tops': [],
            'neckline': None
        }
        
        if len(data) < window:
            return pattern_info
            
        # Find local maxima
        highs = data['High'].rolling(window=window, center=True).max()
        peaks = data[data['High'] == highs]
        
        if len(peaks) < 3:
            return pattern_info
            
        # Find three significant peaks
        peaks = peaks.sort_values('High', ascending=False)
        tops = peaks.iloc[:3].sort_index()
        
        # Check if peaks are within 2% of each other
        max_price = tops['High'].max()
        min_price = tops['High'].min()
        price_diff = (max_price - min_price) / max_price
        if price_diff > 0.02:
            return pattern_info
            
        # Find neckline (lowest point between peaks)
        neckline = data[
            (data.index > tops.index[0]) & 
            (data.index < tops.index[-1])
        ]['Low'].min()
        
        # Calculate pattern strength
        pattern_height = max_price - neckline
        strength = min(1.0, pattern_height / max_price)
        
        pattern_info.update({
            'detected': True,
            'strength': strength,
            'tops': [{
                'price': row['High'],
                'date': idx
            } for idx, row in tops.iterrows()],
            'neckline': {
                'price': neckline,
                'date': data[data['Low'] == neckline].index[0]
            }
        })
        
        return pattern_info

    def _detect_triple_bottom(self, data: pd.DataFrame, window: int = 30) -> Dict:
        """
        Detect Triple Bottom pattern.
        
        Args:
            data (pd.DataFrame): Price data
            window (int): Lookback window
            
        Returns:
            Dict: Pattern information
        """
        pattern_info = {
            'detected': False,
            'strength': 0.0,
            'bottoms': [],
            'neckline': None
        }
        
        if len(data) < window:
            return pattern_info
            
        # Find local minima
        lows = data['Low'].rolling(window=window, center=True).min()
        troughs = data[data['Low'] == lows]
        
        if len(troughs) < 3:
            return pattern_info
            
        # Find three significant troughs
        troughs = troughs.sort_values('Low')
        bottoms = troughs.iloc[:3].sort_index()
        
        # Check if troughs are within 2% of each other
        min_price = bottoms['Low'].min()
        max_price = bottoms['Low'].max()
        price_diff = (max_price - min_price) / min_price
        if price_diff > 0.02:
            return pattern_info
            
        # Find neckline (highest point between troughs)
        neckline = data[
            (data.index > bottoms.index[0]) & 
            (data.index < bottoms.index[-1])
        ]['High'].max()
        
        # Calculate pattern strength
        pattern_height = neckline - min_price
        strength = min(1.0, pattern_height / min_price)
        
        pattern_info.update({
            'detected': True,
            'strength': strength,
            'bottoms': [{
                'price': row['Low'],
                'date': idx
            } for idx, row in bottoms.iterrows()],
            'neckline': {
                'price': neckline,
                'date': data[data['High'] == neckline].index[0]
            }
        })
        
        return pattern_info

    def _detect_cup_and_handle(self, data: pd.DataFrame, window: int = 60) -> Dict:
        """
        Detect Cup and Handle pattern.
        
        Args:
            data (pd.DataFrame): Price data
            window (int): Lookback window
            
        Returns:
            Dict: Pattern information
        """
        pattern_info = {
            'detected': False,
            'strength': 0.0,
            'left_rim': None,
            'right_rim': None,
            'handle': None
        }
        
        if len(data) < window:
            return pattern_info
            
        # Find local maxima for cup rims
        highs = data['High'].rolling(window=window//2, center=True).max()
        peaks = data[data['High'] == highs]
        
        if len(peaks) < 2:
            return pattern_info
            
        # Find two significant peaks for cup rims
        peaks = peaks.sort_values('High', ascending=False)
        left_rim = peaks.iloc[0]
        right_rim = peaks.iloc[1]
        
        # Check if rims are within 5% of each other
        price_diff = abs(left_rim['High'] - right_rim['High']) / left_rim['High']
        if price_diff > 0.05:
            return pattern_info
            
        # Find cup bottom
        between_rims = data[
            (data.index > left_rim.name) & 
            (data.index < right_rim.name)
        ]
        if len(between_rims) == 0:
            return pattern_info
            
        cup_bottom = between_rims['Low'].min()
        
        # Find handle
        after_right_rim = data[data.index > right_rim.name]
        if len(after_right_rim) == 0:
            return pattern_info
            
        handle = after_right_rim.iloc[:window//4]  # Handle should be about 1/4 of cup duration
        handle_high = handle['High'].max()
        handle_low = handle['Low'].min()
        
        # Check handle characteristics
        if handle_high > right_rim['High'] or handle_low < cup_bottom:
            return pattern_info
            
        # Calculate pattern strength
        cup_depth = (left_rim['High'] - cup_bottom) / left_rim['High']
        handle_depth = (handle_high - handle_low) / handle_high
        strength = min(1.0, (cup_depth + handle_depth) / 2)
        
        pattern_info.update({
            'detected': True,
            'strength': strength,
            'left_rim': {
                'price': left_rim['High'],
                'date': left_rim.name
            },
            'right_rim': {
                'price': right_rim['High'],
                'date': right_rim.name
            },
            'handle': {
                'high': handle_high,
                'low': handle_low,
                'start_date': handle.index[0],
                'end_date': handle.index[-1]
            }
        })
        
        return pattern_info

    def _detect_wedge(self, data: pd.DataFrame, window: int = 30) -> Dict:
        """
        Detect Wedge pattern (Rising or Falling).
        
        Args:
            data (pd.DataFrame): Price data
            window (int): Lookback window
            
        Returns:
            Dict: Pattern information
        """
        pattern_info = {
            'detected': False,
            'type': None,
            'strength': 0.0,
            'start': None,
            'end': None
        }
        
        if len(data) < window:
            return pattern_info
            
        # Calculate trend lines
        highs = data['High'].rolling(window=window//3, center=True).max()
        lows = data['Low'].rolling(window=window//3, center=True).min()
        
        # Fit lines to highs and lows
        x = np.arange(len(data))
        high_slope, high_intercept = np.polyfit(x, highs, 1)
        low_slope, low_intercept = np.polyfit(x, lows, 1)
        
        # Determine wedge type
        if high_slope < low_slope:  # Lines converging upward
            pattern_type = 'rising'
            strength = min(1.0, abs(high_slope - low_slope) / abs(high_slope))
        elif high_slope > low_slope:  # Lines converging downward
            pattern_type = 'falling'
            strength = min(1.0, abs(high_slope - low_slope) / abs(high_slope))
        else:
            return pattern_info
            
        pattern_info.update({
            'detected': True,
            'type': pattern_type,
            'strength': strength,
            'start': {
                'high': highs.iloc[0],
                'low': lows.iloc[0],
                'date': data.index[0]
            },
            'end': {
                'high': highs.iloc[-1],
                'low': lows.iloc[-1],
                'date': data.index[-1]
            }
        })
        
        return pattern_info

    def _detect_head_and_shoulders(self, data: pd.DataFrame, window: int = 40) -> Dict:
        """
        Detect Head and Shoulders pattern.
        
        Args:
            data (pd.DataFrame): Price data
            window (int): Lookback window
            
        Returns:
            Dict: Pattern information
        """
        pattern_info = {
            'detected': False,
            'strength': 0.0,
            'left_shoulder': None,
            'head': None,
            'right_shoulder': None,
            'neckline': None
        }
        
        # Implementation will be added in the next step
        return pattern_info

    def _detect_inverse_head_and_shoulders(self, data: pd.DataFrame, window: int = 40) -> Dict:
        """
        Detect Inverse Head and Shoulders pattern.
        
        Args:
            data (pd.DataFrame): Price data
            window (int): Lookback window
            
        Returns:
            Dict: Pattern information
        """
        pattern_info = {
            'detected': False,
            'strength': 0.0,
            'left_shoulder': None,
            'head': None,
            'right_shoulder': None,
            'neckline': None
        }
        
        # Implementation will be added in the next step
        return pattern_info

    def _detect_triangle(self, data: pd.DataFrame, window: int = 30) -> Dict:
        """
        Detect Triangle pattern (Ascending, Descending, or Symmetrical).
        
        Args:
            data (pd.DataFrame): Price data
            window (int): Lookback window
            
        Returns:
            Dict: Pattern information
        """
        pattern_info = {
            'detected': False,
            'type': None,
            'strength': 0.0,
            'start': None,
            'end': None
        }
        
        # Implementation will be added in the next step
        return pattern_info

    def _detect_channel(self, data: pd.DataFrame, window: int = 30) -> Dict:
        """
        Detect Channel pattern (Upward, Downward, or Horizontal).
        
        Args:
            data (pd.DataFrame): Price data
            window (int): Lookback window
            
        Returns:
            Dict: Pattern information
        """
        pattern_info = {
            'detected': False,
            'type': None,
            'strength': 0.0,
            'upper_line': None,
            'lower_line': None
        }
        
        # Implementation will be added in the next step
        return pattern_info

    def _generate_pattern_insights(self, recent_patterns):
        """Generate insights based on detected candlestick patterns."""
        if not recent_patterns:
            return ["No significant candlestick patterns detected in the recent price action."]
        
        insights = []
        
        # Check for most recent pattern first
        if recent_patterns:
            latest = recent_patterns[-1]
            date = latest['Date']
            patterns = latest['Patterns']
            
            pattern_str = ", ".join(patterns)
            insights.append(f"Most recent pattern(s) detected on {date}: {pattern_str}.")
            
            # Add specific insights based on patterns
            for pattern in patterns:
                if pattern == 'Doji':
                    insights.append("Doji pattern indicates market indecision, potential trend reversal.")
                elif pattern == 'Hammer':
                    insights.append("Hammer pattern suggests potential bullish reversal from a downtrend.")
                elif pattern == 'Shooting Star':
                    insights.append("Shooting Star pattern suggests potential bearish reversal from an uptrend.")
                elif pattern == 'Engulfing Bullish':
                    insights.append("Bullish Engulfing pattern indicates a potential upward reversal.")
                elif pattern == 'Engulfing Bearish':
                    insights.append("Bearish Engulfing pattern indicates a potential downward reversal.")
                elif pattern == 'Morning Star':
                    insights.append("Morning Star pattern signals a potential bullish reversal after a downtrend.")
                elif pattern == 'Evening Star':
                    insights.append("Evening Star pattern signals a potential bearish reversal after an uptrend.")
        
        # Check for pattern clusters or sequences
        bullish_count = sum(1 for p in recent_patterns for pattern in p['Patterns'] 
                          if pattern in ['Hammer', 'Engulfing Bullish', 'Morning Star'])
        bearish_count = sum(1 for p in recent_patterns for pattern in p['Patterns'] 
                          if pattern in ['Shooting Star', 'Engulfing Bearish', 'Evening Star'])
        
        if bullish_count > bearish_count:
            insights.append(f"Multiple bullish reversal patterns ({bullish_count}) have formed recently, suggesting potential upward movement.")
        elif bearish_count > bullish_count:
            insights.append(f"Multiple bearish reversal patterns ({bearish_count}) have formed recently, suggesting potential downward movement.")
        else:
            insights.append("Mixed candlestick patterns suggest market indecision.")
            
        return insights

    def _generate_chart_pattern_insights(self, chart_patterns):
        """Generate insights based on detected chart patterns."""
        if not chart_patterns:
            return ["No significant chart patterns detected in the recent price action."]
        
        insights = []
        
        for pattern_type, pattern_data in chart_patterns.items():
            if pattern_data is None:
                continue
                
            if pattern_type == 'Double_Top':
                insights.append(f"Double Top pattern detected at price level {pattern_data['Price_Level']:.2f} (peaks on {pattern_data['First_Peak_Date']} and {pattern_data['Second_Peak_Date']}), suggesting a potential bearish reversal.")
            
            elif pattern_type == 'Double_Bottom':
                insights.append(f"Double Bottom pattern detected at price level {pattern_data['Price_Level']:.2f} (troughs on {pattern_data['First_Trough_Date']} and {pattern_data['Second_Trough_Date']}), suggesting a potential bullish reversal.")
            
            elif pattern_type == 'Head_And_Shoulders':
                insights.append("Head and Shoulders pattern detected, suggesting a potential bearish reversal from an uptrend.")
            
            elif pattern_type == 'Inverse_Head_And_Shoulders':
                insights.append("Inverse Head and Shoulders pattern detected, suggesting a potential bullish reversal from a downtrend.")
            
            elif pattern_type == 'Triangle':
                if pattern_data.get('Type') == 'Ascending':
                    insights.append("Ascending Triangle pattern detected, typically a bullish continuation pattern.")
                elif pattern_data.get('Type') == 'Descending':
                    insights.append("Descending Triangle pattern detected, typically a bearish continuation pattern.")
                else:
                    insights.append("Symmetrical Triangle pattern detected, suggesting a period of consolidation before potential breakout.")
            
            elif pattern_type == 'Channel':
                if pattern_data.get('Type') == 'Ascending':
                    insights.append("Ascending Channel pattern detected, suggesting a continued uptrend.")
                elif pattern_data.get('Type') == 'Descending':
                    insights.append("Descending Channel pattern detected, suggesting a continued downtrend.")
                else:
                    insights.append("Horizontal Channel pattern detected, suggesting a trading range.")
        
        # Overall assessment
        bullish_patterns = sum(1 for _, data in chart_patterns.items() 
                             if data and data.get('Signal') == 'Bullish')
        bearish_patterns = sum(1 for _, data in chart_patterns.items() 
                             if data and data.get('Signal') == 'Bearish')
        
        if bullish_patterns > bearish_patterns:
            insights.append("Overall, the chart patterns suggest a bullish bias in the near term.")
        elif bearish_patterns > bullish_patterns:
            insights.append("Overall, the chart patterns suggest a bearish bias in the near term.")
        else:
            insights.append("The chart patterns show mixed signals without a clear directional bias.")
            
        return insights

    def visualize_patterns(self, symbol, save_path=None):
        """Visualize detected patterns on price chart."""
        try:
            # Load processed market data
            file_path = self.data_dir / 'market_data' / f"{symbol}_processed.csv"
            if not file_path.exists():
                logger.error(f"Processed market data file not found for {symbol}")
                return None

            df = pd.read_csv(file_path)

            # Convert date column to datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
            
            # Get the recent data (last 100 days)
            recent_data = df.tail(100).copy()
            
            # Load pattern analysis
            pattern_file = self.data_dir / 'analysis' / f"{symbol}_pattern_analysis.json"
            if not pattern_file.exists():
                logger.warning(f"Pattern analysis file not found for {symbol}, running detection first")
                pattern_analysis = self.detect_candlestick_patterns(symbol)
                if pattern_analysis is None:
                    return None
            else:
                with open(pattern_file, 'r') as f:
                    pattern_analysis = json.load(f)
            
            # Create plot
            plt.figure(figsize=(12, 6))
            plt.plot(recent_data.index, recent_data['Close'], 'b-', label='Close Price')
            
            # Add 20 and 50 day moving averages if available
            if '20d_MA' in recent_data.columns:
                plt.plot(recent_data.index, recent_data['20d_MA'], 'g-', label='20-day MA', alpha=0.7)
            if '50d_MA' in recent_data.columns:
                plt.plot(recent_data.index, recent_data['50d_MA'], 'r-', label='50-day MA', alpha=0.7)
            
            # Mark patterns on the chart
            for pattern in pattern_analysis.get('Detected_Patterns', []):
                pattern_date = datetime.strptime(pattern['Date'], '%Y-%m-%d')
                if pattern_date in recent_data.index:
                    price = recent_data.loc[pattern_date, 'Close']
                    pattern_names = ", ".join(pattern['Patterns'])
                    
                    # Determine marker color based on pattern type
                    if any(p in ['Hammer', 'Morning Star', 'Engulfing Bullish'] for p in pattern['Patterns']):
                        color = 'g'  # Green for bullish patterns
                    elif any(p in ['Shooting Star', 'Evening Star', 'Engulfing Bearish'] for p in pattern['Patterns']):
                        color = 'r'  # Red for bearish patterns
                    else:
                        color = 'y'  # Yellow for neutral patterns
                    
                    plt.scatter(pattern_date, price, color=color, s=100, zorder=5)
                    plt.annotate(pattern_names, xy=(pattern_date, price), 
                                xytext=(10, 10), textcoords='offset points',
                                fontsize=8, rotation=45, ha='left')
            
            # Add chart patterns if available
            chart_file = self.data_dir / 'analysis' / f"{symbol}_chart_pattern_analysis.json"
            if chart_file.exists():
                with open(chart_file, 'r') as f:
                    chart_analysis = json.load(f)
                
                for pattern_type, pattern_data in chart_analysis.get('Chart_Patterns', {}).items():
                    if pattern_data is None:
                        continue
                    
                    if pattern_type == 'Double_Top':
                        peak1_date = datetime.strptime(pattern_data['First_Peak_Date'], '%Y-%m-%d')
                        peak2_date = datetime.strptime(pattern_data['Second_Peak_Date'], '%Y-%m-%d')
                        price_level = pattern_data['Price_Level']
                        
                        if peak1_date in recent_data.index and peak2_date in recent_data.index:
                            plt.axhline(y=price_level, color='r', linestyle='--', alpha=0.5, 
                                       xmin=recent_data.index.get_loc(peak1_date)/len(recent_data),
                                       xmax=recent_data.index.get_loc(peak2_date)/len(recent_data))
                            plt.text(peak2_date, price_level*1.01, 'Double Top', color='r', fontsize=10)
                    
                    elif pattern_type == 'Double_Bottom':
                        trough1_date = datetime.strptime(pattern_data['First_Trough_Date'], '%Y-%m-%d')
                        trough2_date = datetime.strptime(pattern_data['Second_Trough_Date'], '%Y-%m-%d')
                        price_level = pattern_data['Price_Level']
                        
                        if trough1_date in recent_data.index and trough2_date in recent_data.index:
                            plt.axhline(y=price_level, color='g', linestyle='--', alpha=0.5,
                                       xmin=recent_data.index.get_loc(trough1_date)/len(recent_data),
                                       xmax=recent_data.index.get_loc(trough2_date)/len(recent_data))
                            plt.text(trough2_date, price_level*0.99, 'Double Bottom', color='g', fontsize=10)
            
            # Format plot
            plt.title(f'{symbol} - Price Chart with Detected Patterns')
            plt.xlabel('Date')
            plt.ylabel('Price')
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save or display
            if save_path:
                plt.savefig(save_path)
                logger.info(f"Pattern visualization saved to {save_path}")
            else:
                plt.show()
            
            return True

        except Exception as e:
            logger.error(f"Error visualizing patterns for {symbol}: {str(e)}")
            return None

    def analyze_patterns(self, symbol: str, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> Dict:
        """
        Analyze patterns in price data.
        
        Args:
            symbol (str): Stock symbol
            start_date (str, optional): Start date for analysis
            end_date (str, optional): End date for analysis
            
        Returns:
            Dict: Analysis results
        """
        try:
            # Load price data
            data_path = self.data_dir / f"{symbol}_price_data.csv"
            if not data_path.exists():
                self.logger.error(f"Price data not found for {symbol}")
                return {}
                
            data = pd.read_csv(data_path)
            data['Date'] = pd.to_datetime(data['Date'])
            data.set_index('Date', inplace=True)
            
            if start_date:
                data = data[data.index >= pd.to_datetime(start_date)]
            if end_date:
                data = data[data.index <= pd.to_datetime(end_date)]
                
            if len(data) < 30:  # Minimum data points required
                self.logger.error(f"Insufficient data points for {symbol}")
                return {}
                
            results = {
                'symbol': symbol,
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'candlestick_patterns': {},
                'chart_patterns': {},
                'trend_analysis': {},
                'pattern_clusters': [],
                'bullish_bias': 0.0,
                'bearish_bias': 0.0
            }
            
            # Analyze candlestick patterns
            for pattern_name, pattern_func in self.candlestick_patterns.items():
                pattern_results = []
                for i in range(1, len(data)):
                    if pattern_name in ['bullish_engulfing', 'bearish_engulfing', 'harami']:
                        detected, strength = pattern_func(
                            data.iloc[i-1]['Open'],
                            data.iloc[i-1]['Close'],
                            data.iloc[i]['Open'],
                            data.iloc[i]['Close']
                        )
                    elif pattern_name in ['morning_star', 'evening_star']:
                        detected, strength = pattern_func(data, i)
                    else:
                        detected, strength = pattern_func(
                            data.iloc[i]['Open'],
                            data.iloc[i]['High'],
                            data.iloc[i]['Low'],
                            data.iloc[i]['Close']
                        )
                        
                    if detected:
                        pattern_results.append({
                            'date': data.index[i],
                            'strength': strength
                        })
                        
                if pattern_results:
                    results['candlestick_patterns'][pattern_name] = pattern_results
                    
            # Analyze chart patterns
            for pattern_name, pattern_func in self.chart_patterns.items():
                pattern_info = pattern_func(data)
                if pattern_info['detected']:
                    results['chart_patterns'][pattern_name] = pattern_info
                    
            # Analyze trend
            results['trend_analysis'] = self._analyze_trend(data)
            
            # Find pattern clusters
            results['pattern_clusters'] = self._find_pattern_clusters(results)
            
            # Calculate bullish/bearish bias
            results['bullish_bias'], results['bearish_bias'] = self._calculate_bias(results)
            
            # Save results
            output_path = self.data_dir / 'analysis' / f"{symbol}_pattern_analysis.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=4, default=str)
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing patterns for {symbol}: {str(e)}")
            return {}

    def _analyze_trend(self, data: pd.DataFrame) -> Dict:
        """
        Analyze price trend.
        
        Args:
            data (pd.DataFrame): Price data
            
        Returns:
            Dict: Trend analysis results
        """
        # Calculate moving averages
        ma20 = data['Close'].rolling(window=20).mean()
        ma50 = data['Close'].rolling(window=50).mean()
        ma200 = data['Close'].rolling(window=200).mean()
        
        # Determine trend
        current_price = data['Close'].iloc[-1]
        trend = {
            'short_term': 'bullish' if current_price > ma20.iloc[-1] else 'bearish',
            'medium_term': 'bullish' if current_price > ma50.iloc[-1] else 'bearish',
            'long_term': 'bullish' if current_price > ma200.iloc[-1] else 'bearish'
        }
        
        # Calculate trend strength
        trend_strength = {
            'short_term': abs(current_price - ma20.iloc[-1]) / ma20.iloc[-1],
            'medium_term': abs(current_price - ma50.iloc[-1]) / ma50.iloc[-1],
            'long_term': abs(current_price - ma200.iloc[-1]) / ma200.iloc[-1]
        }
        
        return {
            'direction': trend,
            'strength': trend_strength,
            'moving_averages': {
                'ma20': ma20.iloc[-1],
                'ma50': ma50.iloc[-1],
                'ma200': ma200.iloc[-1]
            }
        }

    def _find_pattern_clusters(self, results: Dict) -> List[Dict]:
        """
        Find clusters of patterns occurring close to each other.
        
        Args:
            results (Dict): Pattern analysis results
            
        Returns:
            List[Dict]: Pattern clusters
        """
        clusters = []
        all_patterns = []
        
        # Collect all patterns with their dates
        for pattern_type, patterns in results['candlestick_patterns'].items():
            for pattern in patterns:
                all_patterns.append({
                    'type': pattern_type,
                    'date': pattern['date'],
                    'strength': pattern['strength']
                })
                
        for pattern_name, pattern_info in results['chart_patterns'].items():
            if pattern_info['detected']:
                all_patterns.append({
                    'type': pattern_name,
                    'date': pattern_info.get('date', pattern_info.get('end_date')),
                    'strength': pattern_info['strength']
                })
                
        # Sort patterns by date
        all_patterns.sort(key=lambda x: x['date'])
        
        # Find clusters (patterns within 5 days of each other)
        current_cluster = []
        for i in range(len(all_patterns)):
            if not current_cluster:
                current_cluster.append(all_patterns[i])
            else:
                last_date = current_cluster[-1]['date']
                current_date = all_patterns[i]['date']
                if (current_date - last_date).days <= 5:
                    current_cluster.append(all_patterns[i])
                else:
                    if len(current_cluster) >= 2:
                        clusters.append({
                            'patterns': current_cluster,
                            'start_date': current_cluster[0]['date'],
                            'end_date': current_cluster[-1]['date'],
                            'average_strength': sum(p['strength'] for p in current_cluster) / len(current_cluster)
                        })
                    current_cluster = [all_patterns[i]]
                    
        # Add last cluster if it exists
        if len(current_cluster) >= 2:
            clusters.append({
                'patterns': current_cluster,
                'start_date': current_cluster[0]['date'],
                'end_date': current_cluster[-1]['date'],
                'average_strength': sum(p['strength'] for p in current_cluster) / len(current_cluster)
            })
            
        return clusters

    def _calculate_bias(self, results: Dict) -> Tuple[float, float]:
        """
        Calculate bullish and bearish bias based on patterns.
        
        Args:
            results (Dict): Pattern analysis results
            
        Returns:
            Tuple[float, float]: (bullish_bias, bearish_bias)
        """
        bullish_patterns = {
            'hammer', 'bullish_engulfing', 'morning_star', 'piercing_pattern',
            'double_bottom', 'inverse_head_and_shoulders', 'cup_and_handle'
        }
        
        bearish_patterns = {
            'shooting_star', 'bearish_engulfing', 'evening_star', 'dark_cloud_cover',
            'double_top', 'head_and_shoulders'
        }
        
        bullish_strength = 0.0
        bearish_strength = 0.0
        total_strength = 0.0
        
        # Calculate bias from candlestick patterns
        for pattern_name, patterns in results['candlestick_patterns'].items():
            for pattern in patterns:
                if pattern_name in bullish_patterns:
                    bullish_strength += pattern['strength']
                elif pattern_name in bearish_patterns:
                    bearish_strength += pattern['strength']
                total_strength += pattern['strength']
                
        # Calculate bias from chart patterns
        for pattern_name, pattern_info in results['chart_patterns'].items():
            if pattern_info['detected']:
                if pattern_name in bullish_patterns:
                    bullish_strength += pattern_info['strength']
                elif pattern_name in bearish_patterns:
                    bearish_strength += pattern_info['strength']
                total_strength += pattern_info['strength']
                
        # Normalize biases
        if total_strength > 0:
            bullish_bias = bullish_strength / total_strength
            bearish_bias = bearish_strength / total_strength
        else:
            bullish_bias = 0.0
            bearish_bias = 0.0
            
        return bullish_bias, bearish_bias 