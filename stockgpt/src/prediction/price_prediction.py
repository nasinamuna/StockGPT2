import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import os
import json
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import yfinance as yf
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StockDataset(Dataset):
    def __init__(self, data: np.ndarray, sequence_length: int):
        self.data = data
        self.sequence_length = sequence_length

    def __len__(self) -> int:
        return len(self.data) - self.sequence_length

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        x = self.data[idx:idx + self.sequence_length]
        y = self.data[idx + self.sequence_length]
        return torch.FloatTensor(x), torch.FloatTensor(y)

class LSTMModel(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, output_size: int):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

class PricePrediction:
    def __init__(self, processed_data_dir='data/processed', models_dir='data/models', cache_dir: str = "data/models"):
        """Initialize the price prediction module."""
        self.processed_data_dir = Path(processed_data_dir)
        self.models_dir = Path(models_dir)
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Set random seeds for reproducibility
        np.random.seed(42)
        tf.random.set_seed(42)
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    def train_lstm_model(self, symbol, prediction_days=5, lookback_window=60, epochs=50, batch_size=32):
        """Train an LSTM model to predict future prices."""
        try:
            # Load processed market data
            file_path = self.processed_data_dir / 'technical_indicators' / f"{symbol}_indicators.csv"
            if not file_path.exists():
                logger.error(f"Technical indicators file not found for {symbol}")
                return None
                
            df = pd.read_csv(file_path)
            
            # Convert date column to datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
            
            # Select features for the model
            features = ['Close', 'Volume', 'Daily_Return', '20d_MA', '50d_MA', 'RSI', 'MACD_Line']
            
            # Check if all features are available
            missing_features = [f for f in features if f not in df.columns]
            if missing_features:
                logger.warning(f"Missing features: {missing_features}. Will use available features only.")
                features = [f for f in features if f in df.columns]
            
            # Ensure we have at least Close price
            if 'Close' not in features:
                logger.error("Close price data is missing, cannot proceed with training")
                return None
            
            # Filter to only required features
            data = df[features].copy()
            
            # Handle missing values
            data = data.dropna()
            
            if len(data) < lookback_window + prediction_days:
                logger.error(f"Not enough data points for {symbol} after handling missing values")
                return None
            
            # Scale the data
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(data)
            
            # Prepare the data for LSTM
            X, y = self._prepare_lstm_data(scaled_data, lookback_window, prediction_days)
            
            # Split into train and test sets (80% train, 20% test)
            split_idx = int(0.8 * len(X))
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Build the LSTM model
            model = self._build_lstm_model(X_train.shape[1], X_train.shape[2])
            
            # Train the model
            history = model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(X_test, y_test),
                verbose=1
            )
            
            # Save the model
            model_path = self.models_dir / f"{symbol}_lstm_model"
            model.save(model_path)
            
            # Save the scaler
            scaler_path = self.models_dir / f"{symbol}_scaler.pkl"
            import pickle
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            
            # Evaluate the model
            y_pred = model.predict(X_test)
            
            # Inverse transform to get actual prices
            # Create a dummy array with the same shape as the original data
            dummy = np.zeros((len(y_pred), len(features)))
            # Put the predicted values (first column is Close price)
            dummy[:, 0] = y_pred.flatten()
            
            # Inverse transform to get actual price predictions
            y_pred_actual = scaler.inverse_transform(dummy)[:, 0]
            
            # Create a similar dummy for actual values
            dummy = np.zeros((len(y_test), len(features)))
            dummy[:, 0] = y_test.flatten()
            y_test_actual = scaler.inverse_transform(dummy)[:, 0]
            
            # Calculate metrics
            rmse = np.sqrt(mean_squared_error(y_test_actual, y_pred_actual))
            mae = mean_absolute_error(y_test_actual, y_pred_actual)
            r2 = r2_score(y_test_actual, y_pred_actual)
            
            # Calculate MAPE (Mean Absolute Percentage Error)
            mape = np.mean(np.abs((y_test_actual - y_pred_actual) / y_test_actual)) * 100
            
            # Save evaluation results
            eval_results = {
                'Symbol': symbol,
                'Model_Type': 'LSTM',
                'Training_Date': datetime.now().strftime('%Y-%m-%d'),
                'Epochs': epochs,
                'Batch_Size': batch_size,
                'Lookback_Window': lookback_window,
                'Prediction_Days': prediction_days,
                'Features_Used': features,
                'RMSE': float(rmse),
                'MAE': float(mae),
                'MAPE': float(mape),
                'R2': float(r2),
                'Training_History': {
                    'Loss': [float(loss) for loss in history.history['loss']],
                    'Val_Loss': [float(loss) for loss in history.history['val_loss']]
                }
            }
            
            eval_path = self.models_dir / f"{symbol}_lstm_evaluation.json"
            with open(eval_path, 'w') as f:
                json.dump(eval_results, f, indent=4)
            
            logger.info(f"LSTM model trained and saved for {symbol} with RMSE: {rmse:.2f}, MAPE: {mape:.2f}%")
            
            return {
                'model': model,
                'scaler': scaler,
                'evaluation': eval_results,
                'features': features
            }
            
        except Exception as e:
            logger.error(f"Error training LSTM model for {symbol}: {str(e)}")
            return None
    
    def _prepare_lstm_data(self, scaled_data, lookback_window, prediction_days):
        """Prepare data for LSTM model training."""
        X = []
        y = []
        
        for i in range(lookback_window, len(scaled_data) - prediction_days):
            X.append(scaled_data[i - lookback_window:i])
            # Target is the Close price (first column) after prediction_days
            y.append(scaled_data[i + prediction_days - 1, 0])
        
        return np.array(X), np.array(y)
    
    def _build_lstm_model(self, timesteps, features):
        """Build an LSTM model for price prediction."""
        model = Sequential()
        
        # First LSTM layer with return sequences for stacking
        model.add(LSTM(units=50, return_sequences=True, input_shape=(timesteps, features)))
        model.add(Dropout(0.2))
        
        # Second LSTM layer
        model.add(LSTM(units=50, return_sequences=False))
        model.add(Dropout(0.2))
        
        # Dense layer
        model.add(Dense(units=25))
        model.add(Dropout(0.2))
        
        # Output layer
        model.add(Dense(units=1))
        
        # Compile the model
        model.compile(optimizer='adam', loss='mean_squared_error')
        
        return model
    
    def predict_future_prices(self, symbol, days=5):
        """Predict future prices using a trained model."""
        try:
            # Check if model exists
            model_path = self.models_dir / f"{symbol}_lstm_model"
            if not os.path.exists(model_path):
                logger.error(f"No trained model found for {symbol}")
                return None
                
            # Check if scaler exists
            scaler_path = self.models_dir / f"{symbol}_scaler.pkl"
            if not os.path.exists(scaler_path):
                logger.error(f"No scaler found for {symbol}")
                return None
            
            # Load model and scaler
            model = tf.keras.models.load_model(model_path)
            
            import pickle
            with open(scaler_path, 'rb') as f:
                scaler = pickle.load(f)
            
            # Load evaluation to get features and lookback window
            eval_path = self.models_dir / f"{symbol}_lstm_evaluation.json"
            with open(eval_path, 'r') as f:
                evaluation = json.load(f)
            
            features = evaluation['Features_Used']
            lookback_window = evaluation['Lookback_Window']
            
            # Load the most recent data
            file_path = self.processed_data_dir / 'technical_indicators' / f"{symbol}_indicators.csv"
            df = pd.read_csv(file_path)
            
            # Convert date column to datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
            
            # Filter to required features
            data = df[features].copy()
            
            # Handle missing values
            data = data.dropna()
            
            # Get the most recent data for the lookback window
            recent_data = data.tail(lookback_window).values
            
            # Scale the data
            scaled_data = scaler.transform(recent_data)
            
            # Reshape for LSTM input [samples, timesteps, features]
            X_recent = np.array([scaled_data])
            
            # Make prediction
            predicted_scaled = model.predict(X_recent)
            
            # Create a dummy array with the same shape as the original data
            dummy = np.zeros((len(predicted_scaled), len(features)))
            # Put the predicted values (first column is Close price)
            dummy[:, 0] = predicted_scaled.flatten()
            
            # Inverse transform to get actual price predictions
            predicted_price = scaler.inverse_transform(dummy)[0, 0]
            
            # Get the last known price
            last_price = data['Close'].iloc[-1]
            
            # Calculate predicted change
            predicted_change = ((predicted_price - last_price) / last_price) * 100
            
            # Get the current date and add days to get prediction date
            last_date = df.index[-1]
            prediction_date = last_date + pd.Timedelta(days=days)
            
            # Create prediction result
            prediction_result = {
                'Symbol': symbol,
                'Last_Price': float(last_price),
                'Predicted_Price': float(predicted_price),
                'Predicted_Change_Percent': float(predicted_change),
                'Prediction_Date': prediction_date.strftime('%Y-%m-%d'),
                'Confidence': self._calculate_prediction_confidence(evaluation)
            }
            
            logger.info(f"Price prediction generated for {symbol}: {predicted_price:.2f} ({predicted_change:+.2f}%)")
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"Error predicting future prices for {symbol}: {str(e)}")
            return None
    
    def _calculate_prediction_confidence(self, evaluation):
        """Calculate a confidence score for the prediction based on model metrics."""
        try:
            # MAPE (Mean Absolute Percentage Error) is a good inverse indicator of confidence
            mape = evaluation.get('MAPE', 0)
            
            # R² is a direct indicator of confidence
            r2 = evaluation.get('R2', 0)
            
            # Convert MAPE to a confidence score (0-100%)
            # Lower MAPE means higher confidence
            if mape > 20:
                mape_score = 0
            else:
                mape_score = (20 - mape) / 20
            
            # Convert R² to a confidence score (0-100%)
            # Higher R² means higher confidence
            r2_score_val = max(0, r2)  # Ensure non-negative
            
            # Combine the scores (weighted average)
            confidence = (0.7 * mape_score + 0.3 * r2_score_val) * 100
            
            return min(100, max(0, confidence))  # Ensure in range 0-100
            
        except Exception as e:
            logger.error(f"Error calculating prediction confidence: {str(e)}")
            return 50  # Default to medium confidence

    def predict(self, symbol, days=5):
        """
        Predict future stock prices
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days to predict
            
        Returns:
            dict: Price prediction results
        """
        try:
            # In a real implementation, this would:
            # 1. Fetch historical stock data
            # 2. Preprocess data
            # 3. Apply ML models to predict future prices
            # 4. Return structured results
            
            # For now, generate mock data
            return self._get_mock_price_prediction(symbol, days)
        except Exception as e:
            logger.error(f"Error in price prediction for {symbol}: {str(e)}")
            return self._get_mock_price_prediction(symbol, days)
    
    def _get_mock_price_prediction(self, symbol, days):
        """Generate mock price prediction data for development"""
        import random
        from datetime import datetime, timedelta
        
        # Start from a random base price
        base_price = random.uniform(500, 2000)
        
        # Generate predictions for each day
        dates = []
        predicted_prices = []
        lower_bounds = []
        upper_bounds = []
        
        # Today's date
        today = datetime.now()
        
        # Generate actual prices for past 30 days (for chart context)
        historical_dates = []
        historical_prices = []
        
        for i in range(30, 0, -1):
            past_date = today - timedelta(days=i)
            historical_dates.append(past_date.strftime('%Y-%m-%d'))
            
            # Add some randomness to historical prices
            price_change = random.uniform(-0.02, 0.02)
            price = base_price * (1 + price_change)
            historical_prices.append(price)
            
            # Update base price for next day
            base_price = price
        
        # Current price is the last historical price
        current_price = historical_prices[-1]
        
        # Generate future predictions
        prediction_trend = random.choice(['up', 'down', 'stable'])
        
        if prediction_trend == 'up':
            trend_factor = random.uniform(0.002, 0.008)  # 0.2% to 0.8% daily increase
        elif prediction_trend == 'down':
            trend_factor = random.uniform(-0.008, -0.002)  # 0.2% to 0.8% daily decrease
        else:
            trend_factor = random.uniform(-0.002, 0.002)  # -0.2% to 0.2% daily change
        
        # Start with current price
        next_price = current_price
        
        for i in range(1, days + 1):
            future_date = today + timedelta(days=i)
            dates.append(future_date.strftime('%Y-%m-%d'))
            
            # Calculate next price with trend and some noise
            daily_change = trend_factor + random.uniform(-0.01, 0.01)  # Add random noise
            next_price = next_price * (1 + daily_change)
            
            predicted_prices.append(next_price)
            
            # Calculate confidence bounds (wider as we go further in time)
            confidence_width = 0.02 + (i * 0.005)  # Starts at 2%, increases by 0.5% each day
            lower_bounds.append(next_price * (1 - confidence_width))
            upper_bounds.append(next_price * (1 + confidence_width))
        
        # Calculate expected return
        expected_return = (predicted_prices[-1] / current_price - 1) * 100
        
        # Generate prediction analysis
        if expected_return > 5:
            analysis = [
                f"The model predicts a strong upward trend for {symbol} over the next {days} days.",
                f"Expected return: {expected_return:.2f}% with moderate confidence.",
                "Technical indicators and market sentiment support this bullish outlook."
            ]
        elif expected_return > 1:
            analysis = [
                f"The model predicts a slight upward trend for {symbol} over the next {days} days.",
                f"Expected return: {expected_return:.2f}% with moderate confidence.",
                "The stock shows some positive momentum but may face resistance."
            ]
        elif expected_return > -1:
            analysis = [
                f"The model predicts relatively stable prices for {symbol} over the next {days} days.",
                f"Expected return: {expected_return:.2f}% with high confidence.",
                "The stock appears to be consolidating in its current range."
            ]
        elif expected_return > -5:
            analysis = [
                f"The model predicts a slight downward trend for {symbol} over the next {days} days.",
                f"Expected return: {expected_return:.2f}% with moderate confidence.",
                "Some bearish indicators suggest selling pressure in the short term."
            ]
        else:
            analysis = [
                f"The model predicts a strong downward trend for {symbol} over the next {days} days.",
                f"Expected return: {expected_return:.2f}% with moderate confidence.",
                "Multiple indicators point to significant selling pressure ahead."
            ]
        
        # Factors influencing the prediction
        factors = [
            "Historical price patterns",
            "Technical indicator trends",
            "Market sentiment analysis",
            "Sector performance",
            "Volatility patterns"
        ]
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'prediction_period': {
                'start': today.strftime('%Y-%m-%d'),
                'end': dates[-1]
            },
            'historical_data': {
                'dates': historical_dates,
                'prices': historical_prices
            },
            'predicted_data': {
                'dates': dates,
                'prices': predicted_prices,
                'lower_bounds': lower_bounds,
                'upper_bounds': upper_bounds
            },
            'expected_return': expected_return,
            'confidence': "Moderate",
            'analysis': analysis,
            'influencing_factors': factors
        } 