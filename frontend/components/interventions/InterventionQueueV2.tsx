'use client';

/**
 * Improved Intervention Queue Component (Task 8)
 *
 * Modern task management interface with multiple views:
 * - Table view: Traditional data table with enhanced visualizations
 * - Kanban view: Drag-and-drop board organized by status
 * - List view: Grouped list with drag-and-drop
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Clock, User, Calendar, LayoutGrid, List, Table as TableIcon } from 'lucide-react';
import type { Intervention, InterventionStatus } from '@/types/intervention';
import {
  formatInterventionType,
  getInterventionTypeBadgeColor,
} from '@/types/intervention';
import { format, parseISO } from 'date-fns';
import { TableSkeleton } from '@/components/ui/skeleton-patterns';
import {
  KanbanProvider,
  KanbanBoard,
  KanbanHeader,
  KanbanCards,
  KanbanCard,
  type DragEndEvent,
} from '@/components/kibo-ui/kanban';
import { cn } from '@/lib/utils';

interface InterventionQueueV2Props {
  interventions: Intervention[];
  onAssign?: (interventionId: string) => void;
  onUpdateStatus?: (interventionId: string, status: string) => void;
  loading?: boolean;
}

type ViewMode = 'table' | 'kanban';

export function InterventionQueueV2({
  interventions,
  onAssign,
  onUpdateStatus,
  loading = false,
}: InterventionQueueV2Props) {
  const router = useRouter();
  const [viewMode, setViewMode] = React.useState<ViewMode>('table');

  // Sort interventions: overdue first, then by due date
  const sortedInterventions = React.useMemo(() => {
    return [...interventions].sort((a, b) => {
      if (a.is_overdue && !b.is_overdue) return -1;
      if (!a.is_overdue && b.is_overdue) return 1;
      if (a.due_date && b.due_date) {
        return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
      }
      if (a.due_date && !b.due_date) return -1;
      if (!a.due_date && b.due_date) return 1;
      return 0;
    });
  }, [interventions]);

  // Kanban columns
  const kanbanColumns = [
    { id: 'pending', name: 'Pending' },
    { id: 'in_progress', name: 'In Progress' },
    { id: 'completed', name: 'Completed' },
  ];

  // Transform interventions for kanban
  const kanbanData = React.useMemo(() => {
    return sortedInterventions
      .filter((i) => i.status !== 'cancelled')
      .map((intervention) => ({
        id: intervention.intervention_id,
        name: intervention.tutor_name || intervention.tutor_id,
        column: intervention.status,
        intervention: intervention,
      }));
  }, [sortedInterventions]);

  type KanbanItem = typeof kanbanData[number];

  // Get status badge variant with semantic colors
  const getStatusBadgeVariant = (
    status: InterventionStatus
  ): 'default' | 'secondary' | 'outline' | 'success' | 'warning' | 'destructive' => {
    switch (status) {
      case 'pending':
        return 'outline';
      case 'in_progress':
        return 'default';
      case 'completed':
        return 'success';
      case 'cancelled':
        return 'destructive';
      default:
        return 'default';
    }
  };

  // Get SLA indicator with semantic colors
  const getSLAIndicator = (intervention: Intervention) => {
    if (!intervention.due_date) {
      return (
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-muted" />
          <span className="text-xs text-muted-foreground">No due date</span>
        </div>
      );
    }

    const slaPercentage = intervention.sla_percentage || 0;
    const isOverdue = intervention.is_overdue;
    const daysUntilDue = intervention.days_until_due || 0;

    let colorClass = 'bg-success';
    let urgencyText = 'On track';
    let urgencyTextClass = 'text-muted-foreground';

    if (isOverdue) {
      colorClass = 'bg-destructive';
      urgencyText = 'Overdue';
      urgencyTextClass = 'text-destructive font-medium';
    } else if (slaPercentage > 80) {
      colorClass = 'bg-destructive';
      urgencyText = 'Critical';
      urgencyTextClass = 'text-destructive font-medium';
    } else if (slaPercentage > 60) {
      colorClass = 'bg-warning';
      urgencyText = 'Urgent';
      urgencyTextClass = 'text-warning-foreground font-medium';
    } else if (slaPercentage > 40) {
      colorClass = 'bg-warning/60';
      urgencyText = 'Approaching';
      urgencyTextClass = 'text-muted-foreground';
    }

    return (
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5">
          <div className={cn('h-2 w-2 rounded-full', colorClass)} />
          <span className={cn('text-xs', urgencyTextClass)}>{urgencyText}</span>
        </div>
        {!isOverdue && daysUntilDue !== undefined && (
          <span className="text-xs text-muted-foreground">
            {daysUntilDue === 0
              ? '• Due today'
              : daysUntilDue === 1
              ? '• Due tomorrow'
              : `• ${daysUntilDue}d left`}
          </span>
        )}
        {isOverdue && daysUntilDue !== undefined && (
          <span className="text-xs text-destructive font-medium">
            • {Math.abs(daysUntilDue)}d overdue
          </span>
        )}
      </div>
    );
  };

  const handleRowClick = (interventionId: string) => {
    router.push(`/interventions/${interventionId}`);
  };

  const handleKanbanDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || !onUpdateStatus) return;

    const interventionId = active.id as string;
    const newStatus = over.id as string;

    // Find the intervention
    const intervention = interventions.find((i) => i.intervention_id === interventionId);
    if (!intervention || intervention.status === newStatus) return;

    onUpdateStatus(interventionId, newStatus);
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Intervention Queue</CardTitle>
          <CardDescription>Loading interventions...</CardDescription>
        </CardHeader>
        <CardContent>
          <TableSkeleton rows={8} columns={6} />
        </CardContent>
      </Card>
    );
  }

  if (sortedInterventions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Intervention Queue</CardTitle>
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
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Intervention Queue</CardTitle>
            <CardDescription>
              {sortedInterventions.length} intervention{sortedInterventions.length !== 1 ? 's' : ''} •{' '}
              {sortedInterventions.filter((i) => i.is_overdue).length} overdue
            </CardDescription>
          </div>
          <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as ViewMode)}>
            <TabsList>
              <TabsTrigger value="table" className="gap-2">
                <TableIcon className="h-4 w-4" />
                Table
              </TabsTrigger>
              <TabsTrigger value="kanban" className="gap-2">
                <LayoutGrid className="h-4 w-4" />
                Kanban
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </CardHeader>
      <CardContent>
        {/* Table View */}
        {viewMode === 'table' && (
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
                    className={cn(
                      'cursor-pointer hover:bg-muted/50 transition-colors',
                      intervention.is_overdue && 'bg-destructive/5 hover:bg-destructive/10'
                    )}
                    onClick={() => handleRowClick(intervention.intervention_id)}
                  >
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {intervention.is_overdue && (
                          <AlertCircle className="h-4 w-4 text-destructive" />
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
        )}

        {/* Kanban View */}
        {viewMode === 'kanban' && (
          <div className="h-[600px]">
            <KanbanProvider
              columns={kanbanColumns}
              data={kanbanData}
              onDragEnd={handleKanbanDragEnd}
              onDataChange={(newData) => {
                // Handle optimistic UI update if needed
              }}
            >
              {(column) => (
                <KanbanBoard id={column.id} key={column.id}>
                  <KanbanHeader>{column.name}</KanbanHeader>
                  <KanbanCards id={column.id}>
                    {(item) => {
                      const kanbanItem = item as unknown as KanbanItem;
                      return (
                      <KanbanCard
                        key={kanbanItem.id}
                        id={kanbanItem.id}
                        name={kanbanItem.name}
                        column={kanbanItem.column}
                        className="cursor-pointer"
                        onClick={() => handleRowClick(kanbanItem.intervention.intervention_id)}
                      >
                        <div className="space-y-3">
                          {/* Tutor Info */}
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0 flex-1">
                              <p className="font-medium text-sm truncate">
                                {kanbanItem.intervention.tutor_name || kanbanItem.intervention.tutor_id}
                              </p>
                              <p className="text-xs text-muted-foreground truncate">
                                {kanbanItem.intervention.tutor_id}
                              </p>
                            </div>
                            {kanbanItem.intervention.is_overdue && (
                              <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0" />
                            )}
                          </div>

                          {/* Type Badge */}
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              getInterventionTypeBadgeColor(kanbanItem.intervention.intervention_type)
                            )}
                          >
                            {formatInterventionType(kanbanItem.intervention.intervention_type)}
                          </Badge>

                          {/* SLA Indicator */}
                          {getSLAIndicator(kanbanItem.intervention)}

                          {/* Due Date */}
                          {kanbanItem.intervention.due_date && (
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Calendar className="h-3 w-3" />
                              {format(parseISO(kanbanItem.intervention.due_date), 'MMM d')}
                            </div>
                          )}

                          {/* Assigned To */}
                          {kanbanItem.intervention.assigned_to && (
                            <div className="flex items-center gap-1 text-xs">
                              <User className="h-3 w-3" />
                              <span className="truncate">{kanbanItem.intervention.assigned_to}</span>
                            </div>
                          )}
                        </div>
                      </KanbanCard>
                    );
                    }}
                  </KanbanCards>
                </KanbanBoard>
              )}
            </KanbanProvider>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
