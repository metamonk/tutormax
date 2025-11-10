'use client';

/**
 * SLA Timer and Alerts Component (Subtask 16.4)
 *
 * Displays countdown timers for intervention SLAs and alerts
 * when approaching deadlines.
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, Clock, AlertCircle, CheckCircle } from 'lucide-react';
import type { Intervention } from '@/types/intervention';
import { formatDistanceToNow, parseISO, differenceInHours, differenceInMinutes } from 'date-fns';

interface SLATimerProps {
  intervention: Intervention;
  showAlert?: boolean;
}

export function SLATimer({ intervention, showAlert = true }: SLATimerProps) {
  const [currentTime, setCurrentTime] = React.useState(new Date());

  // Update timer every minute
  React.useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  if (!intervention.due_date) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">SLA Tracker</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span className="text-sm">No due date set</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const dueDate = parseISO(intervention.due_date);
  const recommendedDate = intervention.recommended_date
    ? parseISO(intervention.recommended_date)
    : null;
  const isOverdue = intervention.is_overdue;
  const slaPercentage = intervention.sla_percentage || 0;

  // Calculate time remaining
  const hoursRemaining = differenceInHours(dueDate, currentTime);
  const minutesRemaining = differenceInMinutes(dueDate, currentTime) % 60;

  // Determine urgency level
  const getUrgencyLevel = (): 'critical' | 'urgent' | 'warning' | 'normal' => {
    if (isOverdue) return 'critical';
    if (slaPercentage > 90 || hoursRemaining < 4) return 'urgent';
    if (slaPercentage > 75 || hoursRemaining < 24) return 'warning';
    return 'normal';
  };

  const urgencyLevel = getUrgencyLevel();

  const urgencyConfig = {
    critical: {
      color: 'text-red-600',
      bgColor: 'bg-red-600',
      badgeVariant: 'destructive' as const,
      icon: AlertCircle,
      label: 'OVERDUE',
    },
    urgent: {
      color: 'text-orange-600',
      bgColor: 'bg-orange-600',
      badgeVariant: 'destructive' as const,
      icon: AlertTriangle,
      label: 'URGENT',
    },
    warning: {
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-600',
      badgeVariant: 'default' as const,
      icon: Clock,
      label: 'DUE SOON',
    },
    normal: {
      color: 'text-green-600',
      bgColor: 'bg-green-600',
      badgeVariant: 'secondary' as const,
      icon: CheckCircle,
      label: 'ON TRACK',
    },
  };

  const config = urgencyConfig[urgencyLevel];
  const UrgencyIcon = config.icon;

  const formatTimeRemaining = (): string => {
    if (isOverdue) {
      const overdueDays = Math.abs(intervention.days_until_due || 0);
      if (overdueDays === 0) return 'Overdue today';
      if (overdueDays === 1) return '1 day overdue';
      return `${overdueDays} days overdue`;
    }

    if (hoursRemaining < 1) {
      return `${minutesRemaining} minutes remaining`;
    }

    if (hoursRemaining < 24) {
      return `${hoursRemaining} hours remaining`;
    }

    const daysRemaining = Math.floor(hoursRemaining / 24);
    if (daysRemaining === 1) return '1 day remaining';
    return `${daysRemaining} days remaining`;
  };

  return (
    <div className="space-y-4">
      {/* Alert Banner */}
      {showAlert && (urgencyLevel === 'critical' || urgencyLevel === 'urgent') && (
        <Alert variant={urgencyLevel === 'critical' ? 'destructive' : 'default'}>
          <UrgencyIcon className="h-4 w-4" />
          <AlertTitle>{config.label}</AlertTitle>
          <AlertDescription>
            {isOverdue
              ? `This intervention is ${formatTimeRemaining()}. Immediate action required.`
              : `This intervention is due ${formatDistanceToNow(dueDate, { addSuffix: true })}. Please prioritize.`}
          </AlertDescription>
        </Alert>
      )}

      {/* SLA Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">SLA Tracker</CardTitle>
            <Badge variant={config.badgeVariant} className="flex items-center gap-1">
              <UrgencyIcon className="h-3 w-3" />
              {config.label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Timer Display */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className={`h-5 w-5 ${config.color}`} />
              <div>
                <div className="text-sm font-medium">Time {isOverdue ? 'Overdue' : 'Remaining'}</div>
                <div className={`text-2xl font-bold ${config.color}`}>
                  {formatTimeRemaining()}
                </div>
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>SLA Progress</span>
              <span>{Math.min(100, Math.round(slaPercentage))}%</span>
            </div>
            <Progress
              value={Math.min(100, slaPercentage)}
              className={`h-2 ${
                isOverdue
                  ? '[&>div]:bg-red-600'
                  : slaPercentage > 90
                  ? '[&>div]:bg-orange-600'
                  : slaPercentage > 75
                  ? '[&>div]:bg-yellow-600'
                  : '[&>div]:bg-green-600'
              }`}
            />
          </div>

          {/* Date Information */}
          <div className="space-y-2 pt-2 border-t">
            {recommendedDate && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Created:</span>
                <span className="font-medium">
                  {new Date(recommendedDate).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
            )}
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Due Date:</span>
              <span className={`font-medium ${isOverdue ? config.color : ''}`}>
                {new Date(dueDate).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
