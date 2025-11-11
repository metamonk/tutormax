'use client';

import { Cell, Pie, PieChart, ResponsiveContainer, Legend } from 'recharts';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';

interface PerformanceTierChartProps {
  distribution: {
    'Exemplary': number;
    'Strong': number;
    'Developing': number;
    'Needs Attention': number;
    'At Risk': number;
  };
}

// Use explicit colors that work in dark mode
const TIER_COLORS: Record<string, string> = {
  'Exemplary': '#10b981',    // Green
  'Strong': '#3b82f6',       // Blue
  'Developing': '#f59e0b',   // Amber
  'Needs Attention': '#f97316', // Orange
  'At Risk': '#ef4444',      // Red
};

const chartConfig = {
  count: {
    label: 'Tutors',
  },
  exemplary: {
    label: 'Exemplary',
    color: 'hsl(var(--chart-2))',
  },
  strong: {
    label: 'Strong',
    color: 'hsl(var(--chart-1))',
  },
  developing: {
    label: 'Developing',
    color: 'hsl(var(--chart-4))',
  },
  needsAttention: {
    label: 'Needs Attention',
    color: 'hsl(var(--chart-3))',
  },
  atRisk: {
    label: 'At Risk',
    color: 'hsl(var(--chart-5))',
  },
};

export function PerformanceTierChart({ distribution }: PerformanceTierChartProps) {
  const total = Object.values(distribution).reduce((sum, val) => sum + val, 0);

  const data = [
    {
      tier: 'Exemplary',
      count: distribution['Exemplary'] || 0,
      percentage: total > 0 ? Math.round((distribution['Exemplary'] / total) * 100) : 0
    },
    {
      tier: 'Strong',
      count: distribution['Strong'] || 0,
      percentage: total > 0 ? Math.round((distribution['Strong'] / total) * 100) : 0
    },
    {
      tier: 'Developing',
      count: distribution['Developing'] || 0,
      percentage: total > 0 ? Math.round((distribution['Developing'] / total) * 100) : 0
    },
    {
      tier: 'Needs Attention',
      count: distribution['Needs Attention'] || 0,
      percentage: total > 0 ? Math.round((distribution['Needs Attention'] / total) * 100) : 0
    },
    {
      tier: 'At Risk',
      count: distribution['At Risk'] || 0,
      percentage: total > 0 ? Math.round((distribution['At Risk'] / total) * 100) : 0
    },
  ].filter(item => item.count > 0); // Only show tiers with tutors

  return (
    <ChartContainer config={chartConfig} className="mx-auto aspect-square max-h-[350px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart margin={{ top: 0, right: 0, bottom: 60, left: 0 }}>
          <ChartTooltip
            content={
              <ChartTooltipContent
                hideLabel
                formatter={(value, name, item) => (
                  <>
                    <div className="flex items-center gap-2">
                      <div
                        className="h-2.5 w-2.5 shrink-0 rounded-[2px]"
                        style={{
                          backgroundColor: item.payload.fill,
                        }}
                      />
                      {item.payload.tier}
                    </div>
                    <div className="ml-auto flex items-baseline gap-0.5 font-mono font-medium tabular-nums text-foreground">
                      {value}
                      <span className="font-normal text-muted-foreground">tutors</span>
                    </div>
                    <div className="text-xs text-muted-foreground">{item.payload.percentage}% of total</div>
                  </>
                )}
              />
            }
          />
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
            dataKey="count"
            animationBegin={0}
            animationDuration={800}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={TIER_COLORS[entry.tier] || '#6b7280'} />
            ))}
          </Pie>
          <Legend
            verticalAlign="bottom"
            height={48}
            content={({ payload }) => (
              <div className="flex flex-wrap justify-center gap-4 pt-4 px-2">
                {data.map((entry, index) => (
                  <div key={`legend-${index}`} className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-sm" style={{ backgroundColor: TIER_COLORS[entry.tier] }} />
                    <span className="text-sm text-muted-foreground whitespace-nowrap">{entry.tier}</span>
                  </div>
                ))}
              </div>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}
