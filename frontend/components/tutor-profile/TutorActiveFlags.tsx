'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ActiveFlag } from '@/lib/types';
import { AlertTriangle, AlertCircle, Info, TrendingDown, UserX, Target } from 'lucide-react';

interface TutorActiveFlagsProps {
  flags: ActiveFlag[];
}

export function TutorActiveFlags({ flags }: TutorActiveFlagsProps) {
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'destructive';
      case 'high':
        return 'destructive';
      case 'medium':
        return 'default';
      case 'low':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <AlertTriangle className="h-5 w-5 text-red-600" />;
      case 'high':
        return <AlertCircle className="h-5 w-5 text-orange-600" />;
      case 'medium':
        return <Info className="h-5 w-5 text-yellow-600" />;
      case 'low':
        return <Info className="h-5 w-5 text-blue-600" />;
      default:
        return <Info className="h-5 w-5 text-gray-600" />;
    }
  };

  const getFlagIcon = (flagType: string) => {
    switch (flagType.toLowerCase()) {
      case 'reschedule_pattern':
        return <AlertTriangle className="h-4 w-4" />;
      case 'no_show_risk':
        return <UserX className="h-4 w-4" />;
      case 'engagement_decline':
        return <TrendingDown className="h-4 w-4" />;
      case 'performance_decline':
        return <TrendingDown className="h-4 w-4" />;
      case 'learning_objectives_low':
        return <Target className="h-4 w-4" />;
      case 'first_session_success_low':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const formatFlagType = (flagType: string) => {
    return flagType
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (flags.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Active Flags</CardTitle>
          <CardDescription>No behavioral flags detected</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
            <Target className="h-12 w-12 mb-4 text-green-600 opacity-50" />
            <p className="font-medium text-green-600">All Clear!</p>
            <p className="text-sm">No concerning patterns detected</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Active Flags</CardTitle>
        <CardDescription>{flags.length} behavioral pattern{flags.length !== 1 ? 's' : ''} detected</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {flags.map((flag, idx) => (
            <div
              key={idx}
              className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-start gap-3 flex-1">
                  <div className="mt-0.5">
                    {getSeverityIcon(flag.severity)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {getFlagIcon(flag.flag_type)}
                      <h4 className="font-medium">{formatFlagType(flag.flag_type)}</h4>
                    </div>
                    <p className="text-sm text-muted-foreground">{flag.description}</p>
                  </div>
                </div>
                <Badge variant={getSeverityColor(flag.severity)} className="ml-4 capitalize">
                  {flag.severity}
                </Badge>
              </div>

              <div className="flex items-center justify-between mt-3 pt-3 border-t text-xs text-muted-foreground">
                <span>Detected: {formatDate(flag.detected_date)}</span>
                {flag.metric_value !== undefined && (
                  <span className="font-mono bg-muted px-2 py-1 rounded">
                    Value: {flag.metric_value.toFixed(2)}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
