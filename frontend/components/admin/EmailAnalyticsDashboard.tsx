/**
 * Email Analytics Dashboard Component
 *
 * Displays comprehensive email campaign metrics including:
 * - Overall email performance metrics
 * - Campaign-specific analytics
 * - Email type breakdown
 * - Trends over time
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { Mail, MailOpen, MousePointerClick, AlertCircle, TrendingUp } from 'lucide-react';

interface EmailMetrics {
  total_sent: number;
  total_delivered: number;
  total_opened: number;
  total_clicked: number;
  total_bounced: number;
  delivery_rate: number;
  open_rate: number;
  click_rate: number;
  bounce_rate: number;
}

interface TemplateMetrics {
  template_type: string;
  total_sent: number;
  open_rate: number;
  click_rate: number;
}

interface EmailAnalyticsData {
  metrics: EmailMetrics;
  by_template_type: TemplateMetrics[];
  trends: {
    sent_by_day: number[];
    opened_by_day: number[];
    clicked_by_day: number[];
  };
}

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b'];

export default function EmailAnalyticsDashboard() {
  const [analyticsData, setAnalyticsData] = useState<EmailAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/email/campaigns/analytics/overview?days=${period}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch email analytics: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        setAnalyticsData(data);
      }
    } catch (error) {
      console.error('Error fetching email analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading email analytics...</div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">No email analytics data available</div>
      </div>
    );
  }

  const { metrics, by_template_type, trends } = analyticsData;

  // Prepare trend data for chart
  const trendData = trends.sent_by_day.map((sent, index) => ({
    day: `Day ${index + 1}`,
    sent,
    opened: trends.opened_by_day[index],
    clicked: trends.clicked_by_day[index]
  }));

  // Prepare template data for pie chart
  const templateData = by_template_type.map((template) => ({
    name: template.template_type.replace(/_/g, ' '),
    value: template.total_sent
  }));

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Email Analytics</h2>
        <select
          value={period}
          onChange={(e) => setPeriod(Number(e.target.value))}
          className="px-4 py-2 border rounded-md"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Sent</p>
                <p className="text-2xl font-bold">{metrics.total_sent.toLocaleString()}</p>
                <p className="text-xs text-green-600 mt-1">
                  {metrics.delivery_rate.toFixed(1)}% delivered
                </p>
              </div>
              <Mail className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Opened</p>
                <p className="text-2xl font-bold">{metrics.total_opened.toLocaleString()}</p>
                <p className="text-xs text-green-600 mt-1">
                  {metrics.open_rate.toFixed(1)}% open rate
                </p>
              </div>
              <MailOpen className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Clicked</p>
                <p className="text-2xl font-bold">{metrics.total_clicked.toLocaleString()}</p>
                <p className="text-xs text-green-600 mt-1">
                  {metrics.click_rate.toFixed(1)}% click rate
                </p>
              </div>
              <MousePointerClick className="h-8 w-8 text-indigo-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Bounced</p>
                <p className="text-2xl font-bold">{metrics.total_bounced.toLocaleString()}</p>
                <p className="text-xs text-red-600 mt-1">
                  {metrics.bounce_rate.toFixed(1)}% bounce rate
                </p>
              </div>
              <AlertCircle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <Tabs defaultValue="trends" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="templates">By Template</TabsTrigger>
          <TabsTrigger value="distribution">Distribution</TabsTrigger>
        </TabsList>

        <TabsContent value="trends">
          <Card>
            <CardHeader>
              <CardTitle>Email Trends (Last 7 Days)</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="sent" stroke="#667eea" strokeWidth={2} name="Sent" />
                  <Line type="monotone" dataKey="opened" stroke="#764ba2" strokeWidth={2} name="Opened" />
                  <Line type="monotone" dataKey="clicked" stroke="#4facfe" strokeWidth={2} name="Clicked" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="templates">
          <Card>
            <CardHeader>
              <CardTitle>Performance by Template Type</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={by_template_type}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="template_type" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="open_rate" fill="#667eea" name="Open Rate (%)" />
                  <Bar dataKey="click_rate" fill="#764ba2" name="Click Rate (%)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="distribution">
          <Card>
            <CardHeader>
              <CardTitle>Email Volume Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={templateData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name}: ${entry.value}`}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {templateData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Template Performance Table */}
      <Card>
        <CardHeader>
          <CardTitle>Template Performance Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4">Template Type</th>
                  <th className="text-right py-3 px-4">Total Sent</th>
                  <th className="text-right py-3 px-4">Open Rate</th>
                  <th className="text-right py-3 px-4">Click Rate</th>
                  <th className="text-right py-3 px-4">Performance</th>
                </tr>
              </thead>
              <tbody>
                {by_template_type.map((template, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">
                      {template.template_type.replace(/_/g, ' ').toUpperCase()}
                    </td>
                    <td className="text-right py-3 px-4">{template.total_sent.toLocaleString()}</td>
                    <td className="text-right py-3 px-4">{template.open_rate.toFixed(1)}%</td>
                    <td className="text-right py-3 px-4">{template.click_rate.toFixed(1)}%</td>
                    <td className="text-right py-3 px-4">
                      {template.open_rate > 70 && template.click_rate > 35 ? (
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                          Excellent
                        </span>
                      ) : template.open_rate > 50 && template.click_rate > 25 ? (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">
                          Good
                        </span>
                      ) : (
                        <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">
                          Needs Improvement
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
