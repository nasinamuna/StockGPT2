from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from typing import List, Optional
import logging
from pathlib import Path
import json
from datetime import datetime
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ..analysis.market_data import MarketData
from ..analysis.technical_analysis import TechnicalAnalysis
from ..analysis.fundamental_analysis import FundamentalAnalysis
from ..analysis.sentiment_analysis import SentimentAnalysis
from ..prediction.price_prediction import PricePrediction

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="StockGPT API",
    description="API for stock market analysis and prediction",
    version="1.0.0"
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analysis modules
market_data = MarketData()
technical_analysis = TechnicalAnalysis()
fundamental_analysis = FundamentalAnalysis()
sentiment_analysis = SentimentAnalysis()
price_prediction = PricePrediction()

# API key security
api_key_header = APIKeyHeader(name="X-API-Key")

async def get_api_key(api_key: str = Depends(api_key_header)):
    """Validate API key."""
    # In production, implement proper API key validation
    if api_key != "your-api-key":  # Replace with actual API key validation
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.get("/")
@limiter.limit("5/minute")
async def root(request: Request):
    """Root endpoint."""
    return {"message": "Welcome to StockGPT API"}

@app.get("/stocks")
@limiter.limit("10/minute")
async def get_stocks(
    request: Request,
    symbol: Optional[str] = None,
    api_key: str = Depends(get_api_key)
):
    """Get stock data."""
    try:
        if symbol:
            # Get data for specific stock
            market_data_result = market_data.get_data(symbol)
            technical_result = technical_analysis.analyze(symbol)
            fundamental_result = fundamental_analysis.get_financial_data(symbol)
            sentiment_result = sentiment_analysis.get_sentiment_data(symbol)
            prediction_result = price_prediction.get_prediction(symbol)
            
            return {
                "market_data": market_data_result,
                "technical_analysis": technical_result,
                "fundamental_analysis": fundamental_result,
                "sentiment_analysis": sentiment_result,
                "price_prediction": prediction_result
            }
        else:
            # Get list of available stocks
            # In production, implement proper stock list retrieval
            return {"stocks": ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]}
            
    except Exception as e:
        logger.error(f"Error getting stock data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stock")
@limiter.limit("5/minute")
async def analyze_stock(
    request: Request,
    symbol: str,
    analysis_type: str,
    api_key: str = Depends(get_api_key)
):
    """Analyze stock with specific analysis type."""
    try:
        if analysis_type == "technical":
            result = technical_analysis.analyze(symbol)
        elif analysis_type == "fundamental":
            result = fundamental_analysis.get_financial_data(symbol)
        elif analysis_type == "sentiment":
            result = sentiment_analysis.get_sentiment_data(symbol)
        elif analysis_type == "prediction":
            result = price_prediction.get_prediction(symbol)
        else:
            raise HTTPException(status_code=400, detail="Invalid analysis type")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing stock: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stock/prediction")
@limiter.limit("5/minute")
async def predict_stock(
    request: Request,
    symbol: str,
    days: int = 30,
    api_key: str = Depends(get_api_key)
):
    """Get stock price prediction."""
    try:
        result = price_prediction.get_prediction(symbol, days)
        return result
        
    except Exception as e:
        logger.error(f"Error predicting stock: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Global error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 