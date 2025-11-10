'use client';

/**
 * Intervention Task List Component
 * Displays and manages intervention tasks for tutors
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import type { InterventionTask } from '@/lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Target, BookOpen, ClipboardList, RotateCw } from 'lucide-react';

interface InterventionTaskListProps {
  tasks: InterventionTask[];
  onUpdateStatus: (taskId: string, status: 'pending' | 'in_progress' | 'completed') => void;
}

export function InterventionTaskList({ tasks, onUpdateStatus }: InterventionTaskListProps) {
  const router = useRouter();
  const pendingTasks = tasks.filter((task) => task.status === 'pending');
  const inProgressTasks = tasks.filter((task) => task.status === 'in_progress');
  const completedTasks = tasks.filter((task) => task.status === 'completed');

  const getPriorityVariant = (priority: string) => {
    const variants = {
      high: 'destructive',
      medium: 'default',
      low: 'secondary',
    };
    return variants[priority as keyof typeof variants] || 'secondary';
  };

  const getTaskTypeIcon = (type: string) => {
    switch (type) {
      case 'coaching':
        return <Target className="h-4 w-4" />;
      case 'training':
        return <BookOpen className="h-4 w-4" />;
      case 'review':
        return <ClipboardList className="h-4 w-4" />;
      case 'followup':
        return <RotateCw className="h-4 w-4" />;
      default:
        return <ClipboardList className="h-4 w-4" />;
    }
  };

  const formatDueDate = (dueDate: string) => {
    const date = new Date(dueDate);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return `${Math.abs(diffDays)} days overdue`;
    if (diffDays === 0) return 'Due today';
    if (diffDays === 1) return 'Due tomorrow';
    return `Due in ${diffDays} days`;
  };

  const renderTaskCard = (task: InterventionTask) => (
    <Card key={task.id} className="mb-3">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-2">
            {getTaskTypeIcon(task.task_type)}
            <div>
              <CardTitle className="text-sm font-semibold">{task.title}</CardTitle>
              <CardDescription className="text-xs">{task.tutor_name}</CardDescription>
            </div>
          </div>
          <Badge variant={getPriorityVariant(task.priority) as any}>
            {task.priority}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">{task.description}</p>

        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className={diffDays(task.due_date) < 0 ? 'text-red-600 font-medium' : ''}>
            {formatDueDate(task.due_date)}
          </span>
          {task.assigned_to && <span>Assigned to: {task.assigned_to}</span>}
        </div>

        <div className="flex gap-2">
          {task.status === 'pending' && (
            <Button
              size="sm"
              className="w-full"
              onClick={() => onUpdateStatus(task.id, 'in_progress')}
            >
              Start Task
            </Button>
          )}
          {task.status === 'in_progress' && (
            <Button
              size="sm"
              className="w-full"
              onClick={() => onUpdateStatus(task.id, 'completed')}
            >
              Complete
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={() => router.push(`/tutor/profile?tutor=${task.tutor_id}`)}
          >
            View Profile
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const diffDays = (dueDate: string) => {
    const date = new Date(dueDate);
    const now = new Date();
    return Math.floor((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Intervention Tasks</CardTitle>
        <CardDescription>
          {pendingTasks.length} pending, {inProgressTasks.length} in progress
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Pending Column */}
          <div className="space-y-2">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm">Pending</h3>
              <Badge variant="secondary">{pendingTasks.length}</Badge>
            </div>
            <div className="space-y-2">
              {pendingTasks.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No pending tasks
                </p>
              ) : (
                pendingTasks.map(renderTaskCard)
              )}
            </div>
          </div>

          {/* In Progress Column */}
          <div className="space-y-2">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm">In Progress</h3>
              <Badge variant="default">{inProgressTasks.length}</Badge>
            </div>
            <div className="space-y-2">
              {inProgressTasks.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No tasks in progress
                </p>
              ) : (
                inProgressTasks.map(renderTaskCard)
              )}
            </div>
          </div>

          {/* Completed Column */}
          <div className="space-y-2">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm">Completed</h3>
              <Badge variant="outline">{completedTasks.length}</Badge>
            </div>
            <div className="space-y-2">
              {completedTasks.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No completed tasks
                </p>
              ) : (
                completedTasks.map(renderTaskCard)
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
