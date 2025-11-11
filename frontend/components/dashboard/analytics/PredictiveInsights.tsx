'use client';

/**
 * Predictive Insights Component
 *
 * Shows forecasts and trend predictions
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Line } from 'react-chartjs-2';
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

interface PredictiveTrendsData {
  historical_data: {
    values: number[];
    dates: string[];
  };
  forecast: {
    values: number[];
    dates: string[];
    confidence_interval: {
      upper: number[];
      lower: number[];
    };
  };
  metadata: {
    trend: string;
    slope: number;
    forecast_days: number;
  };
}

export function PredictiveInsights() {
  const [data, setData] = useState<PredictiveTrendsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/analytics/predictive-insights/trends?forecast_days=30');

        if (!response.ok) {
          throw new Error(`Failed to fetch predictive insights: ${response.status} ${response.statusText}`);
        }

        const trends = await response.json();
        setData(trends);
      } catch (error) {
        console.error('Failed to fetch predictive insights:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Predictive Insights</CardTitle>
          <CardDescription>Loading forecast...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const chartData = {
    labels: [...data.historical_data.dates, ...data.forecast.dates],
    datasets: [
      {
        label: 'Historical',
        data: [
          ...data.historical_data.values,
          ...new Array(data.forecast.values.length).fill(null)
        ],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        pointRadius: 2,
      },
      {
        label: 'Forecast',
        data: [
          ...new Array(data.historical_data.values.length).fill(null),
          ...data.forecast.values
        ],
        borderColor: 'rgb(147, 51, 234)',
        backgroundColor: 'rgba(147, 51, 234, 0.1)',
        borderWidth: 2,
        borderDash: [5, 5],
        pointRadius: 2,
      },
      {
        label: 'Upper Bound',
        data: [
          ...new Array(data.historical_data.values.length).fill(null),
          ...data.forecast.confidence_interval.upper
        ],
        borderColor: 'rgba(147, 51, 234, 0.3)',
        backgroundColor: 'rgba(147, 51, 234, 0.05)',
        borderWidth: 1,
        fill: '+1',
        pointRadius: 0,
      },
      {
        label: 'Lower Bound',
        data: [
          ...new Array(data.historical_data.values.length).fill(null),
          ...data.forecast.confidence_interval.lower
        ],
        borderColor: 'rgba(147, 51, 234, 0.3)',
        backgroundColor: 'rgba(147, 51, 234, 0.05)',
        borderWidth: 1,
        pointRadius: 0,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}%`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Churn Rate (%)'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Date'
        }
      }
    }
  };

  const trendIcon = data.metadata.trend === 'increasing' ? (
    <TrendingUp className="h-5 w-5 text-red-600" />
  ) : (
    <TrendingDown className="h-5 w-5 text-green-600" />
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Predictive Insights
          {trendIcon}
        </CardTitle>
        <CardDescription>
          30-day churn rate forecast with 95% confidence interval
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] mb-4">
          <Line data={chartData} options={options} />
        </div>

        <div className="flex items-start gap-3 p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
          <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
          <div className="flex-1">
            <div className="font-semibold text-blue-900 dark:text-blue-100 mb-1">
              Trend Analysis
            </div>
            <p className="text-sm text-blue-800 dark:text-blue-200">
              Churn rate is {data.metadata.trend}.
              {data.metadata.trend === 'increasing' && (
                <> Consider implementing proactive intervention strategies to reverse this trend.</>
              )}
              {data.metadata.trend === 'decreasing' && (
                <> Current retention strategies are showing positive results.</>
              )}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
