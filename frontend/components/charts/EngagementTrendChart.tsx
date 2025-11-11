'use client';

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';

interface EngagementTrendChartProps {
  avgEngagementScore: number;
}

const chartConfig = {
  score: {
    label: 'Engagement Score',
    color: 'hsl(var(--chart-3))',
  },
};

export function EngagementTrendChart({ avgEngagementScore }: EngagementTrendChartProps) {
  // Generate trend data around the current average (simulated historical data)
  // In a real implementation, this would come from historical analytics data
  const data = [
    { day: 'Day 1', score: avgEngagementScore * 0.92 },
    { day: 'Day 2', score: avgEngagementScore * 0.94 },
    { day: 'Day 3', score: avgEngagementScore * 0.96 },
    { day: 'Day 4', score: avgEngagementScore * 0.95 },
    { day: 'Day 5', score: avgEngagementScore * 0.97 },
    { day: 'Day 6', score: avgEngagementScore * 0.99 },
    { day: 'Today', score: avgEngagementScore },
  ];

  return (
    <ChartContainer config={chartConfig} className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(var(--chart-3))" stopOpacity={0.3} />
              <stop offset="95%" stopColor="hsl(var(--chart-3))" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis dataKey="day" className="text-xs" tick={{ fill: 'hsl(var(--foreground))' }} />
          <YAxis domain={[0, 100]} className="text-xs" tick={{ fill: 'hsl(var(--foreground))' }} />
          <ChartTooltip
            content={
              <ChartTooltipContent
                formatter={(value) => (
                  <div className="flex items-baseline gap-0.5 font-mono font-medium tabular-nums text-foreground">
                    {Number(value).toFixed(1)}
                    <span className="font-normal text-muted-foreground">%</span>
                  </div>
                )}
              />
            }
          />
          <Area
            type="monotone"
            dataKey="score"
            stroke="hsl(var(--chart-3))"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorScore)"
            animationBegin={0}
            animationDuration={1000}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}
