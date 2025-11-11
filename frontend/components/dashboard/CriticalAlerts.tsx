'use client';

/**
 * Critical Alerts Component
 * Displays critical alerts for tutor performance issues
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import type { Alert } from '@/lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertCircle, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';

interface CriticalAlertsProps {
  alerts: Alert[];
  onResolve: (alertId: string) => void;
}

export function CriticalAlerts({ alerts, onResolve }: CriticalAlertsProps) {
  const router = useRouter();
  const unresolvedAlerts = alerts.filter((alert) => !alert.resolved);
  const criticalAlerts = unresolvedAlerts.filter((alert) => alert.alert_type === 'critical');
  const warningAlerts = unresolvedAlerts.filter((alert) => alert.alert_type === 'warning');

  const getSeverityClass = (severity: string) => {
    const classes = {
      high: 'border-red-500 bg-red-50 dark:bg-red-950',
      medium: 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950',
      low: 'border-blue-500 bg-blue-50 dark:bg-blue-950',
    };
    return classes[severity as keyof typeof classes] || '';
  };

  const getAlertTypeIcon = (type: string) => {
    switch (type) {
      case 'critical':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-600" />;
      default:
        return <Info className="h-5 w-5" />;
    }
  };

  const getAlertTypeBadge = (type: string) => {
    const variants = {
      critical: 'destructive',
      warning: 'default',
      info: 'secondary',
    };
    return (
      <Badge variant={variants[type as keyof typeof variants] as any}>
        {type.toUpperCase()}
      </Badge>
    );
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Critical Alerts</CardTitle>
            <CardDescription>
              {criticalAlerts.length} critical, {warningAlerts.length} warnings
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {unresolvedAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <CheckCircle2 className="h-12 w-12 text-green-500 mb-2" />
            <p className="text-muted-foreground">No active alerts. All systems operational.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {unresolvedAlerts.map((alert) => (
              <Card key={alert.id} className={`border-l-4 ${getSeverityClass(alert.severity)}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      {getAlertTypeIcon(alert.alert_type)}
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-base">{alert.title}</CardTitle>
                          {getAlertTypeBadge(alert.alert_type)}
                        </div>
                        <CardDescription className="text-sm">
                          {alert.tutor_name}
                        </CardDescription>
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatTimestamp(alert.timestamp)}
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm mb-4">{alert.message}</p>

                  {alert.metrics && Object.keys(alert.metrics).length > 0 && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-4 p-3 bg-muted rounded-md">
                      {Object.entries(alert.metrics).map(([key, value]) => (
                        <div key={key} className="text-sm">
                          <span className="font-medium">{key}:</span>{' '}
                          <span className="text-muted-foreground">{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => onResolve(alert.id)}
                    >
                      Resolve
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => router.push(`/tutor/${alert.tutor_id}`)}
                    >
                      View Tutor Profile
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
