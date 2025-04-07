import React, { createContext, useContext, useState, ReactNode } from 'react';

interface StockContextType {
  selectedStock: string | null;
  setSelectedStock: (symbol: string | null) => void;
}

const StockContext = createContext<StockContextType | undefined>(undefined);

export const useStock = () => {
  const context = useContext(StockContext);
  if (!context) {
    throw new Error('useStock must be used within a StockProvider');
  }
  return context;
};

interface StockProviderProps {
  children: ReactNode;
}

export const StockProvider: React.FC<StockProviderProps> = ({ children }) => {
  const [selectedStock, setSelectedStock] = useState<string | null>(null);

  return (
    <StockContext.Provider value={{ selectedStock, setSelectedStock }}>
      {children}
    </StockContext.Provider>
  );
}; 