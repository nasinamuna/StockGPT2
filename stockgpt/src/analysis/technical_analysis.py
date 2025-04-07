import pandas as pd
import numpy as np
import talib
import logging
from pathlib import Path
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import mplfinance as mpf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechnicalAnalysis:
    def __init__(self, processed_data_dir: str = "data/processed"):
        """
        Initialize the technical analysis module.
        
        Args:
            processed_data_dir (str): Directory containing processed data
        """
        self.processed_data_dir = Path(processed_data_dir)
        self.indicators = {
            'SMA20': {'function': self._calculate_sma, 'params': {'period': 20}},
            'SMA50': {'function': self._calculate_sma, 'params': {'period': 50}},
            'SMA200': {'function': self._calculate_sma, 'params': {'period': 200}},
            'EMA20': {'function': self._calculate_ema, 'params': {'period': 20}},
            'RSI': {'function': self._calculate_rsi, 'params': {'period': 14}},
            'MACD': {'function': self._calculate_macd, 'params': {}},
            'Bollinger': {'function': self._calculate_bollinger, 'params': {'period': 20, 'deviation': 2}},
            'Stochastic': {'function': self._calculate_stochastic, 'params': {'k_period': 14, 'd_period': 3}},
            'ADX': {'function': self._calculate_adx, 'params': {'period': 14}},
            'ATR': {'function': self._calculate_atr, 'params': {'period': 14}}
        }
        
    def analyze(self, symbol: str, data: Dict[str, Any], period: str = 'short') -> Dict[str, Any]:
        """
        Perform technical analysis for a stock.
        
        Args:
            symbol (str): Stock symbol
            data (dict): Stock data including price history
            period (str): Analysis period ('short', 'medium', 'long')
            
        Returns:
            dict: Technical analysis results
        """
        try:
            # Convert price history to DataFrame
            df = pd.DataFrame(data['price_history'])
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
            
            # Get appropriate timeframe based on period
            if period == 'short':
                df = df.tail(30)  # Last 30 trading days
            elif period == 'medium':
                df = df.tail(90)  # Last 90 trading days
            elif period == 'long':
                df = df.tail(252)  # Last year of trading
            
            # Calculate indicators
            indicators_result = {}
            for name, config in self.indicators.items():
                indicators_result[name] = config['function'](df, **config['params'])
            
            # Detect patterns
            patterns = self._detect_patterns(df)
            
            # Generate analysis text
            analysis_text = self._generate_analysis_text(indicators_result, patterns)
            
            # Generate signals
            signals = self._generate_signals(indicators_result, patterns)
            
            # Generate visualization
            chart_path = self._generate_chart(symbol, df, indicators_result, period)
            
            # Combine all analyses
            technical_analysis = {
                'symbol': symbol,
                'period': period,
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'indicators': indicators_result,
                'patterns': patterns,
                'analysis': analysis_text,
                'signals': signals,
                'recommendation': self._generate_recommendation(signals),
                'chart_path': chart_path
            }
            
            # Save analysis
            output_path = self.processed_data_dir / 'analysis' / f"{symbol}_technical_analysis_{period}.json"
            os.makedirs(output_path.parent, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(technical_analysis, f, indent=4)
            
            logger.info(f"Technical analysis completed for {symbol} ({period} term)")
            return technical_analysis
            
        except Exception as e:
            logger.error(f"Error performing technical analysis for {symbol}: {str(e)}")
            return None
    
    def _calculate_sma(self, df: pd.DataFrame, period: int) -> Dict[str, Any]:
        """Calculate Simple Moving Average"""
        try:
            close_prices = df['Close'].values
            sma = talib.SMA(close_prices, timeperiod=period)
            current_sma = sma[-1] if not np.isnan(sma[-1]) else None
            
            # Calculate trend
            trend = "Up" if current_sma > sma[-2] else "Down" if current_sma < sma[-2] else "Flat"
            
            return {
                'value': current_sma,
                'history': sma.tolist(),
                'trend': trend,
                'description': f'Simple Moving Average ({period} days)'
            }
        except Exception as e:
            logger.error(f"Error calculating SMA: {str(e)}")
            return None
    
    def _calculate_ema(self, df: pd.DataFrame, period: int) -> Dict[str, Any]:
        """Calculate Exponential Moving Average"""
        try:
            close_prices = df['Close'].values
            ema = talib.EMA(close_prices, timeperiod=period)
            current_ema = ema[-1] if not np.isnan(ema[-1]) else None
            
            # Calculate trend
            trend = "Up" if current_ema > ema[-2] else "Down" if current_ema < ema[-2] else "Flat"
            
            return {
                'value': current_ema,
                'history': ema.tolist(),
                'trend': trend,
                'description': f'Exponential Moving Average ({period} days)'
            }
        except Exception as e:
            logger.error(f"Error calculating EMA: {str(e)}")
            return None
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int) -> Dict[str, Any]:
        """Calculate Relative Strength Index"""
        try:
            close_prices = df['Close'].values
            rsi = talib.RSI(close_prices, timeperiod=period)
            current_rsi = rsi[-1] if not np.isnan(rsi[-1]) else None
            
            # Interpret RSI
            if current_rsi is None:
                interpretation = "Unknown"
            elif current_rsi > 70:
                interpretation = "Overbought"
            elif current_rsi < 30:
                interpretation = "Oversold"
            else:
                interpretation = "Neutral"
            
            return {
                'value': current_rsi,
                'history': rsi.tolist(),
                'interpretation': interpretation,
                'description': f'Relative Strength Index ({period} days)'
            }
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return None
    
    def _calculate_macd(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate MACD"""
        try:
            close_prices = df['Close'].values
            macd, macd_signal, macd_hist = talib.MACD(
                close_prices, fastperiod=12, slowperiod=26, signalperiod=9
            )
            
            current_macd = macd[-1] if not np.isnan(macd[-1]) else None
            current_signal = macd_signal[-1] if not np.isnan(macd_signal[-1]) else None
            current_hist = macd_hist[-1] if not np.isnan(macd_hist[-1]) else None
            
            # Interpret MACD
            if current_macd is None or current_signal is None:
                interpretation = "Unknown"
            elif current_macd > current_signal:
                interpretation = "Bullish"
            else:
                interpretation = "Bearish"
            
            return {
                'macd': current_macd,
                'signal': current_signal,
                'histogram': current_hist,
                'macd_history': macd.tolist(),
                'signal_history': macd_signal.tolist(),
                'histogram_history': macd_hist.tolist(),
                'interpretation': interpretation,
                'description': 'Moving Average Convergence Divergence'
            }
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
            return None
    
    def _calculate_bollinger(self, df: pd.DataFrame, period: int, deviation: float) -> Dict[str, Any]:
        """Calculate Bollinger Bands"""
        try:
            close_prices = df['Close'].values
            upper, middle, lower = talib.BBANDS(
                close_prices, timeperiod=period, nbdevup=deviation, nbdevdn=deviation
            )
            
            current_upper = upper[-1] if not np.isnan(upper[-1]) else None
            current_middle = middle[-1] if not np.isnan(middle[-1]) else None
            current_lower = lower[-1] if not np.isnan(lower[-1]) else None
            current_price = close_prices[-1]
            
            # Interpret Bollinger Bands
            if current_upper is None or current_lower is None or current_price is None:
                interpretation = "Unknown"
            elif current_price > current_upper:
                interpretation = "Overbought"
            elif current_price < current_lower:
                interpretation = "Oversold"
            else:
                interpretation = "Within normal range"
            
            return {
                'upper': current_upper,
                'middle': current_middle,
                'lower': current_lower,
                'upper_history': upper.tolist(),
                'middle_history': middle.tolist(),
                'lower_history': lower.tolist(),
                'interpretation': interpretation,
                'description': f'Bollinger Bands ({period} days, {deviation}σ)'
            }
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {str(e)}")
            return None
    
    def _calculate_stochastic(self, df: pd.DataFrame, k_period: int, d_period: int) -> Dict[str, Any]:
        """Calculate Stochastic Oscillator"""
        try:
            high = df['High'].values
            low = df['Low'].values
            close = df['Close'].values
            
            slowk, slowd = talib.STOCH(high, low, close, 
                                     fastk_period=k_period,
                                     slowk_period=d_period,
                                     slowk_matype=0,
                                     slowd_period=d_period,
                                     slowd_matype=0)
            
            current_k = slowk[-1] if not np.isnan(slowk[-1]) else None
            current_d = slowd[-1] if not np.isnan(slowd[-1]) else None
            
            # Interpret Stochastic
            if current_k is None or current_d is None:
                interpretation = "Unknown"
            elif current_k > 80 and current_d > 80:
                interpretation = "Overbought"
            elif current_k < 20 and current_d < 20:
                interpretation = "Oversold"
            else:
                interpretation = "Neutral"
            
            return {
                'k_line': current_k,
                'd_line': current_d,
                'k_history': slowk.tolist(),
                'd_history': slowd.tolist(),
                'interpretation': interpretation,
                'description': f'Stochastic Oscillator ({k_period},{d_period})'
            }
        except Exception as e:
            logger.error(f"Error calculating Stochastic: {str(e)}")
            return None
    
    def _calculate_adx(self, df: pd.DataFrame, period: int) -> Dict[str, Any]:
        """Calculate Average Directional Index"""
        try:
            high = df['High'].values
            low = df['Low'].values
            close = df['Close'].values
            
            adx = talib.ADX(high, low, close, timeperiod=period)
            current_adx = adx[-1] if not np.isnan(adx[-1]) else None
            
            # Interpret ADX
            if current_adx is None:
                interpretation = "Unknown"
            elif current_adx > 25:
                interpretation = "Strong Trend"
            elif current_adx > 20:
                interpretation = "Moderate Trend"
            else:
                interpretation = "Weak Trend"
            
            return {
                'value': current_adx,
                'history': adx.tolist(),
                'interpretation': interpretation,
                'description': f'Average Directional Index ({period} days)'
            }
        except Exception as e:
            logger.error(f"Error calculating ADX: {str(e)}")
            return None
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> Dict[str, Any]:
        """Calculate Average True Range"""
        try:
            high = df['High'].values
            low = df['Low'].values
            close = df['Close'].values
            
            atr = talib.ATR(high, low, close, timeperiod=period)
            current_atr = atr[-1] if not np.isnan(atr[-1]) else None
            
            return {
                'value': current_atr,
                'history': atr.tolist(),
                'description': f'Average True Range ({period} days)'
            }
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return None
    
    def _detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect candlestick and chart patterns"""
        patterns = {
            'candlestick': [],
            'chart': []
        }
        
        try:
            # Detect candlestick patterns
            open_prices = df['Open'].values
            high_prices = df['High'].values
            low_prices = df['Low'].values
            close_prices = df['Close'].values
            
            # Check for common candlestick patterns
            for pattern in ['CDLDOJI', 'CDLHAMMER', 'CDLSHOOTINGSTAR', 
                          'CDLENGULFING', 'CDLMORNINGSTAR', 'CDLEVENINGSTAR']:
                pattern_func = getattr(talib, pattern)
                result = pattern_func(open_prices, high_prices, low_prices, close_prices)
                
                if result[-1] != 0:  # Pattern detected on last candle
                    patterns['candlestick'].append({
                        'name': pattern[3:].lower(),  # Remove 'CDL' prefix
                        'strength': abs(result[-1]),
                        'direction': 'Bullish' if result[-1] > 0 else 'Bearish'
                    })
            
            # Detect chart patterns (simplified)
            if len(df) >= 20:  # Need enough data for pattern detection
                # Check for double top/bottom
                peaks, _ = self._find_peaks(df['Close'].values)
                if len(peaks) >= 2:
                    if self._is_double_top(peaks[-2:]):
                        patterns['chart'].append({
                            'name': 'double_top',
                            'strength': 0.8,
                            'direction': 'Bearish'
                        })
                    elif self._is_double_bottom(peaks[-2:]):
                        patterns['chart'].append({
                            'name': 'double_bottom',
                            'strength': 0.8,
                            'direction': 'Bullish'
                        })
                
                # Check for head and shoulders
                if len(peaks) >= 3:
                    if self._is_head_and_shoulders(peaks[-3:]):
                        patterns['chart'].append({
                            'name': 'head_and_shoulders',
                            'strength': 0.9,
                            'direction': 'Bearish'
                        })
                    elif self._is_inverse_head_and_shoulders(peaks[-3:]):
                        patterns['chart'].append({
                            'name': 'inverse_head_and_shoulders',
                            'strength': 0.9,
                            'direction': 'Bullish'
                        })
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {str(e)}")
        
        return patterns
    
    def _find_peaks(self, data: np.ndarray, order: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """Find peaks and troughs in the data"""
        peaks = []
        troughs = []
        
        for i in range(order, len(data) - order):
            if all(data[i] > data[i-j] for j in range(1, order+1)) and \
               all(data[i] > data[i+j] for j in range(1, order+1)):
                peaks.append(i)
            elif all(data[i] < data[i-j] for j in range(1, order+1)) and \
                 all(data[i] < data[i+j] for j in range(1, order+1)):
                troughs.append(i)
        
        return np.array(peaks), np.array(troughs)
    
    def _is_double_top(self, peaks: List[int]) -> bool:
        """Check if the last two peaks form a double top pattern"""
        if len(peaks) < 2:
            return False
        
        p1, p2 = peaks[-2:]
        return abs(p1 - p2) / p1 < 0.02  # Within 2% of each other
    
    def _is_double_bottom(self, troughs: List[int]) -> bool:
        """Check if the last two troughs form a double bottom pattern"""
        if len(troughs) < 2:
            return False
        
        t1, t2 = troughs[-2:]
        return abs(t1 - t2) / t1 < 0.02  # Within 2% of each other
    
    def _is_head_and_shoulders(self, peaks: List[int]) -> bool:
        """Check if the last three peaks form a head and shoulders pattern"""
        if len(peaks) < 3:
            return False
        
        left, head, right = peaks[-3:]
        return head > left and head > right and abs(left - right) / left < 0.02
    
    def _is_inverse_head_and_shoulders(self, troughs: List[int]) -> bool:
        """Check if the last three troughs form an inverse head and shoulders pattern"""
        if len(troughs) < 3:
            return False
        
        left, head, right = troughs[-3:]
        return head < left and head < right and abs(left - right) / left < 0.02
    
    def _generate_analysis_text(self, indicators: Dict[str, Any], patterns: Dict[str, Any]) -> List[str]:
        """Generate analysis text based on indicators and patterns"""
        analysis = []
        
        # Add indicator analysis
        for name, indicator in indicators.items():
            if indicator is None:
                continue
                
            if 'interpretation' in indicator:
                analysis.append(f"{name}: {indicator['interpretation']}")
            elif 'trend' in indicator:
                analysis.append(f"{name} Trend: {indicator['trend']}")
        
        # Add pattern analysis
        if patterns['candlestick']:
            analysis.append("Candlestick Patterns:")
            for pattern in patterns['candlestick']:
                analysis.append(f"- {pattern['name'].title()} ({pattern['direction']})")
        
        if patterns['chart']:
            analysis.append("Chart Patterns:")
            for pattern in patterns['chart']:
                analysis.append(f"- {pattern['name'].replace('_', ' ').title()} ({pattern['direction']})")
        
        return analysis
    
    def _generate_signals(self, indicators: Dict[str, Any], patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signals based on indicators and patterns"""
        signals = {
            'strength': 0,
            'direction': 'Neutral',
            'confidence': 'Low'
        }
        
        # Calculate signal strength
        strength = 0
        direction = 0
        
        # Add indicator signals
        for indicator in indicators.values():
            if indicator is None:
                continue
                
            if 'interpretation' in indicator:
                if indicator['interpretation'] == 'Bullish':
                    strength += 1
                    direction += 1
                elif indicator['interpretation'] == 'Bearish':
                    strength += 1
                    direction -= 1
            elif 'trend' in indicator:
                if indicator['trend'] == 'Up':
                    strength += 0.5
                    direction += 0.5
                elif indicator['trend'] == 'Down':
                    strength += 0.5
                    direction -= 0.5
        
        # Add pattern signals
        for pattern in patterns['candlestick'] + patterns['chart']:
            strength += pattern['strength']
            direction += pattern['strength'] if pattern['direction'] == 'Bullish' else -pattern['strength']
        
        # Normalize strength and direction
        if strength > 0:
            signals['strength'] = min(strength / 5, 1)  # Normalize to 0-1
            signals['direction'] = 'Bullish' if direction > 0 else 'Bearish' if direction < 0 else 'Neutral'
            signals['confidence'] = 'High' if strength >= 3 else 'Medium' if strength >= 1.5 else 'Low'
        
        return signals
    
    def _generate_recommendation(self, signals: Dict[str, Any]) -> str:
        """Generate trading recommendation based on signals"""
        if signals['strength'] == 0:
            return "No clear trading signal"
        
        action = "Buy" if signals['direction'] == 'Bullish' else "Sell" if signals['direction'] == 'Bearish' else "Hold"
        confidence = signals['confidence']
        
        return f"{action} (Confidence: {confidence})"
    
    def _generate_chart(self, symbol: str, df: pd.DataFrame, 
                       indicators: Dict[str, Any], period: str) -> str:
        """Generate technical analysis chart"""
        try:
            # Create chart directory if it doesn't exist
            chart_dir = self.processed_data_dir / 'charts'
            chart_dir.mkdir(exist_ok=True)
            
            # Prepare data for mplfinance
            df_plot = df.copy()
            df_plot.index = pd.to_datetime(df_plot.index)
            
            # Create additional plots
            apds = []
            
            # Add moving averages
            if 'SMA20' in indicators and indicators['SMA20'] is not None:
                apds.append(mpf.make_addplot(indicators['SMA20']['history'], color='blue', width=0.7))
            if 'SMA50' in indicators and indicators['SMA50'] is not None:
                apds.append(mpf.make_addplot(indicators['SMA50']['history'], color='orange', width=0.7))
            
            # Add Bollinger Bands
            if 'Bollinger' in indicators and indicators['Bollinger'] is not None:
                bb = indicators['Bollinger']
                apds.append(mpf.make_addplot(bb['upper_history'], color='gray', width=0.7))
                apds.append(mpf.make_addplot(bb['middle_history'], color='gray', width=0.7))
                apds.append(mpf.make_addplot(bb['lower_history'], color='gray', width=0.7))
            
            # Generate chart
            chart_path = chart_dir / f"{symbol}_technical_{period}.png"
            
            mpf.plot(df_plot, type='candle', style='charles',
                    title=f"{symbol} Technical Analysis ({period} term)",
                    ylabel='Price',
                    volume=True,
                    addplot=apds,
                    savefig=chart_path)
            
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
            return None 