'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { apiClient } from '@/lib/api';
import { Loader2, Target, Plus, Trash2, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

interface Goal {
  goal_id: string;
  goal_type: string;
  title: string;
  description: string;
  target_value: number;
  current_value: number;
  progress_percentage: number;
  target_date: string;
  status: string;
  created_date: string;
}

interface GoalTrackerProps {
  tutorId: string;
}

export function GoalTracker({ tutorId }: GoalTrackerProps) {
  const [loading, setLoading] = useState(true);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [activeGoals, setActiveGoals] = useState(0);
  const [achievedGoals, setAchievedGoals] = useState(0);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Form state
  const [goalType, setGoalType] = useState('rating_improvement');
  const [targetValue, setTargetValue] = useState('');
  const [targetDate, setTargetDate] = useState('');

  useEffect(() => {
    loadGoals();
  }, [tutorId]);

  const loadGoals = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getTutorGoals(tutorId);

      if (response.success) {
        setGoals(response.goals);
        setActiveGoals(response.active_goals);
        setAchievedGoals(response.achieved_goals);
        setRecommendations(response.recommended_goals);
      }
    } catch (error) {
      console.error('Failed to load goals:', error);
      toast.error('Failed to load goals');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGoal = async () => {
    if (!targetValue || !targetDate) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      await apiClient.createTutorGoal(tutorId, {
        goal_type: goalType,
        target_value: parseFloat(targetValue),
        target_date: new Date(targetDate).toISOString(),
      });

      toast.success('Goal created successfully!');
      setCreateDialogOpen(false);
      setGoalType('rating_improvement');
      setTargetValue('');
      setTargetDate('');
      loadGoals();
    } catch (error) {
      console.error('Failed to create goal:', error);
      toast.error('Failed to create goal');
    }
  };

  const handleDeleteGoal = async (goalId: string) => {
    if (!confirm('Are you sure you want to delete this goal?')) {
      return;
    }

    try {
      await apiClient.deleteTutorGoal(tutorId, goalId);
      toast.success('Goal deleted successfully');
      loadGoals();
    } catch (error) {
      console.error('Failed to delete goal:', error);
      toast.error('Failed to delete goal');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'achieved':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'in_progress':
        return <Clock className="w-5 h-5 text-blue-500" />;
      case 'expired':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: { [key: string]: 'default' | 'secondary' | 'destructive' | 'outline' } = {
      achieved: 'default',
      in_progress: 'secondary',
      expired: 'destructive',
      not_started: 'outline',
    };

    return (
      <Badge variant={variants[status] || 'outline'}>
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  if (loading) {
    return (
      <Card className="p-8">
        <div className="flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">{activeGoals}</div>
              <div className="text-sm text-muted-foreground mt-1">Active Goals</div>
            </div>
            <Target className="w-8 h-8 text-blue-500" />
          </div>
        </Card>
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold">{achievedGoals}</div>
              <div className="text-sm text-muted-foreground mt-1">Achieved</div>
            </div>
            <CheckCircle2 className="w-8 h-8 text-green-500" />
          </div>
        </Card>
        <Card className="p-6 flex items-center justify-center">
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="w-full">
                <Plus className="w-4 h-4 mr-2" />
                Create New Goal
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Goal</DialogTitle>
                <DialogDescription>
                  Set a personal development goal to track your progress
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Goal Type</Label>
                  <Select value={goalType} onValueChange={setGoalType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="rating_improvement">Improve Average Rating</SelectItem>
                      <SelectItem value="session_volume">Increase Session Volume</SelectItem>
                      <SelectItem value="on_time_percentage">Improve Punctuality</SelectItem>
                      <SelectItem value="first_session_success">First Session Excellence</SelectItem>
                      <SelectItem value="engagement_score">Enhance Student Engagement</SelectItem>
                      <SelectItem value="custom">Custom Goal</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Target Value</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={targetValue}
                    onChange={(e) => setTargetValue(e.target.value)}
                    placeholder="e.g., 4.5 for rating, 30 for sessions"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Target Date</Label>
                  <Input
                    type="date"
                    value={targetDate}
                    onChange={(e) => setTargetDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateGoal}>Create Goal</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </Card>
      </div>

      {/* Recommended Goals */}
      {recommendations.length > 0 && (
        <Card className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 border-blue-200 dark:border-blue-800">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-600" />
            Recommended Goals
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm"
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium">{rec.title}</h4>
                  <Badge variant="outline">{rec.priority}</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-3">{rec.description}</p>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">
                    Current: {rec.current_value.toFixed(1)}
                  </span>
                  <span className="font-medium text-primary">
                    Target: {rec.suggested_target}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Goals List */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">My Goals</h3>
        <div className="space-y-4">
          {goals.map((goal) => (
            <Card key={goal.goal_id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {getStatusIcon(goal.status)}
                  <div>
                    <h4 className="font-semibold">{goal.title}</h4>
                    <p className="text-sm text-muted-foreground">{goal.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusBadge(goal.status)}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteGoal(goal.goal_id)}
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Progress</span>
                  <span className="font-medium">
                    {goal.current_value.toFixed(1)} / {goal.target_value}
                  </span>
                </div>
                <Progress value={goal.progress_percentage} className="h-2" />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{Math.round(goal.progress_percentage)}% Complete</span>
                  <span>
                    Due: {new Date(goal.target_date).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </Card>
          ))}

          {goals.length === 0 && (
            <div className="text-center py-12">
              <Target className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">No goals yet</p>
              <Button onClick={() => setCreateDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Goal
              </Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
