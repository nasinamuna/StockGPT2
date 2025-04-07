import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, Tabs, Tab, Button, CircularProgress } from '@mui/material';
import { styled } from '@mui/material/styles';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartData,
  ChartOptions,
  ChartType
} from 'chart.js';
import { Download as DownloadIcon } from '@mui/icons-material';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface StockAnalysisProps {
  symbol: string;
  data: {
    market_data?: any;
    technical_analysis?: any;
    fundamental_analysis?: any;
    sentiment_analysis?: any;
    price_prediction?: any;
  };
}

const AnalysisPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginBottom: theme.spacing(3),
}));

const MetricBox = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius,
  backgroundColor: theme.palette.background.default,
  marginBottom: theme.spacing(2),
}));

const StockAnalysis: React.FC<StockAnalysisProps> = ({ symbol, data }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);

  // Chart options
  const lineChartOptions: ChartOptions<'line'> = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `${symbol} Analysis`,
      },
    },
    scales: {
      y: {
        type: 'linear',
        beginAtZero: false,
      },
      x: {
        type: 'category',
      },
    },
  };

  const barChartOptions: ChartOptions<'bar'> = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `${symbol} Analysis`,
      },
    },
    scales: {
      y: {
        type: 'linear',
        beginAtZero: true,
      },
      x: {
        type: 'category',
      },
    },
  };

  // Technical Analysis Chart Data
  const technicalChartData: ChartData<'line'> = {
    labels: data.market_data?.dates || [],
    datasets: [
      {
        label: 'Price',
        data: data.market_data?.prices || [],
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
      {
        label: 'SMA 50',
        data: data.technical_analysis?.sma50 || [],
        borderColor: 'rgb(255, 99, 132)',
        tension: 0.1,
      },
      {
        label: 'SMA 200',
        data: data.technical_analysis?.sma200 || [],
        borderColor: 'rgb(54, 162, 235)',
        tension: 0.1,
      },
    ],
  };

  // Sentiment Analysis Chart Data
  const sentimentChartData: ChartData<'bar'> = {
    labels: ['News', 'Twitter', 'Reddit', 'Overall'],
    datasets: [
      {
        label: 'Sentiment Score',
        data: [
          data.sentiment_analysis?.news?.average_sentiment || 0,
          data.sentiment_analysis?.twitter?.average_sentiment || 0,
          data.sentiment_analysis?.reddit?.average_sentiment || 0,
          data.sentiment_analysis?.overall?.score || 0,
        ],
        backgroundColor: [
          'rgba(255, 99, 132, 0.5)',
          'rgba(54, 162, 235, 0.5)',
          'rgba(255, 206, 86, 0.5)',
          'rgba(75, 192, 192, 0.5)',
        ],
      },
    ],
  };

  // Prediction Chart Data
  const predictionChartData: ChartData<'line'> = {
    labels: Array.from({ length: data.price_prediction?.prediction?.length || 0 }, (_, i) => `Day ${i + 1}`),
    datasets: [
      {
        label: 'Predicted Price',
        data: data.price_prediction?.prediction || [],
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  const handleExport = () => {
    // Create a data URL for the analysis data
    const dataStr = JSON.stringify(data, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const dataUrl = URL.createObjectURL(dataBlob);
    
    // Create a download link
    const link = document.createElement('a');
    link.href = dataUrl;
    link.download = `${symbol}_analysis_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(dataUrl);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <AnalysisPaper>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" gutterBottom>
            {symbol} Analysis
          </Typography>
          <Button
            variant="contained"
            color="primary"
            startIcon={<DownloadIcon />}
            onClick={handleExport}
          >
            Export Analysis
          </Button>
        </Box>
        
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
          aria-label="analysis tabs"
        >
          <Tab label="Technical" />
          <Tab label="Fundamental" />
          <Tab label="Sentiment" />
          <Tab label="Prediction" />
        </Tabs>
        
        <Box mt={3}>
          {activeTab === 0 && (
            <Box>
              <Line options={lineChartOptions} data={technicalChartData} />
              <Box mt={3}>
                <Typography variant="h6" gutterBottom>
                  Technical Indicators
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={2}>
                  {data.technical_analysis?.indicators && Object.entries(data.technical_analysis.indicators).map(([key, value]) => (
                    <MetricBox key={key} sx={{ width: 'calc(50% - 8px)' }}>
                      <Typography variant="subtitle2" color="textSecondary">
                        {key.replace(/([A-Z])/g, ' $1').trim()}
                      </Typography>
                      <Typography variant="h6">
                        {typeof value === 'number' ? value.toFixed(2) : String(value)}
                      </Typography>
                    </MetricBox>
                  ))}
                </Box>
              </Box>
            </Box>
          )}
          
          {activeTab === 1 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Financial Metrics
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={2}>
                {data.fundamental_analysis?.metrics && Object.entries(data.fundamental_analysis.metrics).map(([key, value]) => (
                  <MetricBox key={key} sx={{ width: 'calc(50% - 8px)' }}>
                    <Typography variant="subtitle2" color="textSecondary">
                      {key.replace(/([A-Z])/g, ' $1').trim()}
                    </Typography>
                    <Typography variant="h6">
                      {typeof value === 'number' ? value.toFixed(2) : String(value)}
                    </Typography>
                  </MetricBox>
                ))}
              </Box>
            </Box>
          )}
          
          {activeTab === 2 && (
            <Box>
              <Bar options={barChartOptions} data={sentimentChartData} />
              <Box mt={3}>
                <Typography variant="h6" gutterBottom>
                  Sentiment Details
                </Typography>
                <MetricBox>
                  <Typography variant="subtitle2" color="textSecondary">
                    Overall Sentiment
                  </Typography>
                  <Typography variant="h6">
                    {data.sentiment_analysis?.overall?.category || 'Neutral'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Confidence: {(data.sentiment_analysis?.overall?.confidence || 0) * 100}%
                  </Typography>
                </MetricBox>
              </Box>
            </Box>
          )}
          
          {activeTab === 3 && (
            <Box>
              <Line options={lineChartOptions} data={predictionChartData} />
              <Box mt={3}>
                <Typography variant="h6" gutterBottom>
                  Prediction Details
                </Typography>
                <MetricBox>
                  <Typography variant="subtitle2" color="textSecondary">
                    Prediction Confidence
                  </Typography>
                  <Typography variant="h6">
                    {(data.price_prediction?.confidence || 0) * 100}%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Last Updated: {new Date(data.price_prediction?.last_updated || '').toLocaleString()}
                  </Typography>
                </MetricBox>
              </Box>
            </Box>
          )}
        </Box>
      </AnalysisPaper>
    </Box>
  );
};

export default StockAnalysis; 