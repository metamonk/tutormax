'use client';

/**
 * Outcome Recording Dialog Component (Subtask 16.5)
 *
 * Allows managers to log the results of completed interventions
 * with outcome selection and detailed notes.
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
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup } from '@/components/ui/radio-group';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, Minus, TrendingDown, XCircle, CheckCircle2 } from 'lucide-react';
import type { Intervention, InterventionOutcome } from '@/types/intervention';
import { formatInterventionType } from '@/types/intervention';

interface OutcomeRecordingDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  intervention: Intervention | null;
  onRecordOutcome: (interventionId: string, outcome: InterventionOutcome, notes?: string) => Promise<void>;
}

interface OutcomeOption {
  value: InterventionOutcome;
  label: string;
  description: string;
  icon: typeof TrendingUp;
  color: string;
  bgColor: string;
}

const OUTCOME_OPTIONS: OutcomeOption[] = [
  {
    value: 'improved',
    label: 'Improved',
    description: 'Tutor showed measurable improvement after intervention',
    icon: TrendingUp,
    color: 'text-green-700',
    bgColor: 'bg-green-50 border-green-200 hover:bg-green-100',
  },
  {
    value: 'no_change',
    label: 'No Change',
    description: 'No significant change in performance observed',
    icon: Minus,
    color: 'text-gray-700',
    bgColor: 'bg-gray-50 border-gray-200 hover:bg-gray-100',
  },
  {
    value: 'declined',
    label: 'Declined',
    description: 'Performance continued to decline despite intervention',
    icon: TrendingDown,
    color: 'text-orange-700',
    bgColor: 'bg-orange-50 border-orange-200 hover:bg-orange-100',
  },
  {
    value: 'churned',
    label: 'Churned',
    description: 'Tutor left the platform after intervention',
    icon: XCircle,
    color: 'text-red-700',
    bgColor: 'bg-red-50 border-red-200 hover:bg-red-100',
  },
];

export function OutcomeRecordingDialog({
  open,
  onOpenChange,
  intervention,
  onRecordOutcome,
}: OutcomeRecordingDialogProps) {
  const [selectedOutcome, setSelectedOutcome] = React.useState<InterventionOutcome | null>(null);
  const [notes, setNotes] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  // Reset state when dialog opens/closes
  React.useEffect(() => {
    if (open && intervention) {
      // Pre-fill with existing outcome if available
      if (intervention.outcome) {
        setSelectedOutcome(intervention.outcome);
      }
      if (intervention.notes) {
        setNotes(intervention.notes);
      }
    } else {
      setSelectedOutcome(null);
      setNotes('');
      setLoading(false);
    }
  }, [open, intervention]);

  const handleSubmit = async () => {
    if (!intervention || !selectedOutcome) return;

    setLoading(true);
    try {
      await onRecordOutcome(intervention.intervention_id, selectedOutcome, notes);
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to record outcome:', error);
      // Error handling would be done in the parent component
    } finally {
      setLoading(false);
    }
  };

  if (!intervention) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Record Intervention Outcome</DialogTitle>
          <DialogDescription>
            Document the results of this intervention to help track effectiveness and inform future
            actions.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Intervention Summary */}
          <div className="rounded-lg border p-4 bg-muted/50">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Tutor:</span>
                <span className="text-sm">{intervention.tutor_name || intervention.tutor_id}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Intervention Type:</span>
                <span className="text-sm">
                  {formatInterventionType(intervention.intervention_type)}
                </span>
              </div>
              {intervention.completed_date && (
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Completed:</span>
                  <span className="text-sm">
                    {new Date(intervention.completed_date).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Outcome Selection */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Outcome *</Label>
            <RadioGroup
              value={selectedOutcome || ''}
              onValueChange={(value) => setSelectedOutcome(value as InterventionOutcome)}
            >
              <div className="grid gap-3">
                {OUTCOME_OPTIONS.map((option) => {
                  const OptionIcon = option.icon;
                  const isSelected = selectedOutcome === option.value;

                  return (
                    <label
                      key={option.value}
                      className={`flex items-start gap-4 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        isSelected
                          ? 'border-primary shadow-sm'
                          : option.bgColor
                      }`}
                    >
                      <input
                        type="radio"
                        value={option.value}
                        checked={isSelected}
                        onChange={(e) => setSelectedOutcome(e.target.value as InterventionOutcome)}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <OptionIcon className={`h-5 w-5 ${option.color}`} />
                          <span className={`font-medium ${option.color}`}>{option.label}</span>
                        </div>
                        <p className="text-sm text-muted-foreground">{option.description}</p>
                      </div>
                      {isSelected && (
                        <CheckCircle2 className="h-5 w-5 text-primary mt-1" />
                      )}
                    </label>
                  );
                })}
              </div>
            </RadioGroup>
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="outcome-notes" className="text-sm font-medium">
              Additional Notes
            </Label>
            <Textarea
              id="outcome-notes"
              placeholder="Provide details about what was done, how the tutor responded, and any follow-up recommendations..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={6}
              className="resize-none"
            />
            <p className="text-xs text-muted-foreground">
              Include specific observations, metrics, or qualitative feedback that supports the
              selected outcome.
            </p>
          </div>

          {/* Recommendations based on outcome */}
          {selectedOutcome && (
            <div className="rounded-lg border p-4 bg-blue-50 border-blue-200">
              <div className="flex items-start gap-2">
                <div className="mt-0.5">
                  <div className="h-2 w-2 rounded-full bg-blue-600" />
                </div>
                <div className="text-sm">
                  <div className="font-medium text-blue-900 mb-1">Recommendation</div>
                  <div className="text-blue-700">
                    {selectedOutcome === 'improved' &&
                      'Continue monitoring performance. Consider recognition or reduced check-in frequency.'}
                    {selectedOutcome === 'no_change' &&
                      'Consider escalating intervention type or scheduling a follow-up review in 2 weeks.'}
                    {selectedOutcome === 'declined' &&
                      'Immediate escalation recommended. Consider performance improvement plan or retention interview.'}
                    {selectedOutcome === 'churned' &&
                      'Document learnings for future retention strategies. Update tutor status in the system.'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!selectedOutcome} loading={loading}>
            {loading ? 'Recording...' : 'Record Outcome'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
