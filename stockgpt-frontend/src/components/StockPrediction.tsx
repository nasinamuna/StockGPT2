import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, CircularProgress } from '@mui/material';
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

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface StockPredictionProps {
  symbol: string;
  data: {
    prediction: number[];
    confidence: number;
    last_updated: string;
    historical_accuracy?: {
      dates: string[];
      actual: number[];
      predicted: number[];
    };
  };
}

const PredictionPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  marginBottom: theme.spacing(3),
}));

const MetricBox = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius,
  backgroundColor: theme.palette.background.default,
  marginBottom: theme.spacing(2),
}));

const ChartContainer = styled(Box)(({ theme }) => ({
  width: '100%',
  [theme.breakpoints.up('md')]: {
    width: '66.67%',
  },
}));

const MetricsContainer = styled(Box)(({ theme }) => ({
  width: '100%',
  [theme.breakpoints.up('md')]: {
    width: '33.33%',
  },
}));

const StockPrediction: React.FC<StockPredictionProps> = ({ symbol, data }) => {
  const [loading, setLoading] = useState(false);

  // Chart options
  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `${symbol} Price Prediction`,
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

  // Prediction Chart Data
  const predictionChartData: ChartData<'line'> = {
    labels: Array.from({ length: data.prediction.length }, (_, i) => `Day ${i + 1}`),
    datasets: [
      {
        label: 'Predicted Price',
        data: data.prediction,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  };

  // Historical Accuracy Chart Data
  const historicalChartData: ChartData<'line'> = {
    labels: data.historical_accuracy?.dates || [],
    datasets: [
      {
        label: 'Actual Price',
        data: data.historical_accuracy?.actual || [],
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
      {
        label: 'Predicted Price',
        data: data.historical_accuracy?.predicted || [],
        borderColor: 'rgb(255, 99, 132)',
        tension: 0.1,
      },
    ],
  };

  // Calculate historical accuracy metrics
  const calculateAccuracyMetrics = () => {
    if (!data.historical_accuracy) return null;

    const { actual, predicted } = data.historical_accuracy;
    const errors = actual.map((a, i) => Math.abs(a - predicted[i]) / a);
    const mape = errors.reduce((sum, error) => sum + error, 0) / errors.length;
    const accuracy = 1 - mape;

    return {
      mape: mape * 100,
      accuracy: accuracy * 100,
    };
  };

  const accuracyMetrics = calculateAccuracyMetrics();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <PredictionPaper>
        <Typography variant="h4" gutterBottom>
          {symbol} Price Prediction
        </Typography>
        
        <Box display="flex" flexDirection={{ xs: 'column', md: 'row' }} gap={3}>
          <ChartContainer>
            <Line options={chartOptions} data={predictionChartData} />
          </ChartContainer>
          
          <MetricsContainer>
            <MetricBox>
              <Typography variant="subtitle2" color="textSecondary">
                Prediction Confidence
              </Typography>
              <Typography variant="h4">
                {(data.confidence * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Last Updated: {new Date(data.last_updated).toLocaleString()}
              </Typography>
            </MetricBox>
            
            {accuracyMetrics && (
              <MetricBox>
                <Typography variant="subtitle2" color="textSecondary">
                  Historical Accuracy
                </Typography>
                <Typography variant="h6">
                  {accuracyMetrics.accuracy.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Mean Absolute Percentage Error: {accuracyMetrics.mape.toFixed(1)}%
                </Typography>
              </MetricBox>
            )}
          </MetricsContainer>
        </Box>
        
        {data.historical_accuracy && (
          <Box mt={3}>
            <Typography variant="h6" gutterBottom>
              Historical Prediction Performance
            </Typography>
            <Line options={chartOptions} data={historicalChartData} />
          </Box>
        )}
      </PredictionPaper>
    </Box>
  );
};

export default StockPrediction; 