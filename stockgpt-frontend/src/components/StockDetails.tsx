import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, Tabs, Tab, CircularProgress } from '@mui/material';
import { styled } from '@mui/material/styles';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartData,
  ChartOptions
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface StockDetailsProps {
  symbol: string;
}

interface StockData {
  prices: number[];
  dates: string[];
  volumes: number[];
  technicalIndicators: {
    sma50: number[];
    sma200: number[];
    rsi: number[];
    macd: {
      line: number[];
      signal: number[];
      histogram: number[];
    };
  };
  fundamentalMetrics: {
    [key: string]: string | number;
  };
}

const DetailsPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  margin: theme.spacing(2),
  borderRadius: theme.shape.borderRadius,
}));

const MetricBox = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  backgroundColor: theme.palette.background.default,
  borderRadius: theme.shape.borderRadius,
  boxShadow: theme.shadows[1],
}));

const StockDetails: React.FC<StockDetailsProps> = ({ symbol }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [stockData, setStockData] = useState<StockData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStockData(symbol);
  }, [symbol]);

  const fetchStockData = async (symbol: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`/api/stock/${symbol}`);
      if (!response.ok) {
        throw new Error('Failed to fetch stock data');
      }
      const data = await response.json();
      setStockData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `${symbol} Stock Price`,
      },
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  };

  const priceChartData: ChartData<'line'> = {
    labels: stockData?.dates || [],
    datasets: [
      {
        label: 'Price',
        data: stockData?.prices || [],
        borderColor: 'rgb(75, 192, 192)',
        yAxisID: 'y',
      },
      {
        label: 'Volume',
        data: stockData?.volumes || [],
        borderColor: 'rgb(53, 162, 235)',
        yAxisID: 'y1',
      },
    ],
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <DetailsPaper>
        <Typography variant="h4" gutterBottom>
          {symbol} Stock Analysis
        </Typography>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
          aria-label="stock analysis tabs"
        >
          <Tab label="Overview" />
          <Tab label="Technical" />
          <Tab label="Fundamental" />
        </Tabs>
        <Box mt={3}>
          {activeTab === 0 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Box>
                <Line options={chartOptions} data={priceChartData} />
              </Box>
              <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" gutterBottom>
                    Key Metrics
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                    {stockData?.fundamentalMetrics && Object.entries(stockData.fundamentalMetrics).map(([key, value]) => (
                      <Box key={key} sx={{ width: 'calc(50% - 8px)' }}>
                        <MetricBox>
                          <Typography variant="subtitle2" color="textSecondary">
                            {key.replace(/([A-Z])/g, ' $1').trim()}
                          </Typography>
                          <Typography variant="h6">
                            {typeof value === 'number' ? value.toLocaleString() : value}
                          </Typography>
                        </MetricBox>
                      </Box>
                    ))}
                  </Box>
                </Box>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" gutterBottom>
                    Technical Indicators
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                    <Box sx={{ width: 'calc(50% - 8px)' }}>
                      <MetricBox>
                        <Typography variant="subtitle2" color="textSecondary">
                          SMA 50
                        </Typography>
                        <Typography variant="h6">
                          {stockData?.technicalIndicators.sma50[stockData.technicalIndicators.sma50.length - 1]?.toFixed(2)}
                        </Typography>
                      </MetricBox>
                    </Box>
                    <Box sx={{ width: 'calc(50% - 8px)' }}>
                      <MetricBox>
                        <Typography variant="subtitle2" color="textSecondary">
                          SMA 200
                        </Typography>
                        <Typography variant="h6">
                          {stockData?.technicalIndicators.sma200[stockData.technicalIndicators.sma200.length - 1]?.toFixed(2)}
                        </Typography>
                      </MetricBox>
                    </Box>
                    <Box sx={{ width: 'calc(50% - 8px)' }}>
                      <MetricBox>
                        <Typography variant="subtitle2" color="textSecondary">
                          RSI
                        </Typography>
                        <Typography variant="h6">
                          {stockData?.technicalIndicators.rsi[stockData.technicalIndicators.rsi.length - 1]?.toFixed(2)}
                        </Typography>
                      </MetricBox>
                    </Box>
                    <Box sx={{ width: 'calc(50% - 8px)' }}>
                      <MetricBox>
                        <Typography variant="subtitle2" color="textSecondary">
                          MACD
                        </Typography>
                        <Typography variant="h6">
                          {stockData?.technicalIndicators.macd.line[stockData.technicalIndicators.macd.line.length - 1]?.toFixed(2)}
                        </Typography>
                      </MetricBox>
                    </Box>
                  </Box>
                </Box>
              </Box>
            </Box>
          )}
          {activeTab === 1 && (
            <Typography variant="body1">
              Technical Analysis Content
            </Typography>
          )}
          {activeTab === 2 && (
            <Typography variant="body1">
              Fundamental Analysis Content
            </Typography>
          )}
        </Box>
      </DetailsPaper>
    </Box>
  );
};

export default StockDetails; 