# StockGPT

StockGPT is a comprehensive stock market analysis tool focused on Indian markets, leveraging FinGPT and other open-source models to provide detailed analysis of stocks.

## Features

- Real-time market data collection from NSE, BSE, and MoneyControl
- Comprehensive financial statement analysis
- Technical analysis with multiple indicators
- Sentiment analysis of news and social media
- Risk assessment and prediction models
- User-friendly web interface

## Project Structure

```
stockgpt/
├── data/
│   ├── raw/           # Raw collected data
│   ├── processed/     # Processed and cleaned data
│   └── models/        # Trained models
├── src/
│   ├── data_collection/   # Data collection modules
│   ├── data_processing/   # Data processing and cleaning
│   ├── analysis/          # Analysis modules
│   ├── prediction/        # Prediction models
│   ├── api/              # FastAPI backend
│   └── web/              # Frontend code
├── notebooks/            # Jupyter notebooks for analysis
├── config/              # Configuration files
└── docs/               # Documentation
```

## Installation

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

4. Configure the project:
- Copy `config/data_sources.json.example` to `config/data_sources.json`
- Update the configuration with your API keys and settings

## Usage

1. Start the data collection service:
```bash
python src/data_collection/main.py
```

2. Start the API server:
```bash
python src/api/main.py
```

3. Start the web interface:
```bash
cd src/web
npm install
npm start
```

## Data Collection

The system collects data from multiple sources:

- NSE and BSE for real-time market data
- MoneyControl for additional market data
- Screener.in for financial statements
- News APIs for sentiment analysis
- Social media platforms for market sentiment

## Analysis Features

1. Technical Analysis
   - Moving averages
   - RSI, MACD, Bollinger Bands
   - Volume analysis
   - Pattern recognition

2. Fundamental Analysis
   - Financial ratios
   - Growth metrics
   - Valuation analysis
   - Peer comparison

3. Sentiment Analysis
   - News sentiment
   - Social media sentiment
   - Market sentiment indicators

4. Risk Assessment
   - Market risk
   - Credit risk
   - Geopolitical risk
   - Portfolio risk

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FinGPT for the base model
- NSE and BSE for market data
- MoneyControl and Screener.in for financial data
- All contributors and maintainers 