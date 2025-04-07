import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import StockAnalysis from '../StockAnalysis';
import { StockProvider } from '../../context/StockContext';

// Mock the API service
jest.mock('../../services/api', () => ({
  getStockAnalysis: jest.fn().mockResolvedValue({
    market_data: {
      price: 150.0,
      volume: 1000000,
      timestamp: '2023-01-01T00:00:00'
    },
    technical_analysis: {
      indicators: {
        sma: [150.0, 151.0, 152.0],
        rsi: 65.0,
        macd: 1.5
      },
      signals: {
        buy: true,
        sell: false
      }
    },
    fundamental_analysis: {
      metrics: {
        pe_ratio: 25.0,
        pb_ratio: 3.0,
        dividend_yield: 0.02
      },
      valuation: 'fair'
    },
    sentiment_analysis: {
      sentiment: {
        news: 0.7,
        social: 0.6
      },
      overall: 'bullish'
    },
    price_prediction: {
      prediction: [155.0, 156.0, 157.0],
      confidence: 0.85
    }
  })
}));

const mockData = {
  market_data: {
    price: 150.0,
    volume: 1000000,
    timestamp: '2023-01-01T00:00:00'
  },
  technical_analysis: {
    indicators: {
      sma: [150.0, 151.0, 152.0],
      rsi: 65.0,
      macd: 1.5
    },
    signals: {
      buy: true,
      sell: false
    }
  },
  fundamental_analysis: {
    metrics: {
      pe_ratio: 25.0,
      pb_ratio: 3.0,
      dividend_yield: 0.02
    },
    valuation: 'fair'
  },
  sentiment_analysis: {
    sentiment: {
      news: 0.7,
      social: 0.6
    },
    overall: 'bullish'
  },
  price_prediction: {
    prediction: [155.0, 156.0, 157.0],
    confidence: 0.85
  }
};

describe('StockAnalysis', () => {
  it('renders loading state initially', () => {
    render(
      <StockProvider>
        <StockAnalysis symbol="AAPL" data={mockData} />
      </StockProvider>
    );
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders analysis data after loading', async () => {
    render(
      <StockProvider>
        <StockAnalysis symbol="AAPL" data={mockData} />
      </StockProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Technical Analysis')).toBeInTheDocument();
      expect(screen.getByText('Fundamental Analysis')).toBeInTheDocument();
      expect(screen.getByText('Sentiment Analysis')).toBeInTheDocument();
    });
  });

  it('renders tabs for different analysis types', async () => {
    render(
      <StockProvider>
        <StockAnalysis symbol="AAPL" data={mockData} />
      </StockProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Technical')).toBeInTheDocument();
      expect(screen.getByText('Fundamental')).toBeInTheDocument();
      expect(screen.getByText('Sentiment')).toBeInTheDocument();
    });
  });

  it('handles API errors', async () => {
    // Mock API to throw error
    jest.spyOn(require('../../services/api'), 'getStockAnalysis')
      .mockRejectedValueOnce(new Error('API Error'));
    
    render(
      <StockProvider>
        <StockAnalysis symbol="AAPL" data={mockData} />
      </StockProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Error loading analysis data')).toBeInTheDocument();
    });
  });

  it('switches between tabs', async () => {
    render(
      <StockProvider>
        <StockAnalysis symbol="AAPL" data={mockData} />
      </StockProvider>
    );
    
    await waitFor(() => {
      const fundamentalTab = screen.getByText('Fundamental');
      fireEvent.click(fundamentalTab);
      
      expect(screen.getByText('Fundamental Analysis')).toBeInTheDocument();
    });
  });

  it('renders technical indicators', async () => {
    render(
      <StockProvider>
        <StockAnalysis symbol="AAPL" data={mockData} />
      </StockProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('SMA')).toBeInTheDocument();
      expect(screen.getByText('RSI')).toBeInTheDocument();
      expect(screen.getByText('MACD')).toBeInTheDocument();
    });
  });

  it('renders fundamental metrics', async () => {
    render(
      <StockProvider>
        <StockAnalysis symbol="AAPL" data={mockData} />
      </StockProvider>
    );
    
    await waitFor(() => {
      const fundamentalTab = screen.getByText('Fundamental');
      fireEvent.click(fundamentalTab);
      
      expect(screen.getByText('P/E Ratio')).toBeInTheDocument();
      expect(screen.getByText('P/B Ratio')).toBeInTheDocument();
      expect(screen.getByText('Dividend Yield')).toBeInTheDocument();
    });
  });

  it('renders sentiment analysis', async () => {
    render(
      <StockProvider>
        <StockAnalysis symbol="AAPL" data={mockData} />
      </StockProvider>
    );
    
    await waitFor(() => {
      const sentimentTab = screen.getByText('Sentiment');
      fireEvent.click(sentimentTab);
      
      expect(screen.getByText('News Sentiment')).toBeInTheDocument();
      expect(screen.getByText('Social Sentiment')).toBeInTheDocument();
      expect(screen.getByText('Overall Sentiment')).toBeInTheDocument();
    });
  });

  it('exports analysis data', async () => {
    render(
      <StockProvider>
        <StockAnalysis symbol="AAPL" data={mockData} />
      </StockProvider>
    );
    
    await waitFor(() => {
      const exportButton = screen.getByText('Export Analysis');
      fireEvent.click(exportButton);
      
      // Mock the download function
      const mockDownload = jest.fn();
      global.URL.createObjectURL = jest.fn(() => 'mock-url');
      global.URL.revokeObjectURL = jest.fn();
      
      expect(mockDownload).toHaveBeenCalled();
    });
  });
}); 