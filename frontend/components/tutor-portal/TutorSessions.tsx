'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TutorSessionsResponse } from '@/lib/types';
import { Calendar, Star, ThumbsUp, ThumbsDown, MessageSquare, ChevronLeft, ChevronRight } from 'lucide-react';

interface TutorSessionsProps {
  data: TutorSessionsResponse | null;
  loading?: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
}

export function TutorSessions({ data, loading, onLoadMore, hasMore }: TutorSessionsProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Sessions</CardTitle>
          <CardDescription>Loading session history...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.sessions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Sessions</CardTitle>
          <CardDescription>No sessions found</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
            <Calendar className="h-12 w-12 mb-4 opacity-50" />
            <p>Your session history will appear here.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getRatingColor = (rating: number | null) => {
    if (!rating) return 'text-gray-400';
    if (rating >= 4.5) return 'text-green-600';
    if (rating >= 4.0) return 'text-blue-600';
    if (rating >= 3.0) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Recent Sessions</CardTitle>
            <CardDescription>
              {data.pagination.total} session{data.pagination.total !== 1 ? 's' : ''} total
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {data.sessions.map((session) => (
            <div
              key={session.session_id}
              className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium">{session.subject}</h4>
                    <Badge variant="outline" className="text-xs">
                      Session #{session.session_number}
                    </Badge>
                    {session.session_type === 'group' && (
                      <Badge variant="secondary" className="text-xs">
                        Group
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatDate(session.scheduled_start)}
                    {session.duration_minutes && ` • ${session.duration_minutes} min`}
                  </p>
                </div>
                {session.rating !== null && (
                  <div className="flex items-center gap-1 ml-4">
                    <Star className={`h-5 w-5 ${getRatingColor(session.rating)} fill-current`} />
                    <span className={`font-bold ${getRatingColor(session.rating)}`}>
                      {session.rating.toFixed(1)}
                    </span>
                  </div>
                )}
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                {session.engagement_score !== null && (
                  <div className="text-sm">
                    <span className="text-muted-foreground">Engagement:</span>{' '}
                    <span className="font-medium">{session.engagement_score.toFixed(1)}/5.0</span>
                  </div>
                )}
                {session.learning_objectives_met !== null && (
                  <div className="text-sm flex items-center gap-1">
                    <span className="text-muted-foreground">Goals:</span>
                    {session.learning_objectives_met ? (
                      <span className="text-green-600 font-medium flex items-center">
                        <ThumbsUp className="h-3 w-3 mr-1" /> Met
                      </span>
                    ) : (
                      <span className="text-orange-600 font-medium flex items-center">
                        <ThumbsDown className="h-3 w-3 mr-1" /> Not Met
                      </span>
                    )}
                  </div>
                )}
                {session.no_show && (
                  <div className="text-sm">
                    <Badge variant="destructive" className="text-xs">
                      No Show
                    </Badge>
                  </div>
                )}
                {session.would_recommend !== null && (
                  <div className="text-sm flex items-center gap-1">
                    <span className="text-muted-foreground">Would Recommend:</span>
                    {session.would_recommend ? (
                      <span className="text-green-600 font-medium">Yes</span>
                    ) : (
                      <span className="text-red-600 font-medium">No</span>
                    )}
                  </div>
                )}
              </div>

              {/* Feedback */}
              {session.feedback_text && (
                <div className="mt-3 p-3 bg-muted/50 rounded-md">
                  <div className="flex items-start gap-2">
                    <MessageSquare className="h-4 w-4 text-muted-foreground mt-0.5" />
                    <p className="text-sm italic">&ldquo;{session.feedback_text}&rdquo;</p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Pagination */}
        {data.pagination.total > data.pagination.limit && (
          <div className="flex items-center justify-between mt-6 pt-4 border-t">
            <p className="text-sm text-muted-foreground">
              Showing {data.pagination.offset + 1}-{Math.min(data.pagination.offset + data.pagination.limit, data.pagination.total)} of {data.pagination.total}
            </p>
            {hasMore && onLoadMore && (
              <Button onClick={onLoadMore} variant="outline" size="sm">
                Load More
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
