'use client';

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, XAxis, YAxis } from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import type { TutorMetrics } from '@/lib/types';

interface BottomPerformersChartProps {
  tutorMetrics: TutorMetrics[];
}

const chartConfig = {
  score: {
    label: 'Average Rating',
    color: 'hsl(var(--chart-5))',
  },
};

export function BottomPerformersChart({ tutorMetrics }: BottomPerformersChartProps) {
  // Filter for 30-day window and sort by avg_rating (ascending for bottom performers)
  const thirtyDayMetrics = tutorMetrics.filter((m) => m.window === '30day');
  const sorted = [...thirtyDayMetrics].sort((a, b) => a.avg_rating - b.avg_rating);
  const bottom5 = sorted.slice(0, 5);

  const data = bottom5.map((m) => ({
    name: m.tutor_name,
    score: Number((m.avg_rating * 20).toFixed(1)), // Convert 0-5 rating to 0-100 scale
    originalRating: m.avg_rating,
    sessions: m.sessions_completed,
    tier: m.performance_tier,
  }));

  if (data.length === 0) {
    return (
      <div className="flex h-[280px] items-center justify-center text-muted-foreground">
        No performance data available
      </div>
    );
  }

  return (
    <ChartContainer config={chartConfig} className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis dataKey="name" className="text-xs" tick={{ fill: 'hsl(var(--foreground))' }} />
          <YAxis domain={[0, 100]} className="text-xs" tick={{ fill: 'hsl(var(--foreground))' }} />
          <ChartTooltip
            content={
              <ChartTooltipContent
                formatter={(value, name, item) => (
                  <>
                    <div className="text-sm font-medium">{item.payload.name}</div>
                    <div className="flex items-baseline gap-0.5 font-mono font-medium tabular-nums text-foreground">
                      {item.payload.originalRating.toFixed(2)}
                      <span className="font-normal text-muted-foreground">/5.0</span>
                    </div>
                    <div className="text-xs text-muted-foreground">Tier: {item.payload.tier}</div>
                    <div className="text-xs text-muted-foreground">{item.payload.sessions} sessions</div>
                  </>
                )}
              />
            }
          />
          <Bar dataKey="score" radius={[4, 4, 0, 0]} animationBegin={0} animationDuration={800}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill="hsl(var(--chart-5))" />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}
