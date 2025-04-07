# StockGPT: Indian Stock Market Analysis System

## Overview

StockGPT is a comprehensive Indian stock market analysis system that combines elements from open-source financial models like FinGPT with custom development to provide fundamental, technical, and sentiment analysis capabilities. This project aims to help users make more informed investment decisions in the Indian stock market by analyzing various market data, financial statements, news, and social media content.

## Features

- **Market Data Analysis**: Real-time and historical price, volume, and derivatives data from NSE and BSE
- **Fundamental Analysis**: Analysis of balance sheets, income statements, and cash flows
- **Technical Analysis**: Calculation and interpretation of technical indicators and chart patterns
- **Sentiment Analysis**: News and social media sentiment tracking and analysis
- **Risk Assessment**: Evaluation of market, credit, and geopolitical risks
- **Price Prediction**: Machine learning-based forecasting of future price movements
- **Web Interface**: User-friendly interface for accessing all analysis features

## System Architecture

StockGPT consists of the following main components:

1. **Data Collection Layer**: Gathers market data, financial statements, news, and corporate actions
2. **Data Processing Layer**: Cleans and transforms data for analysis
3. **Analysis Layer**: Performs various types of analysis on the processed data
4. **Prediction Layer**: Uses machine learning models to forecast future trends
5. **Web Application**: Provides user interface for interacting with the system

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 14.x or higher (for frontend)
- PostgreSQL database (optional, for storing processed data)
- MongoDB (optional, for storing unstructured data)

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stockgpt.git
cd stockgpt
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create necessary directories:
```bash
mkdir -p data/{raw,processed,models}
mkdir -p data/raw/{market_data,financial_statements,news_social,corporate_actions}
mkdir -p data/processed/{market_data,financial_statements,news_social,technical_indicators,analysis}
```

5. Configure data sources:
- Copy `config/data_sources.example.json` to `config/data_sources.json`
- Update API keys and source mappings in `config/data_sources.json`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd stockgpt-frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure API endpoint:
- Edit `src/services/api.js` to point to your backend server

### Database Setup (Optional)

For production use, it's recommended to set up databases:

1. PostgreSQL setup:
```bash
# Create database
createdb stockgpt

# Run migration scripts
python scripts/db_setup.py
```

2. MongoDB setup:
```bash
# Start MongoDB and create database
mongo

use stockgpt
db.createCollection("news")
db.createCollection("social_media")
```

## Running the Application

### Development Mode

1. Start the backend server:
```bash
cd stockgpt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

2. Start the frontend development server:
```bash
cd stockgpt-frontend
npm start
```

3. Access the application at `http://localhost:3000`

### Production Deployment

#### Using Docker (Recommended)

1. Build the Docker images:
```bash
docker-compose build
```

2. Run the containers:
```bash
docker-compose up -d
```

3. Access the application at `http://localhost`

#### Manual Deployment

1. Build the frontend:
```bash
cd stockgpt-frontend
npm run build
```

2. Copy the build files to the backend static directory:
```bash
cp -r build/* ../stockgpt/static/
```

3. Set up a production WSGI server (e.g., Gunicorn):
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app
```

4. Set up a reverse proxy with Nginx or Apache to serve the application

## Usage Guide

### Stock Analysis

1. **Search for a Stock**: Enter the stock symbol or company name in the search bar
2. **View Stock Overview**: See basic information and recent performance
3. **Technical Analysis**: Access technical indicators, chart patterns, and trend analysis
4. **Fundamental Analysis**: Review financial statements, ratios, and company health
5. **Sentiment Analysis**: Check news and social media sentiment around the stock
6. **Risk Assessment**: Evaluate various risk factors associated with the stock
7. **Price Prediction**: View machine learning-based price forecasts

### Data Collection and Updates

1. **Manual Data Update**:
```bash
python scripts/update_data.py --symbol=RELIANCE.NS
```

2. **Scheduled Updates**:
- Set up a cron job to run updates periodically:
```bash
0 18 * * 1-5 cd /path/to/stockgpt && python scripts/update_data.py --all
```

### Customizing Analysis Parameters

Edit `config/analysis_parameters.json` to customize:
- Technical indicators used
- Fundamental analysis thresholds
- Sentiment analysis sources
- Risk assessment criteria
- Prediction model parameters

## Project Structure

```
stockgpt/
├── config/           # Configuration files
├── data/            # Data storage
│   ├── raw/         # Raw collected data
│   ├── processed/   # Processed data
│   └── models/      # Trained ML models
├── src/             # Source code
│   ├── data_collection/    # Data collection modules
│   ├── data_processing/    # Data processing modules
│   ├── analysis/          # Analysis modules
│   ├── prediction/        # Prediction modules
│   ├── api/              # API endpoints
│   └── web/              # Web interface
├── stockgpt-frontend/     # React frontend code
├── scripts/          # Utility scripts
├── tests/           # Test cases
├── requirements.txt  # Python dependencies
├── docker-compose.yml # Docker configuration
└── README.md        # This file
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

Please ensure your code adheres to the project's coding standards and includes appropriate tests.

## Troubleshooting

### Common Issues

1. **Data Source Connection Errors**:
   - Check your internet connection
   - Verify API keys in `config/data_sources.json`
   - Ensure source URLs are correct and accessible

2. **Model Training Errors**:
   - Check for missing or corrupt data files
   - Ensure sufficient data points for training
   - Verify GPU availability for training (if applicable)

3. **Web Interface Issues**:
   - Check browser console for JavaScript errors
   - Verify API endpoint configuration
   - Check backend logs for server errors

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) - Financial NLP model
- [FinBERT](https://github.com/ProsusAI/finBERT) - Financial sentiment analysis
- [Mistral 7B](https://mistral.ai/) - Language model architecture
- [Falcon 7B](https://github.com/predibase/falcon7b) - Language model architecture
- [NSE India](https://www.nseindia.com/) - Market data
- [BSE India](https://www.bseindia.com/) - Market data

---

*Disclaimer: StockGPT is a tool for information and analysis purposes only. It does not constitute financial advice. Always conduct your own research and consult with a licensed financial advisor before making investment decisions.* 