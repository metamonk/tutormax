'use client';

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import type { TutorMetrics } from '@/lib/types';

interface TopPerformersChartProps {
  tutorMetrics: TutorMetrics[];
}

const chartConfig = {
  score: {
    label: 'Average Rating',
    color: 'hsl(var(--chart-1))',
  },
};

export function TopPerformersChart({ tutorMetrics }: TopPerformersChartProps) {
  // Filter for 30-day window and sort by avg_rating
  const thirtyDayMetrics = tutorMetrics.filter((m) => m.window === '30day');
  const sorted = [...thirtyDayMetrics].sort((a, b) => b.avg_rating - a.avg_rating);
  const top5 = sorted.slice(0, 5);

  const data = top5.map((m) => ({
    name: m.tutor_name,
    score: Number((m.avg_rating * 20).toFixed(1)), // Convert 0-5 rating to 0-100 scale
    originalRating: m.avg_rating,
    sessions: m.sessions_completed,
  }));

  if (data.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-muted-foreground">
        No performance data available
      </div>
    );
  }

  return (
    <ChartContainer config={chartConfig} className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" horizontal={false} />
          <XAxis type="number" domain={[0, 100]} className="text-xs" />
          <YAxis
            dataKey="name"
            type="category"
            width={120}
            className="text-xs"
            tick={{ fill: 'hsl(var(--foreground))' }}
          />
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
                    <div className="text-xs text-muted-foreground">{item.payload.sessions} sessions completed</div>
                  </>
                )}
              />
            }
          />
          <Bar
            dataKey="score"
            fill="hsl(var(--chart-1))"
            radius={[0, 4, 4, 0]}
            animationBegin={0}
            animationDuration={800}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}
