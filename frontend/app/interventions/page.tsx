'use client';

/**
 * Intervention Management Page
 *
 * Main page for operations managers to view, assign, track, and complete
 * interventions for at-risk tutors.
 */

import React from 'react';
import { InterventionQueue } from '@/components/interventions/InterventionQueue';
import { AssignInterventionDialog } from '@/components/interventions/AssignInterventionDialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { RefreshCw, Users, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { InterventionAPI } from '@/lib/api/interventions';
import type { Intervention, InterventionStats, InterventionStatus } from '@/types/intervention';
import { toast } from 'sonner';

export default function InterventionsPage() {
  const [interventions, setInterventions] = React.useState<Intervention[]>([]);
  const [stats, setStats] = React.useState<InterventionStats | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [activeTab, setActiveTab] = React.useState<InterventionStatus | 'all'>('all');
  const [assignDialogOpen, setAssignDialogOpen] = React.useState(false);
  const [selectedIntervention, setSelectedIntervention] = React.useState<Intervention | null>(null);
  const [filterType, setFilterType] = React.useState<string>('all');

  // Fetch interventions
  const fetchInterventions = React.useCallback(async () => {
    setLoading(true);
    try {
      const params: any = {};

      if (activeTab !== 'all') {
        params.status = activeTab;
      }

      if (filterType !== 'all') {
        params.intervention_type = filterType;
      }

      const data = await InterventionAPI.getInterventions(params);
      setInterventions(data);
    } catch (error) {
      console.error('Failed to fetch interventions:', error);
      toast.error('Failed to load interventions');
    } finally {
      setLoading(false);
    }
  }, [activeTab, filterType]);

  // Fetch stats
  const fetchStats = React.useCallback(async () => {
    try {
      const data = await InterventionAPI.getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, []);

  // Initial load
  React.useEffect(() => {
    fetchInterventions();
    fetchStats();
  }, [fetchInterventions, fetchStats]);

  // Auto-refresh every 30 seconds
  React.useEffect(() => {
    const interval = setInterval(() => {
      fetchInterventions();
      fetchStats();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchInterventions, fetchStats]);

  // Handle assign
  const handleAssign = (interventionId: string) => {
    const intervention = interventions.find((i) => i.intervention_id === interventionId);
    if (intervention) {
      setSelectedIntervention(intervention);
      setAssignDialogOpen(true);
    }
  };

  // Handle assign submit
  const handleAssignSubmit = async (interventionId: string, assignedTo: string) => {
    try {
      await InterventionAPI.assignIntervention(interventionId, { assigned_to: assignedTo });
      toast.success('Intervention assigned successfully');
      fetchInterventions();
      fetchStats();
    } catch (error) {
      console.error('Failed to assign intervention:', error);
      toast.error('Failed to assign intervention');
      throw error;
    }
  };

  // Handle status update
  const handleUpdateStatus = async (interventionId: string, status: string) => {
    try {
      await InterventionAPI.updateStatus(interventionId, { status: status as InterventionStatus });
      toast.success(`Intervention ${status === 'in_progress' ? 'started' : 'updated'} successfully`);
      fetchInterventions();
      fetchStats();
    } catch (error) {
      console.error('Failed to update status:', error);
      toast.error('Failed to update status');
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Intervention Management</h1>
          <p className="text-muted-foreground">
            Monitor and manage interventions for at-risk tutors
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            fetchInterventions();
            fetchStats();
          }}
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Interventions</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
              <p className="text-xs text-muted-foreground">
                {stats.pending} pending • {stats.in_progress} in progress
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Overdue</CardTitle>
              <AlertCircle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.overdue}</div>
              <p className="text-xs text-muted-foreground">Requires immediate attention</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Due This Week</CardTitle>
              <Clock className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">{stats.due_this_week}</div>
              <p className="text-xs text-muted-foreground">{stats.due_today} due today</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
              <p className="text-xs text-muted-foreground">Successfully resolved</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Filter by Type:</span>
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="w-[240px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="automated_coaching">Automated Coaching</SelectItem>
              <SelectItem value="training_module">Training Module</SelectItem>
              <SelectItem value="manager_coaching">Manager Coaching</SelectItem>
              <SelectItem value="peer_mentoring">Peer Mentoring</SelectItem>
              <SelectItem value="performance_improvement_plan">Performance Improvement Plan</SelectItem>
              <SelectItem value="retention_interview">Retention Interview</SelectItem>
              <SelectItem value="recognition">Recognition</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Interventions Table with Tabs */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as InterventionStatus | 'all')}>
        <TabsList>
          <TabsTrigger value="all">
            All
            {stats && <Badge variant="secondary" className="ml-2">{stats.total}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="pending">
            Pending
            {stats && <Badge variant="outline" className="ml-2">{stats.pending}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="in_progress">
            In Progress
            {stats && <Badge variant="default" className="ml-2">{stats.in_progress}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="completed">
            Completed
            {stats && <Badge variant="secondary" className="ml-2">{stats.completed}</Badge>}
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          <InterventionQueue
            interventions={interventions}
            onAssign={handleAssign}
            onUpdateStatus={handleUpdateStatus}
            loading={loading}
          />
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <AssignInterventionDialog
        open={assignDialogOpen}
        onOpenChange={setAssignDialogOpen}
        intervention={selectedIntervention}
        onAssign={handleAssignSubmit}
      />
    </div>
  );
}
