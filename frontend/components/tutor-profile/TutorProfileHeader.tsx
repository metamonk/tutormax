'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TutorBasicInfo, ChurnPredictionWindow } from '@/lib/types';
import { User, Mail, Calendar, MapPin, BookOpen, AlertTriangle, TrendingUp } from 'lucide-react';

interface TutorProfileHeaderProps {
  tutorInfo: TutorBasicInfo;
  churnPredictions: ChurnPredictionWindow[];
}

export function TutorProfileHeader({ tutorInfo, churnPredictions }: TutorProfileHeaderProps) {
  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toUpperCase()) {
      case 'CRITICAL':
        return 'destructive';
      case 'HIGH':
        return 'destructive';
      case 'MEDIUM':
        return 'default';
      case 'LOW':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel.toUpperCase()) {
      case 'CRITICAL':
      case 'HIGH':
        return <AlertTriangle className="h-4 w-4" />;
      case 'MEDIUM':
        return <TrendingUp className="h-4 w-4" />;
      default:
        return <TrendingUp className="h-4 w-4" />;
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Basic Info */}
      <Card className="lg:col-span-2">
        <CardContent className="pt-6">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-start gap-4">
              <div className="h-16 w-16 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-2xl font-bold">
                {tutorInfo.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <h2 className="text-2xl font-bold">{tutorInfo.name}</h2>
                <p className="text-muted-foreground flex items-center gap-1 mt-1">
                  <User className="h-4 w-4" />
                  {tutorInfo.tutor_id}
                </p>
              </div>
            </div>
            <Badge variant={tutorInfo.status === 'active' ? 'default' : 'secondary'} className="capitalize">
              {tutorInfo.status}
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-2 text-sm">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <span>{tutorInfo.email}</span>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span>Onboarded: {formatDate(tutorInfo.onboarding_date)}</span>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
              <span>Tenure: {tutorInfo.tenure_days} days</span>
            </div>

            {tutorInfo.location && (
              <div className="flex items-center gap-2 text-sm">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <span>{tutorInfo.location}</span>
              </div>
            )}

            {tutorInfo.education_level && (
              <div className="flex items-center gap-2 text-sm">
                <BookOpen className="h-4 w-4 text-muted-foreground" />
                <span>{tutorInfo.education_level}</span>
              </div>
            )}
          </div>

          {tutorInfo.subjects.length > 0 && (
            <div className="mt-4 pt-4 border-t">
              <p className="text-sm font-medium mb-2">Subjects:</p>
              <div className="flex flex-wrap gap-2">
                {tutorInfo.subjects.map((subject, idx) => (
                  <Badge key={idx} variant="outline">
                    {subject}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Churn Predictions */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-600" />
            Churn Risk
          </h3>
          <div className="space-y-3">
            {churnPredictions.map((pred) => (
              <div key={pred.window} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <div>
                  <p className="text-sm font-medium">{pred.window.toUpperCase()}</p>
                  <p className="text-xs text-muted-foreground">
                    {pred.churn_score.toFixed(0)}% risk
                  </p>
                </div>
                <Badge variant={getRiskColor(pred.risk_level)} className="flex items-center gap-1">
                  {getRiskIcon(pred.risk_level)}
                  {pred.risk_level}
                </Badge>
              </div>
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-4 text-center">
            Last updated: {formatDate(churnPredictions[0]?.prediction_date || new Date().toISOString())}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
