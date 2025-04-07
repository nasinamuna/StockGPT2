import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import fastapi
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from pydantic import BaseModel

from .analysis import (
    MarketData,
    TechnicalAnalysis,
    FundamentalAnalysis,
    SentimentAnalysis,
)
from .prediction import PricePrediction

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="StockGPT",
    description="An integrated platform for Indian stock market analysis",
    version="1.0.0"
)

# Setup CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directory structure if it doesn't exist
base_dir = Path(__file__).parent.parent
data_dir = base_dir / "data"
processed_dir = data_dir / "processed"
analysis_dir = processed_dir / "analysis"

for directory in [data_dir, processed_dir, analysis_dir]:
    os.makedirs(directory, exist_ok=True)

# Set up templates directory for HTML rendering
templates_dir = base_dir / "templates"
static_dir = base_dir / "static"

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Initialize analysis modules
market_data = MarketData()
technical_analysis = TechnicalAnalysis()
fundamental_analysis = FundamentalAnalysis()
sentiment_analysis = SentimentAnalysis()
price_prediction = PricePrediction()

# Mock stock data
MOCK_STOCKS = {
    "RELIANCE": {"name": "Reliance Industries Ltd.", "sector": "Energy"},
    "TCS": {"name": "Tata Consultancy Services Ltd.", "sector": "Technology"},
    "HDFCBANK": {"name": "HDFC Bank Ltd.", "sector": "Banking"},
    "INFY": {"name": "Infosys Ltd.", "sector": "Technology"},
    "SBIN": {"name": "State Bank of India", "sector": "Banking"}
}

# API Models
class StockModel(BaseModel):
    symbol: str

class StockAnalysisRequest(BaseModel):
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    analysis_type: Optional[List[str]] = ["Fundamental", "Technical", "Sentiment"]

class StockPredictionRequest(BaseModel):
    symbol: str
    days: Optional[int] = 5

# API Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Include from API routes
@app.get("/stocks")
async def get_stocks():
    """Get list of available stocks"""
    return MOCK_STOCKS

@app.post("/api/stock")
async def analyze_stock(request: StockAnalysisRequest):
    """Perform stock analysis"""
    try:
        symbol = request.symbol
        
        # Get stock data
        stock_data = market_data.get_data(symbol)
        
        # Initialize response
        response = {
            "symbol": symbol,
            "data": {
                "info": {
                    "name": MOCK_STOCKS.get(symbol, {}).get("name", "Unknown Company"),
                    "sector": MOCK_STOCKS.get(symbol, {}).get("sector", "Unknown Sector"),
                }
            }
        }
        
        # Add requested analyses
        if "Fundamental" in request.analysis_type:
            response["data"]["fundamental"] = fundamental_analysis.analyze(symbol, stock_data)
            
        if "Technical" in request.analysis_type:
            response["data"]["technical"] = technical_analysis.analyze(symbol, stock_data)
            
        if "Sentiment" in request.analysis_type:
            response["data"]["sentiment"] = sentiment_analysis.analyze(symbol)
        
        return response
    except Exception as e:
        logger.error(f"Error analyzing stock: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stock/prediction")
async def predict_stock(request: StockPredictionRequest):
    """Generate stock price predictions"""
    try:
        prediction_data = price_prediction.predict(request.symbol, request.days)
        return {"symbol": request.symbol, "prediction": prediction_data}
    except Exception as e:
        logger.error(f"Error predicting stock: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Include routes for static files
@app.get("/{path:path}", response_class=HTMLResponse)
async def catch_all(path: str, request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 