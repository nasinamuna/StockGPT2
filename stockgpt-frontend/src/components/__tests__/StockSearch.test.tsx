import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import StockSearch from '../StockSearch';
import { StockProvider } from '../../context/StockContext';

// Mock the API service
jest.mock('../../services/api', () => ({
  searchStocks: jest.fn().mockResolvedValue([
    { symbol: 'AAPL', name: 'Apple Inc.' },
    { symbol: 'GOOGL', name: 'Alphabet Inc.' }
  ])
}));

describe('StockSearch', () => {
  const mockOnStockSelect = jest.fn();

  it('renders search input and button', () => {
    render(
      <StockProvider>
        <StockSearch onStockSelect={mockOnStockSelect} />
      </StockProvider>
    );
    
    expect(screen.getByPlaceholderText('Enter stock symbol...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
  });

  it('handles search input changes', () => {
    render(
      <StockProvider>
        <StockSearch onStockSelect={mockOnStockSelect} />
      </StockProvider>
    );
    
    const input = screen.getByPlaceholderText('Enter stock symbol...');
    fireEvent.change(input, { target: { value: 'AAPL' } });
    
    expect(input).toHaveValue('AAPL');
  });

  it('performs search on button click', async () => {
    render(
      <StockProvider>
        <StockSearch onStockSelect={mockOnStockSelect} />
      </StockProvider>
    );
    
    const input = screen.getByPlaceholderText('Enter stock symbol...');
    const button = screen.getByRole('button', { name: /search/i });
    
    fireEvent.change(input, { target: { value: 'AAPL' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    });
  });

  it('shows loading state during search', async () => {
    render(
      <StockProvider>
        <StockSearch onStockSelect={mockOnStockSelect} />
      </StockProvider>
    );
    
    const input = screen.getByPlaceholderText('Enter stock symbol...');
    const button = screen.getByRole('button', { name: /search/i });
    
    fireEvent.change(input, { target: { value: 'AAPL' } });
    fireEvent.click(button);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });
  });

  it('handles search errors', async () => {
    // Mock API to throw error
    jest.spyOn(require('../../services/api'), 'searchStocks')
      .mockRejectedValueOnce(new Error('API Error'));
    
    render(
      <StockProvider>
        <StockSearch onStockSelect={mockOnStockSelect} />
      </StockProvider>
    );
    
    const input = screen.getByPlaceholderText('Enter stock symbol...');
    const button = screen.getByRole('button', { name: /search/i });
    
    fireEvent.change(input, { target: { value: 'AAPL' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(screen.getByText('Error searching stocks')).toBeInTheDocument();
    });
  });

  it('handles empty search results', async () => {
    // Mock API to return empty results
    jest.spyOn(require('../../services/api'), 'searchStocks')
      .mockResolvedValueOnce([]);
    
    render(
      <StockProvider>
        <StockSearch onStockSelect={mockOnStockSelect} />
      </StockProvider>
    );
    
    const input = screen.getByPlaceholderText('Enter stock symbol...');
    const button = screen.getByRole('button', { name: /search/i });
    
    fireEvent.change(input, { target: { value: 'INVALID' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      expect(screen.getByText('No stocks found')).toBeInTheDocument();
    });
  });

  it('calls onStockSelect when a stock is selected', async () => {
    render(
      <StockProvider>
        <StockSearch onStockSelect={mockOnStockSelect} />
      </StockProvider>
    );
    
    const input = screen.getByPlaceholderText('Enter stock symbol...');
    const button = screen.getByRole('button', { name: /search/i });
    
    fireEvent.change(input, { target: { value: 'AAPL' } });
    fireEvent.click(button);
    
    await waitFor(() => {
      const stockItem = screen.getByText('Apple Inc.');
      fireEvent.click(stockItem);
      expect(mockOnStockSelect).toHaveBeenCalledWith('AAPL');
    });
  });
}); 