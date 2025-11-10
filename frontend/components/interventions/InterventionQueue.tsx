'use client';

/**
 * My Intervention Queue Component (Subtask 16.1)
 *
 * Displays pending interventions with SLA indicators and highlights
 * interventions nearing their deadlines.
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, Clock, User, Calendar } from 'lucide-react';
import type { Intervention } from '@/types/intervention';
import {
  formatInterventionType,
  getInterventionTypeBadgeColor,
  getStatusBadgeVariant,
} from '@/types/intervention';
import { formatDistanceToNow, parseISO, format } from 'date-fns';

interface InterventionQueueProps {
  interventions: Intervention[];
  onAssign?: (interventionId: string) => void;
  onUpdateStatus?: (interventionId: string, status: string) => void;
  loading?: boolean;
}

export function InterventionQueue({
  interventions,
  onAssign,
  onUpdateStatus,
  loading = false,
}: InterventionQueueProps) {
  const router = useRouter();

  // Sort interventions: overdue first, then by due date
  const sortedInterventions = React.useMemo(() => {
    return [...interventions].sort((a, b) => {
      // Overdue items first
      if (a.is_overdue && !b.is_overdue) return -1;
      if (!a.is_overdue && b.is_overdue) return 1;

      // Then by due date
      if (a.due_date && b.due_date) {
        return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
      }

      // Items with due dates before those without
      if (a.due_date && !b.due_date) return -1;
      if (!a.due_date && b.due_date) return 1;

      return 0;
    });
  }, [interventions]);

  const getSLAIndicator = (intervention: Intervention) => {
    if (!intervention.due_date) return null;

    const slaPercentage = intervention.sla_percentage || 0;
    const isOverdue = intervention.is_overdue;
    const daysUntilDue = intervention.days_until_due || 0;

    let color = 'bg-green-500';
    let urgencyText = 'On track';

    if (isOverdue) {
      color = 'bg-red-500';
      urgencyText = 'Overdue';
    } else if (slaPercentage > 80) {
      color = 'bg-orange-500';
      urgencyText = 'Urgent';
    } else if (slaPercentage > 60) {
      color = 'bg-yellow-500';
      urgencyText = 'Approaching';
    }

    return (
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1">
          <div className={`h-2 w-2 rounded-full ${color}`} />
          <span className="text-xs text-muted-foreground">{urgencyText}</span>
        </div>
        {!isOverdue && daysUntilDue !== undefined && (
          <span className="text-xs text-muted-foreground">
            {daysUntilDue === 0
              ? 'Due today'
              : daysUntilDue === 1
              ? 'Due tomorrow'
              : `${daysUntilDue} days`}
          </span>
        )}
        {isOverdue && daysUntilDue !== undefined && (
          <span className="text-xs text-red-600 font-medium">
            {Math.abs(daysUntilDue)} days overdue
          </span>
        )}
      </div>
    );
  };

  const handleRowClick = (interventionId: string) => {
    router.push(`/interventions/${interventionId}`);
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>My Intervention Queue</CardTitle>
          <CardDescription>Loading interventions...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (sortedInterventions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>My Intervention Queue</CardTitle>
          <CardDescription>No interventions found</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <Clock className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-sm text-muted-foreground">
              You have no pending interventions at the moment.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>My Intervention Queue</CardTitle>
        <CardDescription>
          {sortedInterventions.length} intervention{sortedInterventions.length !== 1 ? 's' : ''} •{' '}
          {sortedInterventions.filter((i) => i.is_overdue).length} overdue
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tutor</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>SLA</TableHead>
                <TableHead>Due Date</TableHead>
                <TableHead>Assigned To</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedInterventions.map((intervention) => (
                <TableRow
                  key={intervention.intervention_id}
                  className={`cursor-pointer hover:bg-muted/50 ${
                    intervention.is_overdue ? 'bg-red-50 hover:bg-red-100/50' : ''
                  }`}
                  onClick={() => handleRowClick(intervention.intervention_id)}
                >
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      {intervention.is_overdue && (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      )}
                      <div>
                        <div>{intervention.tutor_name || intervention.tutor_id}</div>
                        <div className="text-xs text-muted-foreground">
                          {intervention.tutor_id}
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={getInterventionTypeBadgeColor(intervention.intervention_type)}
                    >
                      {formatInterventionType(intervention.intervention_type)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusBadgeVariant(intervention.status)}>
                      {intervention.status.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell>{getSLAIndicator(intervention)}</TableCell>
                  <TableCell>
                    {intervention.due_date ? (
                      <div className="flex items-center gap-1 text-sm">
                        <Calendar className="h-3 w-3" />
                        {format(parseISO(intervention.due_date), 'MMM d, yyyy')}
                      </div>
                    ) : (
                      <span className="text-muted-foreground text-sm">Not set</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {intervention.assigned_to ? (
                      <div className="flex items-center gap-1 text-sm">
                        <User className="h-3 w-3" />
                        {intervention.assigned_to}
                      </div>
                    ) : (
                      <span className="text-muted-foreground text-sm">Unassigned</span>
                    )}
                  </TableCell>
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    <div className="flex gap-2">
                      {!intervention.assigned_to && onAssign && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onAssign(intervention.intervention_id)}
                        >
                          Assign
                        </Button>
                      )}
                      {intervention.status === 'pending' && onUpdateStatus && (
                        <Button
                          size="sm"
                          onClick={() =>
                            onUpdateStatus(intervention.intervention_id, 'in_progress')
                          }
                        >
                          Start
                        </Button>
                      )}
                      {intervention.status === 'in_progress' && onUpdateStatus && (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() =>
                            onUpdateStatus(intervention.intervention_id, 'completed')
                          }
                        >
                          Complete
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
