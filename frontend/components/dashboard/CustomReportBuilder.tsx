'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';

interface Metric {
  id: string;
  label: string;
  description: string;
}

const AVAILABLE_METRICS: Metric[] = [
  { id: 'avg_rating', label: 'Average Rating', description: 'Session rating average' },
  { id: 'sessions_completed', label: 'Sessions Completed', description: 'Total sessions' },
  { id: 'engagement_score', label: 'Engagement Score', description: 'Tutor engagement metric' },
  { id: 'reschedule_rate', label: 'Reschedule Rate', description: 'Percentage of rescheduled sessions' },
  { id: 'no_show_rate', label: 'No-Show Rate', description: 'Percentage of no-show sessions' },
  { id: 'first_session_success_rate', label: 'First Session Success', description: 'First session rating ≥4' },
  { id: 'learning_objectives_met_pct', label: 'Learning Objectives Met', description: 'Objectives achievement rate' },
  { id: 'performance_tier', label: 'Performance Tier', description: 'Tier classification' },
];

export function CustomReportBuilder() {
  const [open, setOpen] = useState(false);
  const [reportName, setReportName] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [format, setFormat] = useState<'csv' | 'pdf'>('csv');
  const [isGenerating, setIsGenerating] = useState(false);

  const toggleMetric = (metricId: string) => {
    setSelectedMetrics((prev) =>
      prev.includes(metricId)
        ? prev.filter((id) => id !== metricId)
        : [...prev, metricId]
    );
  };

  const handleGenerate = async () => {
    if (!reportName.trim()) {
      toast.error('Please enter a report name');
      return;
    }

    if (selectedMetrics.length === 0) {
      toast.error('Please select at least one metric');
      return;
    }

    if (!startDate || !endDate) {
      toast.error('Please select date range');
      return;
    }

    setIsGenerating(true);

    try {
      const response = await fetch('/api/v1/reports/custom-report', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          report_name: reportName,
          start_date: new Date(startDate).toISOString(),
          end_date: new Date(endDate).toISOString(),
          metrics: selectedMetrics,
          format: format,
          group_by_tier: false,
          include_summary: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate report: ${response.statusText}`);
      }

      // Download file
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${reportName.replace(/\s+/g, '_')}_${Date.now()}.${format}`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success('Report generated successfully');
      setOpen(false);

      // Reset form
      setReportName('');
      setStartDate('');
      setEndDate('');
      setSelectedMetrics([]);
    } catch (error) {
      console.error('Report generation error:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to generate report');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <svg
            className="mr-2 h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          Custom Report
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Build Custom Report</DialogTitle>
          <DialogDescription>
            Select metrics and date range to generate a custom performance report.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="report-name">Report Name *</Label>
            <Input
              id="report-name"
              placeholder="e.g., Monthly Performance Review"
              value={reportName}
              onChange={(e) => setReportName(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="start-date">Start Date *</Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="end-date">End Date *</Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Select Metrics *</Label>
            <div className="grid grid-cols-1 gap-2 border rounded-md p-3 max-h-[200px] overflow-y-auto">
              {AVAILABLE_METRICS.map((metric) => (
                <div key={metric.id} className="flex items-start space-x-2">
                  <Checkbox
                    id={metric.id}
                    checked={selectedMetrics.includes(metric.id)}
                    onCheckedChange={() => toggleMetric(metric.id)}
                  />
                  <div className="grid gap-1.5 leading-none">
                    <label
                      htmlFor={metric.id}
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                    >
                      {metric.label}
                    </label>
                    <p className="text-xs text-muted-foreground">{metric.description}</p>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              Selected: {selectedMetrics.length} of {AVAILABLE_METRICS.length}
            </p>
          </div>

          <div className="space-y-2">
            <Label>Export Format</Label>
            <div className="flex gap-4">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="format"
                  value="csv"
                  checked={format === 'csv'}
                  onChange={(e) => setFormat(e.target.value as 'csv' | 'pdf')}
                  className="h-4 w-4"
                />
                <span className="text-sm">CSV</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="format"
                  value="pdf"
                  checked={format === 'pdf'}
                  onChange={(e) => setFormat(e.target.value as 'csv' | 'pdf')}
                  className="h-4 w-4"
                />
                <span className="text-sm">PDF</span>
              </label>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
            disabled={isGenerating}
          >
            Cancel
          </Button>
          <Button onClick={handleGenerate} disabled={isGenerating}>
            {isGenerating ? 'Generating...' : 'Generate Report'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
