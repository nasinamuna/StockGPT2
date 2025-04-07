import React, { useState } from 'react';
import { TextField, Autocomplete, Paper, Box, Typography } from '@mui/material';
import { styled } from '@mui/material/styles';

interface Stock {
  symbol: string;
  name: string;
  exchange: string;
}

interface StockSearchProps {
  onStockSelect: (stock: Stock) => void;
}

const SearchContainer = styled(Box)(({ theme }) => ({
  width: '100%',
  maxWidth: 600,
  margin: '0 auto',
  padding: theme.spacing(2),
}));

const StockPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.shape.borderRadius,
  boxShadow: theme.shadows[2],
}));

const StockSearch: React.FC<StockSearchProps> = ({ onStockSelect }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [options, setOptions] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (value: string) => {
    setSearchTerm(value);
    if (value.length < 2) {
      setOptions([]);
      return;
    }

    setLoading(true);
    try {
      // TODO: Replace with actual API call
      const response = await fetch(`/api/stocks/search?query=${value}`);
      const data = await response.json();
      setOptions(data);
    } catch (error) {
      console.error('Error searching stocks:', error);
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SearchContainer>
      <StockPaper>
        <Typography variant="h6" gutterBottom>
          Search Stocks
        </Typography>
        <Autocomplete
          options={options}
          getOptionLabel={(option) => `${option.symbol} - ${option.name}`}
          loading={loading}
          onInputChange={(_, value) => handleSearch(value)}
          onChange={(_, value) => value && onStockSelect(value)}
          renderInput={(params) => (
            <TextField
              {...params}
              label="Enter stock symbol or company name"
              variant="outlined"
              fullWidth
            />
          )}
          renderOption={(props, option) => (
            <Box component="li" {...props}>
              <Box>
                <Typography variant="subtitle1">
                  {option.symbol}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {option.name} ({option.exchange})
                </Typography>
              </Box>
            </Box>
          )}
        />
      </StockPaper>
    </SearchContainer>
  );
};

export default StockSearch; 