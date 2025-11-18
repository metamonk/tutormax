'use client';

/**
 * Assign Intervention Dialog Component (Subtask 16.2)
 *
 * Provides one-click assignment functionality for interventions.
 * Allows quick assignment to managers or coaches.
 */

import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { User, UserCheck } from 'lucide-react';
import type { Intervention } from '@/types/intervention';
import { formatInterventionType } from '@/types/intervention';

interface AssignInterventionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  intervention: Intervention | null;
  onAssign: (interventionId: string, assignedTo: string) => Promise<void>;
}

// Mock list of available assignees
// In production, this would come from an API
const ASSIGNEES = [
  { id: 'manager_sarah', name: 'Sarah Johnson', role: 'Operations Manager' },
  { id: 'coach_mike', name: 'Mike Chen', role: 'Performance Coach' },
  { id: 'manager_alex', name: 'Alex Rivera', role: 'People Ops Manager' },
  { id: 'coach_emma', name: 'Emma Davis', role: 'Senior Coach' },
];

export function AssignInterventionDialog({
  open,
  onOpenChange,
  intervention,
  onAssign,
}: AssignInterventionDialogProps) {
  const [selectedAssignee, setSelectedAssignee] = React.useState<string>('');
  const [customAssignee, setCustomAssignee] = React.useState<string>('');
  const [loading, setLoading] = React.useState(false);

  // Reset state when dialog opens/closes
  React.useEffect(() => {
    if (!open) {
      setSelectedAssignee('');
      setCustomAssignee('');
      setLoading(false);
    }
  }, [open]);

  const handleAssign = async () => {
    if (!intervention) return;

    const assignee = selectedAssignee || customAssignee;
    if (!assignee) return;

    setLoading(true);
    try {
      await onAssign(intervention.intervention_id, assignee);
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to assign intervention:', error);
      // Error handling would be done in the parent component
    } finally {
      setLoading(false);
    }
  };

  const getInitials = (name: string) => {
    if (!name || typeof name !== 'string') return 'ST';
    return name
      .split(' ')
      .filter((n) => n.length > 0)
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'ST';
  };

  if (!intervention) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Assign Intervention</DialogTitle>
          <DialogDescription>
            Assign this intervention to a manager or coach for immediate action.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Intervention Details */}
          <div className="rounded-lg border p-4 bg-muted/50">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Tutor:</span>
                <span className="text-sm">{intervention.tutor_name || intervention.tutor_id}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Type:</span>
                <span className="text-sm">
                  {formatInterventionType(intervention.intervention_type)}
                </span>
              </div>
              {intervention.trigger_reason && (
                <div className="mt-2 pt-2 border-t">
                  <span className="text-xs font-medium text-muted-foreground">Reason:</span>
                  <p className="text-xs text-muted-foreground mt-1">
                    {intervention.trigger_reason}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Quick Assign Buttons */}
          <div>
            <Label className="text-sm font-medium mb-3 block">Quick Assign</Label>
            <div className="grid grid-cols-2 gap-2">
              {ASSIGNEES.map((assignee) => (
                <button
                  key={assignee.id}
                  onClick={() => {
                    setSelectedAssignee(assignee.id);
                    setCustomAssignee('');
                  }}
                  className={`flex items-center gap-3 p-3 rounded-lg border transition-all hover:bg-muted/50 ${
                    selectedAssignee === assignee.id
                      ? 'border-primary bg-primary/5 ring-1 ring-primary'
                      : 'border-border'
                  }`}
                >
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="text-xs">
                      {getInitials(assignee.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 text-left">
                    <div className="text-sm font-medium">{assignee.name}</div>
                    <div className="text-xs text-muted-foreground">{assignee.role}</div>
                  </div>
                  {selectedAssignee === assignee.id && (
                    <UserCheck className="h-4 w-4 text-primary" />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Custom Assignee Input */}
          <div className="space-y-2">
            <Label htmlFor="custom-assignee" className="text-sm font-medium">
              Or assign to someone else
            </Label>
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <Input
                id="custom-assignee"
                placeholder="Enter name or ID"
                value={customAssignee}
                onChange={(e) => {
                  setCustomAssignee(e.target.value);
                  setSelectedAssignee('');
                }}
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button
            onClick={handleAssign}
            disabled={!selectedAssignee && !customAssignee}
            loading={loading}
          >
            {loading ? 'Assigning...' : 'Assign Intervention'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
