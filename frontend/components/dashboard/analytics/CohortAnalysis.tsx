'use client';

/**
 * Cohort Analysis Component
 *
 * Tracks tutor retention and performance by cohort
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface RetentionCurveData {
  time_points_days: number[];
  retention_rates: number[];
  metadata: {
    cohort_id: string | null;
    curve_type: string;
  };
}

export function CohortAnalysis() {
  const [data, setData] = useState<RetentionCurveData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/analytics/cohort-analysis/retention-curve');
        const curveData = await response.json();
        setData(curveData);
      } catch (error) {
        console.error('Failed to fetch cohort data:', error);
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
          <CardTitle>Cohort Analysis</CardTitle>
          <CardDescription>Loading retention curve...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const chartData = {
    labels: data.time_points_days.map(d => `Day ${d}`),
    datasets: [
      {
        label: 'Retention Rate',
        data: data.retention_rates,
        fill: true,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `Retention: ${context.parsed.y.toFixed(1)}%`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        title: {
          display: true,
          text: 'Retention Rate (%)'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Days Since Onboarding'
        }
      }
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Retention Curve</CardTitle>
        <CardDescription>
          Tutor retention over time since onboarding
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[400px]">
          <Line data={chartData} options={options} />
        </div>
        <div className="mt-4 grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-blue-600">
              {data.retention_rates[2].toFixed(1)}%
            </div>
            <div className="text-sm text-muted-foreground">30-Day Retention</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-600">
              {data.retention_rates[4].toFixed(1)}%
            </div>
            <div className="text-sm text-muted-foreground">90-Day Retention</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-600">
              {data.retention_rates[6].toFixed(1)}%
            </div>
            <div className="text-sm text-muted-foreground">1-Year Retention</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
