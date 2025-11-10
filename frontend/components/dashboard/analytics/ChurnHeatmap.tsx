'use client';

/**
 * Churn Heatmap Component
 *
 * Visualizes churn patterns over time using a heatmap matrix.
 * Shows risk levels on Y-axis and time periods on X-axis.
 *
 * Performance target: < 500ms render time
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RefreshCw } from 'lucide-react';

interface HeatmapData {
  matrix: number[][];
  x_labels: string[];
  y_labels: string[];
  metadata: {
    start_date: string;
    end_date: string;
    granularity: string;
    periods_count: number;
    max_churn_rate: number;
    avg_churn_rate: number;
  };
}

export function ChurnHeatmap() {
  const [data, setData] = useState<HeatmapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [granularity, setGranularity] = useState('weekly');
  const [viewType, setViewType] = useState('risk');

  const fetchHeatmap = async () => {
    try {
      setLoading(true);
      const endpoint = viewType === 'risk'
        ? '/api/analytics/churn-heatmap'
        : '/api/analytics/churn-heatmap/by-tier';

      const params = new URLSearchParams();
      if (viewType === 'risk') {
        params.append('granularity', granularity);
      }

      const response = await fetch(`http://localhost:8000${endpoint}?${params}`);
      const heatmapData = await response.json();
      setData(heatmapData);
    } catch (error) {
      console.error('Failed to fetch heatmap:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHeatmap();
  }, [granularity, viewType]);

  const getHeatmapColor = (value: number, max: number): string => {
    // Color scale from green (low churn) to red (high churn)
    const intensity = max > 0 ? value / max : 0;

    if (intensity < 0.2) return 'bg-green-100 dark:bg-green-900/20';
    if (intensity < 0.4) return 'bg-green-300 dark:bg-green-700/40';
    if (intensity < 0.6) return 'bg-yellow-300 dark:bg-yellow-700/40';
    if (intensity < 0.8) return 'bg-orange-400 dark:bg-orange-600/50';
    return 'bg-red-500 dark:bg-red-700/60';
  };

  const getTextColor = (value: number, max: number): string => {
    const intensity = max > 0 ? value / max : 0;
    return intensity > 0.5 ? 'text-white' : 'text-gray-900 dark:text-gray-100';
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Churn Heatmap</CardTitle>
          <CardDescription>Loading heatmap data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Churn Heatmap</CardTitle>
          <CardDescription>No data available</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const maxValue = data.metadata.max_churn_rate;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Churn Heatmap</CardTitle>
            <CardDescription>
              Visualizing churn patterns over time
              <span className="ml-2 text-xs">
                (Avg: {data.metadata.avg_churn_rate.toFixed(1)}%,
                Max: {data.metadata.max_churn_rate.toFixed(1)}%)
              </span>
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Select value={viewType} onValueChange={setViewType}>
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="risk">By Risk Level</SelectItem>
                <SelectItem value="tier">By Tier</SelectItem>
              </SelectContent>
            </Select>
            {viewType === 'risk' && (
              <Select value={granularity} onValueChange={setGranularity}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                </SelectContent>
              </Select>
            )}
            <Button variant="outline" size="sm" onClick={fetchHeatmap}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <div className="min-w-[600px]">
            {/* Heatmap Grid */}
            <div className="flex">
              {/* Y-axis labels */}
              <div className="flex flex-col justify-around pr-3">
                {data.y_labels.map((label, idx) => (
                  <div
                    key={idx}
                    className="h-12 flex items-center text-sm font-medium text-right"
                  >
                    {label}
                  </div>
                ))}
              </div>

              {/* Heatmap cells */}
              <div className="flex-1">
                <div className="grid" style={{ gridTemplateColumns: `repeat(${data.x_labels.length}, 1fr)` }}>
                  {/* X-axis labels */}
                  {data.x_labels.map((label, idx) => (
                    <div
                      key={`header-${idx}`}
                      className="text-xs text-center pb-2 font-medium"
                      style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
                    >
                      {label}
                    </div>
                  ))}

                  {/* Heatmap matrix */}
                  {data.matrix.map((row, rowIdx) =>
                    row.map((value, colIdx) => (
                      <div
                        key={`${rowIdx}-${colIdx}`}
                        className={`
                          h-12 flex items-center justify-center
                          border border-gray-200 dark:border-gray-700
                          transition-all hover:scale-105 hover:z-10
                          cursor-pointer rounded-sm
                          ${getHeatmapColor(value, maxValue)}
                        `}
                        title={`${data.y_labels[rowIdx]}, ${data.x_labels[colIdx]}: ${value.toFixed(1)}% churn`}
                      >
                        <span className={`text-xs font-semibold ${getTextColor(value, maxValue)}`}>
                          {value.toFixed(0)}%
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Color Legend */}
            <div className="mt-6 flex items-center justify-center gap-2">
              <span className="text-sm text-muted-foreground">Low</span>
              <div className="flex gap-1">
                <div className="w-8 h-8 bg-green-100 dark:bg-green-900/20 border border-gray-300 dark:border-gray-600 rounded" />
                <div className="w-8 h-8 bg-green-300 dark:bg-green-700/40 border border-gray-300 dark:border-gray-600 rounded" />
                <div className="w-8 h-8 bg-yellow-300 dark:bg-yellow-700/40 border border-gray-300 dark:border-gray-600 rounded" />
                <div className="w-8 h-8 bg-orange-400 dark:bg-orange-600/50 border border-gray-300 dark:border-gray-600 rounded" />
                <div className="w-8 h-8 bg-red-500 dark:bg-red-700/60 border border-gray-300 dark:border-gray-600 rounded" />
              </div>
              <span className="text-sm text-muted-foreground">High</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
