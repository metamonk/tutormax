'use client';

/**
 * Performance Tiers Component
 * Displays performance tier distribution with interactive filtering
 */

import React, { useMemo, useState } from 'react';
import type { TutorMetrics, PerformanceAnalytics } from '@/lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Pill, PillIndicator, PillStatus } from '@/components/kibo-ui/pill';
import { Users, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PerformanceTiersProps {
  analytics: PerformanceAnalytics | null;
  tutorMetrics: TutorMetrics[];
  onTierClick?: (tier: string | null) => void;
}

type TierDefinition = {
  name: 'Platinum' | 'Gold' | 'Silver' | 'Bronze';
  displayName: string;
  description: string;
  minScore: number;
  maxScore: number;
  variant: 'success' | 'warning' | 'error' | 'info';
  bgColor: string;
  textColor: string;
  icon: typeof TrendingUp;
};

const TIER_DEFINITIONS: TierDefinition[] = [
  {
    name: 'Platinum',
    displayName: 'Platinum',
    description: 'Exceptional performance (≥90%)',
    minScore: 90,
    maxScore: 100,
    variant: 'success',
    bgColor: 'bg-gradient-to-r from-purple-500 to-purple-700',
    textColor: 'text-purple-900 dark:text-purple-100',
    icon: TrendingUp,
  },
  {
    name: 'Gold',
    displayName: 'Gold',
    description: 'Strong performance (80-89%)',
    minScore: 80,
    maxScore: 89,
    variant: 'success',
    bgColor: 'bg-gradient-to-r from-yellow-400 to-yellow-600',
    textColor: 'text-yellow-900 dark:text-yellow-100',
    icon: TrendingUp,
  },
  {
    name: 'Silver',
    displayName: 'Silver',
    description: 'Developing performance (70-79%)',
    minScore: 70,
    maxScore: 79,
    variant: 'warning',
    bgColor: 'bg-gradient-to-r from-gray-400 to-gray-600',
    textColor: 'text-gray-900 dark:text-gray-100',
    icon: Minus,
  },
  {
    name: 'Bronze',
    displayName: 'Bronze',
    description: 'Needs support (<70%)',
    minScore: 0,
    maxScore: 69,
    variant: 'error',
    bgColor: 'bg-gradient-to-r from-orange-600 to-orange-800',
    textColor: 'text-orange-900 dark:text-orange-100',
    icon: TrendingDown,
  },
];

// Map performance tiers from analytics to our tier system
const mapPerformanceTierToRating = (tier: string): number => {
  const tierMap: Record<string, number> = {
    'Exemplary': 95,
    'Strong': 85,
    'Developing': 75,
    'Needs Support': 60,
  };
  return tierMap[tier] || 0;
};

export function PerformanceTiers({ analytics, tutorMetrics, onTierClick }: PerformanceTiersProps) {
  const [selectedTier, setSelectedTier] = useState<string | null>(null);

  // Calculate tutor counts per tier
  const tierCounts = useMemo(() => {
    if (!analytics) return null;

    // Get 30-day metrics for most accurate tier assessment
    const thirtyDayMetrics = tutorMetrics.filter((m) => m.window === '30day');

    const counts: Record<string, number> = {
      Platinum: 0,
      Gold: 0,
      Silver: 0,
      Bronze: 0,
    };

    thirtyDayMetrics.forEach((metric) => {
      const rating = mapPerformanceTierToRating(metric.performance_tier);

      for (const tierDef of TIER_DEFINITIONS) {
        if (rating >= tierDef.minScore && rating <= tierDef.maxScore) {
          counts[tierDef.name]++;
          break;
        }
      }
    });

    return counts;
  }, [analytics, tutorMetrics]);

  const handleTierClick = (tierName: string) => {
    const newSelectedTier = selectedTier === tierName ? null : tierName;
    setSelectedTier(newSelectedTier);
    onTierClick?.(newSelectedTier);
  };

  if (!analytics || !tierCounts) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Tiers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <p className="text-muted-foreground">Loading tier data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const totalTutors = Object.values(tierCounts).reduce((sum, count) => sum + count, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          Performance Tiers
        </CardTitle>
        <CardDescription>
          Distribution of {totalTutors} tutors across performance levels
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {TIER_DEFINITIONS.map((tier) => {
            const count = tierCounts[tier.name];
            const percentage = totalTutors > 0 ? ((count / totalTutors) * 100).toFixed(1) : '0.0';
            const isSelected = selectedTier === tier.name;
            const Icon = tier.icon;

            return (
              <Card
                key={tier.name}
                className={cn(
                  'cursor-pointer transition-all hover:shadow-lg',
                  isSelected && 'ring-2 ring-primary ring-offset-2'
                )}
                onClick={() => handleTierClick(tier.name)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <Pill variant="secondary" className={cn('font-semibold', tier.textColor)}>
                      <PillIndicator variant={tier.variant} pulse={isSelected} />
                      <PillStatus className="border-r-0">
                        {tier.displayName}
                      </PillStatus>
                    </Pill>
                    <Icon className={cn('h-5 w-5', tier.textColor)} />
                  </div>
                  <CardDescription className="text-xs mt-2">
                    {tier.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold">{count}</span>
                      <span className="text-sm text-muted-foreground">tutors</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={cn('h-full transition-all', tier.bgColor)}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium">{percentage}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {selectedTier && (
          <div className="mt-4 p-4 bg-muted rounded-lg">
            <p className="text-sm text-muted-foreground">
              Showing {tierCounts[selectedTier]} tutors in{' '}
              <span className="font-semibold text-foreground">{selectedTier}</span> tier.
              Click the tier again to clear the filter.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
