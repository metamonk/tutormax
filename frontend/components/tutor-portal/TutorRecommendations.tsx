'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TutorRecommendationsResponse } from '@/lib/types';
import { BookOpen, Clock, Target, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface TutorRecommendationsProps {
  data: TutorRecommendationsResponse | null;
  loading?: boolean;
}

export function TutorRecommendations({ data, loading }: TutorRecommendationsProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Training Recommendations</CardTitle>
          <CardDescription>Loading recommendations...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Training Recommendations</CardTitle>
          <CardDescription>Unable to load recommendations</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
      case 'assigned':
        return 'destructive';
      case 'medium':
        return 'default';
      case 'low':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high':
      case 'assigned':
        return <AlertTriangle className="h-4 w-4" />;
      case 'medium':
        return <Target className="h-4 w-4" />;
      case 'low':
        return <BookOpen className="h-4 w-4" />;
      default:
        return <BookOpen className="h-4 w-4" />;
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle>Training Recommendations</CardTitle>
            <CardDescription>{data.message}</CardDescription>
          </div>
          {data.performance_tier && (
            <Badge variant="outline" className="ml-4">
              {data.performance_tier}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {/* Growth Areas */}
        {data.growth_areas.length > 0 && (
          <div className="mb-6 p-4 bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-900 rounded-lg">
            <h4 className="font-medium text-sm mb-2 flex items-center gap-2">
              <Target className="h-4 w-4 text-orange-600" />
              Focus Areas for Growth
            </h4>
            <div className="flex flex-wrap gap-2">
              {data.growth_areas.map((area, idx) => (
                <Badge key={idx} variant="secondary" className="bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200">
                  {area}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations List */}
        <div className="space-y-4">
          {data.recommendations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
              <CheckCircle2 className="h-12 w-12 mb-4 text-green-600 opacity-50" />
              <p className="font-medium">Great job!</p>
              <p className="text-sm">No specific training needed at this time.</p>
            </div>
          ) : (
            data.recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-start gap-3 flex-1">
                    <div className={`mt-0.5 ${rec.priority === 'high' || rec.priority === 'assigned' ? 'text-red-600' : rec.priority === 'medium' ? 'text-blue-600' : 'text-gray-600'}`}>
                      {getPriorityIcon(rec.priority)}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium mb-1">{rec.title}</h4>
                      <p className="text-sm text-muted-foreground">{rec.description}</p>
                    </div>
                  </div>
                  <Badge variant={getPriorityColor(rec.priority)} className="ml-4 capitalize">
                    {rec.priority}
                  </Badge>
                </div>

                <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
                  {rec.estimated_time && (
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      <span>{rec.estimated_time}</span>
                    </div>
                  )}
                  {rec.category && (
                    <Badge variant="outline" className="text-xs">
                      {rec.category.replace('_', ' ')}
                    </Badge>
                  )}
                  {rec.status && (
                    <Badge variant="secondary" className="text-xs capitalize">
                      {rec.status.replace('_', ' ')}
                    </Badge>
                  )}
                </div>

                {rec.due_date && (
                  <div className="mt-3 pt-3 border-t">
                    <p className="text-sm text-muted-foreground">
                      {rec.assigned_date && `Assigned: ${formatDate(rec.assigned_date)} • `}
                      Due: {formatDate(rec.due_date)}
                    </p>
                  </div>
                )}

                {rec.priority === 'assigned' && (
                  <div className="mt-3">
                    <Button size="sm" className="w-full sm:w-auto">
                      Start Training
                    </Button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
