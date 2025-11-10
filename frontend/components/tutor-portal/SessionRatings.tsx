'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Rating, RatingButton } from '@/components/kibo-ui/rating';
import { StarIcon, Calendar, MessageSquare } from 'lucide-react';
import { useState, useEffect } from 'react';

export interface RatingData {
  session_id: string;
  student_id: string;
  session_date: string;
  rating: number;
  feedback_text?: string;
  subject: string;
}

export interface RatingDistribution {
  5: number;
  4: number;
  3: number;
  2: number;
  1: number;
}

interface SessionRatingsProps {
  ratings: RatingData[];
  loading?: boolean;
  startDate?: Date;
  endDate?: Date;
  onDateRangeChange?: (startDate: Date, endDate: Date) => void;
}

export function SessionRatings({ ratings, loading, startDate, endDate }: SessionRatingsProps) {
  const [distribution, setDistribution] = useState<RatingDistribution>({
    5: 0,
    4: 0,
    3: 0,
    2: 0,
    1: 0,
  });
  const [averageRating, setAverageRating] = useState<number>(0);

  useEffect(() => {
    if (!ratings || ratings.length === 0) {
      setDistribution({ 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 });
      setAverageRating(0);
      return;
    }

    // Calculate distribution
    const dist: RatingDistribution = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };
    let total = 0;

    ratings.forEach((r) => {
      const roundedRating = Math.round(r.rating) as 1 | 2 | 3 | 4 | 5;
      dist[roundedRating] = (dist[roundedRating] || 0) + 1;
      total += r.rating;
    });

    setDistribution(dist);
    setAverageRating(total / ratings.length);
  }, [ratings]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 4.5) return 'text-green-600';
    if (rating >= 4.0) return 'text-blue-600';
    if (rating >= 3.0) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getDistributionPercentage = (count: number) => {
    if (ratings.length === 0) return 0;
    return (count / ratings.length) * 100;
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Session Ratings</CardTitle>
          <CardDescription>Loading ratings data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!ratings || ratings.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Session Ratings</CardTitle>
          <CardDescription>No ratings available</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
            <StarIcon className="h-12 w-12 mb-4 opacity-50" />
            <p>Your session ratings will appear here.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Average Rating Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Session Ratings Overview</CardTitle>
          <CardDescription>
            {ratings.length} rating{ratings.length !== 1 ? 's' : ''} received
            {startDate && endDate && (
              <> from {formatDate(startDate.toISOString())} to {formatDate(endDate.toISOString())}</>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center mb-6">
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <span className={`text-5xl font-bold ${getRatingColor(averageRating)}`}>
                  {averageRating.toFixed(2)}
                </span>
                <span className="text-2xl text-muted-foreground">/5.0</span>
              </div>
              <div className="flex items-center justify-center gap-1">
                <Rating value={averageRating} readOnly className="text-yellow-500">
                  <RatingButton />
                  <RatingButton />
                  <RatingButton />
                  <RatingButton />
                  <RatingButton />
                </Rating>
              </div>
            </div>
          </div>

          {/* Rating Distribution */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium mb-3">Rating Distribution</h4>
            {[5, 4, 3, 2, 1].map((rating) => {
              const count = distribution[rating as keyof RatingDistribution];
              const percentage = getDistributionPercentage(count);

              return (
                <div key={rating} className="flex items-center gap-3">
                  <div className="flex items-center gap-1 min-w-[80px]">
                    <span className="text-sm font-medium">{rating}</span>
                    <StarIcon className="h-3 w-3 text-yellow-500 fill-current" />
                  </div>
                  <div className="flex-1 h-6 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-yellow-500 transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <span className="text-sm text-muted-foreground min-w-[60px] text-right">
                    {count} ({percentage.toFixed(0)}%)
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Recent Ratings List */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Ratings</CardTitle>
          <CardDescription>Latest feedback from students</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {ratings.slice(0, 10).map((ratingData) => (
              <div
                key={ratingData.session_id}
                className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className="text-xs">
                        {ratingData.subject}
                      </Badge>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatDate(ratingData.session_date)}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 ml-4">
                    <Rating value={ratingData.rating} readOnly className="text-yellow-500">
                      <RatingButton size={16} />
                      <RatingButton size={16} />
                      <RatingButton size={16} />
                      <RatingButton size={16} />
                      <RatingButton size={16} />
                    </Rating>
                    <span className={`font-bold ml-1 ${getRatingColor(ratingData.rating)}`}>
                      {ratingData.rating.toFixed(1)}
                    </span>
                  </div>
                </div>

                {ratingData.feedback_text && (
                  <div className="mt-2 p-3 bg-muted/50 rounded-md">
                    <div className="flex items-start gap-2">
                      <MessageSquare className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                      <p className="text-sm italic">&ldquo;{ratingData.feedback_text}&rdquo;</p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
