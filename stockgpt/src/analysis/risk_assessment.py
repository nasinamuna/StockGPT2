import pandas as pd
import numpy as np
import logging
from pathlib import Path
import os
import json
from datetime import datetime, timedelta
import scipy.stats as stats

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RiskAssessment:
    def __init__(self, processed_data_dir='data/processed'):
        """Initialize the risk assessment module."""
        self.processed_data_dir = Path(processed_data_dir)
        
    def assess_market_risk(self, symbol, market_index='NIFTY50', lookback_period=252):
        """Assess market risk for a stock compared to a market index."""
        try:
            # Load processed market data for the stock
            stock_path = self.processed_data_dir / 'market_data' / f"{symbol}_processed.csv"
            if not stock_path.exists():
                logger.error(f"Processed market data file not found for {symbol}")
                return None
                
            stock_data = pd.read_csv(stock_path)
            
            # Convert date column to datetime
            if 'Date' in stock_data.columns:
                stock_data['Date'] = pd.to_datetime(stock_data['Date'])
                stock_data.set_index('Date', inplace=True)
            
            # Load processed market data for the index
            index_path = self.processed_data_dir / 'market_data' / f"{market_index}_processed.csv"
            if not index_path.exists():
                logger.error(f"Processed market data file not found for index {market_index}")
                return None
                
            index_data = pd.read_csv(index_path)
            
            # Convert date column to datetime
            if 'Date' in index_data.columns:
                index_data['Date'] = pd.to_datetime(index_data['Date'])
                index_data.set_index('Date', inplace=True)
            
            # Align dates between stock and index
            merged_data = pd.merge(
                stock_data['Close'], 
                index_data['Close'], 
                left_index=True, 
                right_index=True,
                suffixes=('_stock', '_index')
            )
            
            # Filter for lookback period
            if len(merged_data) > lookback_period:
                merged_data = merged_data.tail(lookback_period)
            
            # Calculate daily returns
            merged_data['Return_stock'] = merged_data['Close_stock'].pct_change().fillna(0)
            merged_data['Return_index'] = merged_data['Close_index'].pct_change().fillna(0)
            
            # Calculate beta (market risk)
            beta = self._calculate_beta(merged_data['Return_stock'], merged_data['Return_index'])
            
            # Calculate volatility
            volatility = merged_data['Return_stock'].std() * np.sqrt(252)  # Annualized
            
            # Calculate Sharpe ratio (assuming risk-free rate of 4%)
            risk_free_rate = 0.04
            excess_return = merged_data['Return_stock'].mean() * 252 - risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0
            
            # Calculate Value at Risk (VaR) - 95% confidence
            var_95 = self._calculate_var(merged_data['Return_stock'], confidence_level=0.95)
            
            # Calculate Maximum Drawdown
            max_drawdown = self._calculate_max_drawdown(merged_data['Close_stock'])
            
            # Calculate Correlation with index
            correlation = merged_data['Return_stock'].corr(merged_data['Return_index'])
            
            # Assemble results
            risk_assessment = {
                'Symbol': symbol,
                'Market_Index': market_index,
                'Analysis_Date': datetime.now().strftime('%Y-%m-%d'),
                'Beta': beta,
                'Annualized_Volatility': volatility,
                'Sharpe_Ratio': sharpe_ratio,
                'Value_at_Risk_95': var_95,
                'Maximum_Drawdown': max_drawdown,
                'Correlation_with_Index': correlation,
                'Risk_Level': self._determine_risk_level(beta, volatility, max_drawdown),
                'Insights': self._generate_risk_insights(beta, volatility, sharpe_ratio, var_95, max_drawdown, correlation)
            }
            
            # Save analysis
            output_path = self.processed_data_dir / 'analysis' / f"{symbol}_risk_assessment.json"
            os.makedirs(output_path.parent, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(risk_assessment, f, indent=4)
                
            logger.info(f"Risk assessment completed for {symbol}")
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Error performing risk assessment for {symbol}: {str(e)}")
            return None
    
    def _calculate_beta(self, stock_returns, index_returns):
        """Calculate beta (market risk) of a stock."""
        try:
            # Calculate covariance and variance
            covariance = stock_returns.cov(index_returns)
            variance = index_returns.var()
            
            # Calculate beta
            beta = covariance / variance if variance > 0 else 1.0
            
            return beta
            
        except Exception as e:
            logger.error(f"Error calculating beta: {str(e)}")
            return 1.0  # Default to market beta
    
    def _calculate_var(self, returns, confidence_level=0.95):
        """Calculate Value at Risk (VaR) at specified confidence level."""
        try:
            # Calculate VaR using historical method
            var = np.percentile(returns, 100 * (1 - confidence_level))
            
            # Convert to positive percentage for easier interpretation
            var = abs(var) * 100
            
            return var
            
        except Exception as e:
            logger.error(f"Error calculating VaR: {str(e)}")
            return None
    
    def _calculate_max_drawdown(self, prices):
        """Calculate maximum drawdown from a price series."""
        try:
            # Calculate the running maximum
            running_max = np.maximum.accumulate(prices)
            
            # Calculate the drawdown
            drawdown = (prices - running_max) / running_max
            
            # Get the maximum drawdown
            max_drawdown = abs(drawdown.min()) * 100  # Convert to percentage
            
            return max_drawdown
            
        except Exception as e:
            logger.error(f"Error calculating maximum drawdown: {str(e)}")
            return None
    
    def _determine_risk_level(self, beta, volatility, max_drawdown):
        """Determine overall risk level based on various metrics."""
        try:
            risk_score = 0
            
            # Beta contribution to risk score
            if beta >= 1.5:
                risk_score += 3  # High risk
            elif beta >= 1.2:
                risk_score += 2  # Medium-high risk
            elif beta >= 0.8:
                risk_score += 1  # Medium risk
            elif beta >= 0.5:
                risk_score += 0  # Medium-low risk
            else:
                risk_score -= 1  # Low risk
            
            # Volatility contribution to risk score
            if volatility >= 0.4:  # 40% annualized volatility
                risk_score += 3  # High risk
            elif volatility >= 0.3:
                risk_score += 2  # Medium-high risk
            elif volatility >= 0.2:
                risk_score += 1  # Medium risk
            elif volatility >= 0.1:
                risk_score += 0  # Medium-low risk
            else:
                risk_score -= 1  # Low risk
            
            # Drawdown contribution to risk score
            if max_drawdown >= 50:
                risk_score += 3  # High risk
            elif max_drawdown >= 30:
                risk_score += 2  # Medium-high risk
            elif max_drawdown >= 20:
                risk_score += 1  # Medium risk
            elif max_drawdown >= 10:
                risk_score += 0  # Medium-low risk
            else:
                risk_score -= 1  # Low risk
            
            # Determine risk level based on score
            if risk_score >= 6:
                return "Very High"
            elif risk_score >= 3:
                return "High"
            elif risk_score >= 0:
                return "Medium"
            elif risk_score >= -2:
                return "Low"
            else:
                return "Very Low"
                
        except Exception as e:
            logger.error(f"Error determining risk level: {str(e)}")
            return "Unknown"
    
    def _generate_risk_insights(self, beta, volatility, sharpe_ratio, var_95, max_drawdown, correlation):
        """Generate insights based on risk metrics."""
        insights = []
        
        # Beta insights
        if beta > 1.5:
            insights.append(f"The stock has a high beta of {beta:.2f}, indicating significantly more volatility than the market. It typically amplifies market movements by {beta:.2f}x.")
        elif beta > 1.0:
            insights.append(f"The stock has a beta of {beta:.2f}, indicating moderately more volatility than the market. It typically moves in the same direction as the market but with slightly larger swings.")
        elif beta > 0.8:
            insights.append(f"The stock has a beta of {beta:.2f}, indicating volatility similar to the market. It typically follows market trends closely.")
        elif beta > 0:
            insights.append(f"The stock has a low beta of {beta:.2f}, indicating less volatility than the market. It typically experiences smaller price swings than the overall market.")
        else:
            insights.append(f"The stock has a negative beta of {beta:.2f}, indicating it tends to move in the opposite direction of the market. This could provide diversification benefits.")
        
        # Volatility insights
        annualized_volatility_pct = volatility * 100
        if annualized_volatility_pct > 40:
            insights.append(f"The stock has extremely high volatility ({annualized_volatility_pct:.1f}% annualized), suggesting significant price swings and uncertainty.")
        elif annualized_volatility_pct > 30:
            insights.append(f"The stock has high volatility ({annualized_volatility_pct:.1f}% annualized), indicating substantial price fluctuations.")
        elif annualized_volatility_pct > 20:
            insights.append(f"The stock has moderate volatility ({annualized_volatility_pct:.1f}% annualized), with typical price movements for an individual stock.")
        else:
            insights.append(f"The stock has relatively low volatility ({annualized_volatility_pct:.1f}% annualized), suggesting more stable price behavior than average.")
        
        # Sharpe ratio insights
        if sharpe_ratio > 1.0:
            insights.append(f"The Sharpe ratio of {sharpe_ratio:.2f} indicates good risk-adjusted returns relative to the risk-free rate.")
        elif sharpe_ratio > 0:
            insights.append(f"The Sharpe ratio of {sharpe_ratio:.2f} indicates modest risk-adjusted returns relative to the risk-free rate.")
        else:
            insights.append(f"The negative Sharpe ratio of {sharpe_ratio:.2f} indicates that the stock has underperformed the risk-free rate on a risk-adjusted basis.")
        
        # VaR insights
        if var_95:
            insights.append(f"The 95% Value at Risk (VaR) is {var_95:.2f}%, meaning that with 95% confidence, the stock won't lose more than this percentage in a single day.")
        
        # Drawdown insights
        if max_drawdown:
            if max_drawdown > 50:
                insights.append(f"The stock has experienced an extreme maximum drawdown of {max_drawdown:.1f}%, suggesting significant downside risk during adverse market conditions.")
            elif max_drawdown > 30:
                insights.append(f"The stock has experienced a large maximum drawdown of {max_drawdown:.1f}%, indicating substantial downside risk during market downturns.")
            elif max_drawdown > 20:
                insights.append(f"The stock has experienced a moderate maximum drawdown of {max_drawdown:.1f}%, typical for an average stock during market corrections.")
            else:
                insights.append(f"The stock has experienced a relatively small maximum drawdown of {max_drawdown:.1f}%, suggesting better downside protection than average.")
        
        # Correlation insights
        if correlation > 0.8:
            insights.append(f"The stock shows strong correlation ({correlation:.2f}) with the market index, indicating limited diversification benefits.")
        elif correlation > 0.5:
            insights.append(f"The stock shows moderate correlation ({correlation:.2f}) with the market index, offering some diversification benefits.")
        elif correlation > 0:
            insights.append(f"The stock shows low correlation ({correlation:.2f}) with the market index, offering good diversification benefits.")
        else:
            insights.append(f"The stock shows negative correlation ({correlation:.2f}) with the market index, potentially offering excellent diversification benefits.")
        
        return insights
    
    def assess_credit_risk(self, symbol):
        """Assess credit and financial health risk for a company."""
        # Implementation for credit risk assessment
        # ...
        return None
    
    def assess_geopolitical_risk(self, symbol):
        """Assess geopolitical and regulatory risk for a company."""
        # Implementation for geopolitical risk assessment
        # ...
        return None 