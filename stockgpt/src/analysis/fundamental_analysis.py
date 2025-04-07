import pandas as pd
import numpy as np
import yfinance as yf
import logging
from pathlib import Path
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FundamentalAnalysis:
    def __init__(self, cache_dir: str = "data/processed/financial_statements"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=24)  # Cache TTL of 24 hours
        self.logger = logging.getLogger(__name__)
        self.metrics = {
            'profitability': {
                'gross_margin': self._calculate_gross_margin,
                'operating_margin': self._calculate_operating_margin,
                'net_margin': self._calculate_net_margin,
                'roa': self._calculate_roa,
                'roe': self._calculate_roe,
                'roic': self._calculate_roic
            },
            'liquidity': {
                'current_ratio': self._calculate_current_ratio,
                'quick_ratio': self._calculate_quick_ratio,
                'cash_ratio': self._calculate_cash_ratio
            },
            'leverage': {
                'debt_to_equity': self._calculate_debt_to_equity,
                'interest_coverage': self._calculate_interest_coverage,
                'debt_to_assets': self._calculate_debt_to_assets
            },
            'efficiency': {
                'asset_turnover': self._calculate_asset_turnover,
                'inventory_turnover': self._calculate_inventory_turnover,
                'receivables_turnover': self._calculate_receivables_turnover
            },
            'valuation': {
                'pe_ratio': self._calculate_pe_ratio,
                'pb_ratio': self._calculate_pb_ratio,
                'ps_ratio': self._calculate_ps_ratio,
                'ev_ebitda': self._calculate_ev_ebitda
            }
        }
    
    def analyze(self, symbol: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform fundamental analysis for a stock.
        
        Args:
            symbol (str): Stock symbol
            data (dict): Stock data including financial statements
            
        Returns:
            dict: Fundamental analysis results
        """
        try:
            # Get financial statements
            financials = self._get_financial_statements(symbol, data)
            if not financials:
                logger.error(f"Could not get financial statements for {symbol}")
                return None
            
            # Calculate metrics
            metrics_result = {}
            for category, category_metrics in self.metrics.items():
                metrics_result[category] = {}
                for metric_name, metric_func in category_metrics.items():
                    metrics_result[category][metric_name] = metric_func(financials)
            
            # Get industry comparison
            industry_comparison = self._get_industry_comparison(symbol, metrics_result)
            
            # Generate analysis text
            analysis_text = self._generate_analysis_text(metrics_result, industry_comparison)
            
            # Generate signals
            signals = self._generate_signals(metrics_result, industry_comparison)
            
            # Combine all analyses
            fundamental_analysis = {
                'symbol': symbol,
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'metrics': metrics_result,
                'industry_comparison': industry_comparison,
                'analysis': analysis_text,
                'signals': signals,
                'recommendation': self._generate_recommendation(signals)
            }
            
            # Save analysis
            output_path = self.cache_dir / 'analysis' / f"{symbol}_fundamental_analysis.json"
            os.makedirs(output_path.parent, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(fundamental_analysis, f, indent=4)
            
            logger.info(f"Fundamental analysis completed for {symbol}")
            return fundamental_analysis
            
        except Exception as e:
            logger.error(f"Error performing fundamental analysis for {symbol}: {str(e)}")
            return None
    
    def _get_financial_statements(self, symbol: str, data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """Get financial statements from data or fetch from Yahoo Finance"""
        try:
            financials = {}
            
            # Try to get from provided data
            if 'financial_statements' in data:
                financials = data['financial_statements']
            else:
                # Fetch from Yahoo Finance
                stock = yf.Ticker(symbol)
                
                # Get income statement
                income_stmt = stock.financials
                if not income_stmt.empty:
                    financials['income_statement'] = income_stmt
                
                # Get balance sheet
                balance_sheet = stock.balance_sheet
                if not balance_sheet.empty:
                    financials['balance_sheet'] = balance_sheet
                
                # Get cash flow statement
                cash_flow = stock.cashflow
                if not cash_flow.empty:
                    financials['cash_flow'] = cash_flow
            
            return financials
            
        except Exception as e:
            logger.error(f"Error getting financial statements for {symbol}: {str(e)}")
            return None
    
    def _calculate_gross_margin(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate gross margin"""
        try:
            income_stmt = financials.get('income_statement')
            if income_stmt is None or income_stmt.empty:
                return None
            
            gross_profit = income_stmt.loc['Gross Profit']
            revenue = income_stmt.loc['Total Revenue']
            
            gross_margin = (gross_profit / revenue) * 100
            
            return {
                'value': gross_margin.iloc[0],
                'history': gross_margin.tolist(),
                'description': 'Gross Margin (%)'
            }
        except Exception as e:
            logger.error(f"Error calculating gross margin: {str(e)}")
            return None
    
    def _calculate_operating_margin(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate operating margin"""
        try:
            income_stmt = financials.get('income_statement')
            if income_stmt is None or income_stmt.empty:
                return None
            
            operating_income = income_stmt.loc['Operating Income']
            revenue = income_stmt.loc['Total Revenue']
            
            operating_margin = (operating_income / revenue) * 100
            
            return {
                'value': operating_margin.iloc[0],
                'history': operating_margin.tolist(),
                'description': 'Operating Margin (%)'
            }
        except Exception as e:
            logger.error(f"Error calculating operating margin: {str(e)}")
            return None
    
    def _calculate_net_margin(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate net margin"""
        try:
            income_stmt = financials.get('income_statement')
            if income_stmt is None or income_stmt.empty:
                return None
            
            net_income = income_stmt.loc['Net Income']
            revenue = income_stmt.loc['Total Revenue']
            
            net_margin = (net_income / revenue) * 100
            
            return {
                'value': net_margin.iloc[0],
                'history': net_margin.tolist(),
                'description': 'Net Margin (%)'
            }
        except Exception as e:
            logger.error(f"Error calculating net margin: {str(e)}")
            return None
    
    def _calculate_roa(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Return on Assets"""
        try:
            income_stmt = financials.get('income_statement')
            balance_sheet = financials.get('balance_sheet')
            if income_stmt is None or balance_sheet is None:
                return None
            
            net_income = income_stmt.loc['Net Income']
            total_assets = balance_sheet.loc['Total Assets']
            
            roa = (net_income / total_assets) * 100
            
            return {
                'value': roa.iloc[0],
                'history': roa.tolist(),
                'description': 'Return on Assets (%)'
            }
        except Exception as e:
            logger.error(f"Error calculating ROA: {str(e)}")
            return None
    
    def _calculate_roe(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Return on Equity"""
        try:
            income_stmt = financials.get('income_statement')
            balance_sheet = financials.get('balance_sheet')
            if income_stmt is None or balance_sheet is None:
                return None
            
            net_income = income_stmt.loc['Net Income']
            total_equity = balance_sheet.loc['Total Stockholder Equity']
            
            roe = (net_income / total_equity) * 100
            
            return {
                'value': roe.iloc[0],
                'history': roe.tolist(),
                'description': 'Return on Equity (%)'
            }
        except Exception as e:
            logger.error(f"Error calculating ROE: {str(e)}")
            return None
    
    def _calculate_roic(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Return on Invested Capital"""
        try:
            income_stmt = financials.get('income_statement')
            balance_sheet = financials.get('balance_sheet')
            if income_stmt is None or balance_sheet is None:
                return None
            
            nopat = income_stmt.loc['Operating Income'] * (1 - 0.21)  # Assuming 21% tax rate
            invested_capital = balance_sheet.loc['Total Assets'] - balance_sheet.loc['Total Current Liabilities']
            
            roic = (nopat / invested_capital) * 100
            
            return {
                'value': roic.iloc[0],
                'history': roic.tolist(),
                'description': 'Return on Invested Capital (%)'
            }
        except Exception as e:
            logger.error(f"Error calculating ROIC: {str(e)}")
            return None
    
    def _calculate_current_ratio(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Current Ratio"""
        try:
            balance_sheet = financials.get('balance_sheet')
            if balance_sheet is None:
                return None
            
            current_assets = balance_sheet.loc['Total Current Assets']
            current_liabilities = balance_sheet.loc['Total Current Liabilities']
            
            current_ratio = current_assets / current_liabilities
            
            return {
                'value': current_ratio.iloc[0],
                'history': current_ratio.tolist(),
                'description': 'Current Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating current ratio: {str(e)}")
            return None
    
    def _calculate_quick_ratio(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Quick Ratio"""
        try:
            balance_sheet = financials.get('balance_sheet')
            if balance_sheet is None:
                return None
            
            current_assets = balance_sheet.loc['Total Current Assets']
            inventory = balance_sheet.loc['Inventory']
            current_liabilities = balance_sheet.loc['Total Current Liabilities']
            
            quick_ratio = (current_assets - inventory) / current_liabilities
            
            return {
                'value': quick_ratio.iloc[0],
                'history': quick_ratio.tolist(),
                'description': 'Quick Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating quick ratio: {str(e)}")
            return None
    
    def _calculate_cash_ratio(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Cash Ratio"""
        try:
            balance_sheet = financials.get('balance_sheet')
            if balance_sheet is None:
                return None
            
            cash = balance_sheet.loc['Cash']
            current_liabilities = balance_sheet.loc['Total Current Liabilities']
            
            cash_ratio = cash / current_liabilities
            
            return {
                'value': cash_ratio.iloc[0],
                'history': cash_ratio.tolist(),
                'description': 'Cash Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating cash ratio: {str(e)}")
            return None
    
    def _calculate_debt_to_equity(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Debt to Equity Ratio"""
        try:
            balance_sheet = financials.get('balance_sheet')
            if balance_sheet is None:
                return None
            
            total_debt = balance_sheet.loc['Total Debt']
            total_equity = balance_sheet.loc['Total Stockholder Equity']
            
            debt_to_equity = total_debt / total_equity
            
            return {
                'value': debt_to_equity.iloc[0],
                'history': debt_to_equity.tolist(),
                'description': 'Debt to Equity Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating debt to equity ratio: {str(e)}")
            return None
    
    def _calculate_interest_coverage(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Interest Coverage Ratio"""
        try:
            income_stmt = financials.get('income_statement')
            if income_stmt is None:
                return None
            
            ebit = income_stmt.loc['Operating Income']
            interest_expense = income_stmt.loc['Interest Expense']
            
            interest_coverage = ebit / interest_expense
            
            return {
                'value': interest_coverage.iloc[0],
                'history': interest_coverage.tolist(),
                'description': 'Interest Coverage Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating interest coverage ratio: {str(e)}")
            return None
    
    def _calculate_debt_to_assets(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Debt to Assets Ratio"""
        try:
            balance_sheet = financials.get('balance_sheet')
            if balance_sheet is None:
                return None
            
            total_debt = balance_sheet.loc['Total Debt']
            total_assets = balance_sheet.loc['Total Assets']
            
            debt_to_assets = total_debt / total_assets
            
            return {
                'value': debt_to_assets.iloc[0],
                'history': debt_to_assets.tolist(),
                'description': 'Debt to Assets Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating debt to assets ratio: {str(e)}")
            return None
    
    def _calculate_asset_turnover(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Asset Turnover Ratio"""
        try:
            income_stmt = financials.get('income_statement')
            balance_sheet = financials.get('balance_sheet')
            if income_stmt is None or balance_sheet is None:
                return None
            
            revenue = income_stmt.loc['Total Revenue']
            total_assets = balance_sheet.loc['Total Assets']
            
            asset_turnover = revenue / total_assets
            
            return {
                'value': asset_turnover.iloc[0],
                'history': asset_turnover.tolist(),
                'description': 'Asset Turnover Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating asset turnover ratio: {str(e)}")
            return None
    
    def _calculate_inventory_turnover(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Inventory Turnover Ratio"""
        try:
            income_stmt = financials.get('income_statement')
            balance_sheet = financials.get('balance_sheet')
            if income_stmt is None or balance_sheet is None:
                return None
            
            cogs = income_stmt.loc['Cost Of Revenue']
            inventory = balance_sheet.loc['Inventory']
            
            inventory_turnover = cogs / inventory
            
            return {
                'value': inventory_turnover.iloc[0],
                'history': inventory_turnover.tolist(),
                'description': 'Inventory Turnover Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating inventory turnover ratio: {str(e)}")
            return None
    
    def _calculate_receivables_turnover(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Receivables Turnover Ratio"""
        try:
            income_stmt = financials.get('income_statement')
            balance_sheet = financials.get('balance_sheet')
            if income_stmt is None or balance_sheet is None:
                return None
            
            revenue = income_stmt.loc['Total Revenue']
            receivables = balance_sheet.loc['Net Receivables']
            
            receivables_turnover = revenue / receivables
            
            return {
                'value': receivables_turnover.iloc[0],
                'history': receivables_turnover.tolist(),
                'description': 'Receivables Turnover Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating receivables turnover ratio: {str(e)}")
            return None
    
    def _calculate_pe_ratio(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Price to Earnings Ratio"""
        try:
            income_stmt = financials.get('income_statement')
            if income_stmt is None:
                return None
            
            net_income = income_stmt.loc['Net Income']
            shares_outstanding = income_stmt.loc['Basic Average Shares']
            
            eps = net_income / shares_outstanding
            pe_ratio = 1 / eps  # Assuming price is 1 for ratio calculation
            
            return {
                'value': pe_ratio.iloc[0],
                'history': pe_ratio.tolist(),
                'description': 'Price to Earnings Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating P/E ratio: {str(e)}")
            return None
    
    def _calculate_pb_ratio(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Price to Book Ratio"""
        try:
            balance_sheet = financials.get('balance_sheet')
            if balance_sheet is None:
                return None
            
            total_equity = balance_sheet.loc['Total Stockholder Equity']
            shares_outstanding = balance_sheet.loc['Common Stock']
            
            book_value_per_share = total_equity / shares_outstanding
            pb_ratio = 1 / book_value_per_share  # Assuming price is 1 for ratio calculation
            
            return {
                'value': pb_ratio.iloc[0],
                'history': pb_ratio.tolist(),
                'description': 'Price to Book Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating P/B ratio: {str(e)}")
            return None
    
    def _calculate_ps_ratio(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Price to Sales Ratio"""
        try:
            income_stmt = financials.get('income_statement')
            if income_stmt is None:
                return None
            
            revenue = income_stmt.loc['Total Revenue']
            shares_outstanding = income_stmt.loc['Basic Average Shares']
            
            sales_per_share = revenue / shares_outstanding
            ps_ratio = 1 / sales_per_share  # Assuming price is 1 for ratio calculation
            
            return {
                'value': ps_ratio.iloc[0],
                'history': ps_ratio.tolist(),
                'description': 'Price to Sales Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating P/S ratio: {str(e)}")
            return None
    
    def _calculate_ev_ebitda(self, financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate Enterprise Value to EBITDA Ratio"""
        try:
            income_stmt = financials.get('income_statement')
            balance_sheet = financials.get('balance_sheet')
            if income_stmt is None or balance_sheet is None:
                return None
            
            ebitda = income_stmt.loc['EBITDA']
            total_debt = balance_sheet.loc['Total Debt']
            cash = balance_sheet.loc['Cash']
            
            ev = total_debt - cash  # Simplified EV calculation
            ev_ebitda = ev / ebitda
            
            return {
                'value': ev_ebitda.iloc[0],
                'history': ev_ebitda.tolist(),
                'description': 'Enterprise Value to EBITDA Ratio'
            }
        except Exception as e:
            logger.error(f"Error calculating EV/EBITDA ratio: {str(e)}")
            return None
    
    def _get_industry_comparison(self, symbol: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Get industry comparison data"""
        try:
            # This is a simplified implementation
            # In a real application, you would fetch industry averages from a database or API
            
            # Mock industry averages
            industry_averages = {
                'profitability': {
                    'gross_margin': 40.0,
                    'operating_margin': 15.0,
                    'net_margin': 10.0,
                    'roa': 8.0,
                    'roe': 15.0,
                    'roic': 12.0
                },
                'liquidity': {
                    'current_ratio': 2.0,
                    'quick_ratio': 1.5,
                    'cash_ratio': 0.5
                },
                'leverage': {
                    'debt_to_equity': 1.0,
                    'interest_coverage': 5.0,
                    'debt_to_assets': 0.5
                },
                'efficiency': {
                    'asset_turnover': 1.0,
                    'inventory_turnover': 6.0,
                    'receivables_turnover': 8.0
                },
                'valuation': {
                    'pe_ratio': 20.0,
                    'pb_ratio': 3.0,
                    'ps_ratio': 2.0,
                    'ev_ebitda': 15.0
                }
            }
            
            comparison = {}
            for category, category_metrics in metrics.items():
                comparison[category] = {}
                for metric_name, metric_data in category_metrics.items():
                    if metric_data is None:
                        continue
                    
                    company_value = metric_data['value']
                    industry_avg = industry_averages[category][metric_name]
                    
                    comparison[category][metric_name] = {
                        'company_value': company_value,
                        'industry_average': industry_avg,
                        'difference': company_value - industry_avg,
                        'difference_percent': ((company_value - industry_avg) / industry_avg) * 100
                    }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error getting industry comparison for {symbol}: {str(e)}")
            return None
    
    def _generate_analysis_text(self, metrics: Dict[str, Any], industry_comparison: Dict[str, Any]) -> List[str]:
        """Generate analysis text based on metrics and industry comparison"""
        analysis = []
        
        # Add profitability analysis
        if 'profitability' in metrics:
            analysis.append("Profitability Analysis:")
            for metric_name, metric_data in metrics['profitability'].items():
                if metric_data is None:
                    continue
                
                value = metric_data['value']
                industry_comp = industry_comparison.get('profitability', {}).get(metric_name)
                
                if industry_comp:
                    diff = industry_comp['difference_percent']
                    if diff > 0:
                        analysis.append(f"- {metric_data['description']}: {value:.2f} (Above industry average by {diff:.1f}%)")
                    else:
                        analysis.append(f"- {metric_data['description']}: {value:.2f} (Below industry average by {abs(diff):.1f}%)")
                else:
                    analysis.append(f"- {metric_data['description']}: {value:.2f}")
        
        # Add liquidity analysis
        if 'liquidity' in metrics:
            analysis.append("\nLiquidity Analysis:")
            for metric_name, metric_data in metrics['liquidity'].items():
                if metric_data is None:
                    continue
                
                value = metric_data['value']
                industry_comp = industry_comparison.get('liquidity', {}).get(metric_name)
                
                if industry_comp:
                    diff = industry_comp['difference_percent']
                    if diff > 0:
                        analysis.append(f"- {metric_data['description']}: {value:.2f} (Above industry average by {diff:.1f}%)")
                    else:
                        analysis.append(f"- {metric_data['description']}: {value:.2f} (Below industry average by {abs(diff):.1f}%)")
                else:
                    analysis.append(f"- {metric_data['description']}: {value:.2f}")
        
        # Add leverage analysis
        if 'leverage' in metrics:
            analysis.append("\nLeverage Analysis:")
            for metric_name, metric_data in metrics['leverage'].items():
                if metric_data is None:
                    continue
                
                value = metric_data['value']
                industry_comp = industry_comparison.get('leverage', {}).get(metric_name)
                
                if industry_comp:
                    diff = industry_comp['difference_percent']
                    if diff > 0:
                        analysis.append(f"- {metric_data['description']}: {value:.2f} (Above industry average by {diff:.1f}%)")
                    else:
                        analysis.append(f"- {metric_data['description']}: {value:.2f} (Below industry average by {abs(diff):.1f}%)")
                else:
                    analysis.append(f"- {metric_data['description']}: {value:.2f}")
        
        # Add efficiency analysis
        if 'efficiency' in metrics:
            analysis.append("\nEfficiency Analysis:")
            for metric_name, metric_data in metrics['efficiency'].items():
                if metric_data is None:
                    continue
                
                value = metric_data['value']
                industry_comp = industry_comparison.get('efficiency', {}).get(metric_name)
                
                if industry_comp:
                    diff = industry_comp['difference_percent']
                    if diff > 0:
                        analysis.append(f"- {metric_data['description']}: {value:.2f} (Above industry average by {diff:.1f}%)")
                    else:
                        analysis.append(f"- {metric_data['description']}: {value:.2f} (Below industry average by {abs(diff):.1f}%)")
                else:
                    analysis.append(f"- {metric_data['description']}: {value:.2f}")
        
        # Add valuation analysis
        if 'valuation' in metrics:
            analysis.append("\nValuation Analysis:")
            for metric_name, metric_data in metrics['valuation'].items():
                if metric_data is None:
                    continue
                
                value = metric_data['value']
                industry_comp = industry_comparison.get('valuation', {}).get(metric_name)
                
                if industry_comp:
                    diff = industry_comp['difference_percent']
                    if diff > 0:
                        analysis.append(f"- {metric_data['description']}: {value:.2f} (Above industry average by {diff:.1f}%)")
                    else:
                        analysis.append(f"- {metric_data['description']}: {value:.2f} (Below industry average by {abs(diff):.1f}%)")
                else:
                    analysis.append(f"- {metric_data['description']}: {value:.2f}")
        
        return analysis
    
    def _generate_signals(self, metrics: Dict[str, Any], industry_comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signals based on metrics and industry comparison"""
        signals = {
            'strength': 0,
            'direction': 'Neutral',
            'confidence': 'Low'
        }
        
        # Calculate signal strength
        strength = 0
        direction = 0
        
        # Add profitability signals
        if 'profitability' in metrics:
            for metric_data in metrics['profitability'].values():
                if metric_data is None:
                    continue
                
                value = metric_data['value']
                if 'roa' in metric_data['description'].lower():
                    if value > 10:
                        strength += 1
                        direction += 1
                    elif value < 5:
                        strength += 1
                        direction -= 1
                elif 'roe' in metric_data['description'].lower():
                    if value > 15:
                        strength += 1
                        direction += 1
                    elif value < 10:
                        strength += 1
                        direction -= 1
        
        # Add liquidity signals
        if 'liquidity' in metrics:
            for metric_data in metrics['liquidity'].values():
                if metric_data is None:
                    continue
                
                value = metric_data['value']
                if 'current_ratio' in metric_data['description'].lower():
                    if value > 2:
                        strength += 0.5
                        direction += 0.5
                    elif value < 1:
                        strength += 0.5
                        direction -= 0.5
        
        # Add leverage signals
        if 'leverage' in metrics:
            for metric_data in metrics['leverage'].values():
                if metric_data is None:
                    continue
                
                value = metric_data['value']
                if 'debt_to_equity' in metric_data['description'].lower():
                    if value < 1:
                        strength += 0.5
                        direction += 0.5
                    elif value > 2:
                        strength += 0.5
                        direction -= 0.5
        
        # Add valuation signals
        if 'valuation' in metrics:
            for metric_data in metrics['valuation'].values():
                if metric_data is None:
                    continue
                
                value = metric_data['value']
                if 'pe_ratio' in metric_data['description'].lower():
                    if value < 15:
                        strength += 1
                        direction += 1
                    elif value > 25:
                        strength += 1
                        direction -= 1
        
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