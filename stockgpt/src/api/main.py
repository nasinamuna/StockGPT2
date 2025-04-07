from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict
from ..mock_implementations import (
    MarketData,
    TechnicalAnalysis,
    FundamentalAnalysis,
    SentimentAnalysis,
    PricePrediction
)
from pydantic import BaseModel

router = APIRouter()

# Mock stock data
MOCK_STOCKS = {
    "RELIANCE": {"name": "Reliance Industries Ltd.", "sector": "Energy"},
    "TCS": {"name": "Tata Consultancy Services Ltd.", "sector": "Technology"},
    "HDFCBANK": {"name": "HDFC Bank Ltd.", "sector": "Banking"},
    "INFY": {"name": "Infosys Ltd.", "sector": "Technology"},
    "SBIN": {"name": "State Bank of India", "sector": "Banking"},
    "IRFC": {"name": "Indian Railway Finance Corporation", "sector": "Finance"}
}

# Define data models for API requests and responses
class StockAnalysisRequest(BaseModel):
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    analysis_type: Optional[List[str]] = ["fundamental", "technical", "sentiment"]

class StockPredictionRequest(BaseModel):
    symbol: str
    days: Optional[int] = 5

# Get stock data endpoint
@router.get("/stocks", response_model=Dict[str, Dict])
async def get_stocks():
    """Get list of available stocks"""
    return MOCK_STOCKS

# Get detailed stock analysis
@router.post("/api/stock/analyze", response_model=Dict)
async def analyze_stock(request: StockAnalysisRequest):
    try:
        # Initialize analysis components
        market_data = MarketData()
        stock_data = market_data.get_stock_data(request.symbol, request.start_date, request.end_date)
        
        response = {"symbol": request.symbol, "data": {}}
        
        # Perform requested analyses
        if "fundamental" in request.analysis_type:
            fundamental = FundamentalAnalysis()
            response["data"]["fundamental"] = fundamental.analyze(request.symbol)
            
        if "technical" in request.analysis_type:
            technical = TechnicalAnalysis()
            response["data"]["technical"] = technical.analyze(request.symbol)
            
        if "sentiment" in request.analysis_type:
            sentiment = SentimentAnalysis()
            response["data"]["sentiment"] = sentiment.analyze(request.symbol)
        
        # Add basic stock info
        response["data"]["info"] = {
            "name": MOCK_STOCKS.get(request.symbol, {}).get("name", "Unknown"),
            "sector": MOCK_STOCKS.get(request.symbol, {}).get("sector", "Unknown"),
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get stock prediction
@router.post("/api/stock/predict", response_model=Dict)
async def predict_stock(request: StockPredictionRequest):
    try:
        predictor = PricePrediction()
        prediction_data = predictor.predict(request.symbol, request.days)
        return {"symbol": request.symbol, "prediction": prediction_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get technical analysis
@router.get("/api/stock/{symbol}/technical", response_model=Dict)
async def get_technical_analysis(symbol: str):
    try:
        technical = TechnicalAnalysis()
        return technical.analyze(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get fundamental analysis
@router.get("/api/stock/{symbol}/fundamental", response_model=Dict)
async def get_fundamental_analysis(symbol: str):
    try:
        fundamental = FundamentalAnalysis()
        return fundamental.analyze(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get sentiment analysis
@router.get("/api/stock/{symbol}/sentiment", response_model=Dict)
async def get_sentiment_analysis(symbol: str):
    try:
        sentiment = SentimentAnalysis()
        return sentiment.analyze(symbol)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 