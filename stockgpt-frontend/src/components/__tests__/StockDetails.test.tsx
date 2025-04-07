import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import StockDetails from '../StockDetails';
import { StockProvider } from '../../context/StockContext';

// Mock the API service
jest.mock('../../services/api', () => ({
  getStockData: jest.fn().mockResolvedValue({
    price: 150.0,
    volume: 1000000,
    timestamp: '2023-01-01T00:00:00',
    historical_data: {
      dates: ['2023-01-01', '2023-01-02', '2023-01-03'],
      prices: [150.0, 151.0, 152.0],
      volumes: [1000000, 1100000, 1200000]
    }
  })
}));

describe('StockDetails', () => {
  it('renders loading state initially', () => {
    render(
      <StockProvider>
        <StockDetails symbol="AAPL" />
      </StockProvider>
    );
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders stock data after loading', async () => {
    render(
      <StockProvider>
        <StockDetails symbol="AAPL" />
      </StockProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('$150.00')).toBeInTheDocument();
      expect(screen.getByText('1,000,000')).toBeInTheDocument();
    });
  });

  it('renders tabs for different analysis types', async () => {
    render(
      <StockProvider>
        <StockDetails symbol="AAPL" />
      </StockProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
      expect(screen.getByText('Technical')).toBeInTheDocument();
      expect(screen.getByText('Fundamental')).toBeInTheDocument();
    });
  });

  it('handles API errors', async () => {
    // Mock API to throw error
    jest.spyOn(require('../../services/api'), 'getStockData')
      .mockRejectedValueOnce(new Error('API Error'));
    
    render(
      <StockProvider>
        <StockDetails symbol="AAPL" />
      </StockProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Error loading stock data')).toBeInTheDocument();
    });
  });

  it('switches between tabs', async () => {
    render(
      <StockProvider>
        <StockDetails symbol="AAPL" />
      </StockProvider>
    );
    
    await waitFor(() => {
      const technicalTab = screen.getByText('Technical');
      fireEvent.click(technicalTab);
      
      expect(screen.getByText('Technical Analysis')).toBeInTheDocument();
    });
  });

  it('renders price chart', async () => {
    render(
      <StockProvider>
        <StockDetails symbol="AAPL" />
      </StockProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Price Chart')).toBeInTheDocument();
    });
  });

  it('renders volume chart', async () => {
    render(
      <StockProvider>
        <StockDetails symbol="AAPL" />
      </StockProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Volume')).toBeInTheDocument();
    });
  });
}); 