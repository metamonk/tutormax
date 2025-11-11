'use client';

/**
 * Intervention Effectiveness Component
 *
 * Shows effectiveness metrics for different intervention types
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, Clock, TrendingUp } from 'lucide-react';

interface InterventionData {
  intervention_type: string;
  total_interventions: number;
  completion_rate: number;
  success_rate: number;
  churn_rate: number;
  avg_time_to_complete_days: number | null;
  effectiveness_score: number;
}

interface InterventionEffectivenessData {
  interventions: InterventionData[];
  summary: {
    total_interventions: number;
    date_range: {
      start: string;
      end: string;
    };
  };
}

export function InterventionEffectiveness({ summary = false }: { summary?: boolean }) {
  const [data, setData] = useState<InterventionEffectivenessData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/analytics/intervention-effectiveness');

        if (!response.ok) {
          throw new Error(`Failed to fetch intervention effectiveness: ${response.status} ${response.statusText}`);
        }

        const effectiveness = await response.json();
        setData(effectiveness);
      } catch (error) {
        console.error('Failed to fetch intervention effectiveness:', error);
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
          <CardTitle>Intervention Effectiveness</CardTitle>
          <CardDescription>Loading effectiveness data...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const formatInterventionType = (type: string): string => {
    return type
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getEffectivenessColor = (score: number): string => {
    if (score >= 70) return 'text-green-600';
    if (score >= 50) return 'text-blue-600';
    if (score >= 30) return 'text-orange-600';
    return 'text-red-600';
  };

  const displayData = summary ? data.interventions.slice(0, 3) : data.interventions;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Intervention Effectiveness</CardTitle>
        <CardDescription>
          Performance metrics for intervention strategies
          <span className="ml-2 text-xs">
            (Total: {data.summary.total_interventions} interventions)
          </span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {displayData.map((intervention, index) => (
            <div key={index} className="space-y-3 pb-6 border-b last:border-b-0 last:pb-0">
              {/* Header */}
              <div className="flex items-center justify-between">
                <h4 className="font-semibold">
                  {formatInterventionType(intervention.intervention_type)}
                </h4>
                <Badge variant="outline">
                  {intervention.total_interventions} total
                </Badge>
              </div>

              {/* Effectiveness Score */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Effectiveness Score</span>
                <span className={`text-2xl font-bold ${getEffectivenessColor(intervention.effectiveness_score)}`}>
                  {intervention.effectiveness_score.toFixed(1)}
                </span>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <div>
                    <div className="font-medium">{intervention.completion_rate.toFixed(1)}%</div>
                    <div className="text-xs text-muted-foreground">Completion</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-blue-600" />
                  <div>
                    <div className="font-medium">{intervention.success_rate.toFixed(1)}%</div>
                    <div className="text-xs text-muted-foreground">Success</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-red-600" />
                  <div>
                    <div className="font-medium">{intervention.churn_rate.toFixed(1)}%</div>
                    <div className="text-xs text-muted-foreground">Churn</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-orange-600" />
                  <div>
                    <div className="font-medium">
                      {intervention.avg_time_to_complete_days?.toFixed(0) || 'N/A'} days
                    </div>
                    <div className="text-xs text-muted-foreground">Avg Time</div>
                  </div>
                </div>
              </div>

              {/* Progress Bars */}
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">Success Rate</span>
                    <span>{intervention.success_rate.toFixed(1)}%</span>
                  </div>
                  <Progress value={intervention.success_rate} className="h-2" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {summary && data.interventions.length > 3 && (
          <div className="mt-4 text-center">
            <button className="text-sm text-blue-600 hover:underline">
              View all {data.interventions.length} intervention types →
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
