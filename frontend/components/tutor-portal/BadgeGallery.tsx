'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { apiClient } from '@/lib/api';
import { Loader2, Award, TrendingUp, Flame, Star } from 'lucide-react';
import confetti from 'canvas-confetti';

interface BadgeData {
  badge_id: string;
  title: string;
  description: string;
  badge_type: string;
  icon: string;
  earned: boolean;
  earned_date: string | null;
  progress_current: number;
  progress_target: number;
  progress_percentage: number;
}

interface BadgeGalleryProps {
  tutorId: string;
}

export function BadgeGallery({ tutorId }: BadgeGalleryProps) {
  const [loading, setLoading] = useState(true);
  const [badges, setBadges] = useState<BadgeData[]>([]);
  const [totalEarned, setTotalEarned] = useState(0);
  const [recentAchievements, setRecentAchievements] = useState<BadgeData[]>([]);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    loadBadges();
  }, [tutorId]);

  const loadBadges = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getTutorBadges(tutorId);

      if (response.success) {
        setBadges(response.badges);
        setTotalEarned(response.total_earned);
        setRecentAchievements(response.recent_achievements);

        // Show confetti for recent achievements
        if (response.recent_achievements.length > 0) {
          triggerConfetti();
        }
      }
    } catch (error) {
      console.error('Failed to load badges:', error);
    } finally {
      setLoading(false);
    }
  };

  const triggerConfetti = () => {
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    });
  };

  const getBadgeIcon = (badgeType: string) => {
    switch (badgeType) {
      case 'milestone':
        return <Award className="w-6 h-6" />;
      case 'streak':
        return <Flame className="w-6 h-6" />;
      case 'excellence':
        return <Star className="w-6 h-6" />;
      case 'engagement':
        return <TrendingUp className="w-6 h-6" />;
      default:
        return <Award className="w-6 h-6" />;
    }
  };

  const filteredBadges = filter === 'all'
    ? badges
    : badges.filter(b => b.badge_type === filter);

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
          <div className="text-center">
            <div className="text-3xl font-bold text-primary">{totalEarned}</div>
            <div className="text-sm text-muted-foreground mt-1">Badges Earned</div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-primary">{badges.length - totalEarned}</div>
            <div className="text-sm text-muted-foreground mt-1">In Progress</div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-primary">
              {Math.round((totalEarned / badges.length) * 100)}%
            </div>
            <div className="text-sm text-muted-foreground mt-1">Completion</div>
          </div>
        </Card>
      </div>

      {/* Recent Achievements */}
      {recentAchievements.length > 0 && (
        <Card className="p-6 bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-950 dark:to-orange-950 border-yellow-200 dark:border-yellow-800">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-yellow-600" />
            Recent Achievements
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentAchievements.map((badge) => (
              <div
                key={badge.badge_id}
                className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <div className="text-3xl">{badge.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{badge.title}</div>
                    <div className="text-xs text-muted-foreground">
                      {badge.earned_date && new Date(badge.earned_date).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Badge Gallery */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Badge Gallery</h3>

        <Tabs value={filter} onValueChange={setFilter} className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="milestone">Milestones</TabsTrigger>
            <TabsTrigger value="streak">Streaks</TabsTrigger>
            <TabsTrigger value="excellence">Excellence</TabsTrigger>
            <TabsTrigger value="engagement">Engagement</TabsTrigger>
          </TabsList>

          <TabsContent value={filter} className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredBadges.map((badge) => (
                <Card
                  key={badge.badge_id}
                  className={`p-6 transition-all ${
                    badge.earned
                      ? 'bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 border-blue-200 dark:border-blue-800'
                      : 'opacity-60 hover:opacity-80'
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div className={`text-4xl ${!badge.earned && 'grayscale'}`}>
                      {badge.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold truncate">{badge.title}</h4>
                        {badge.earned && (
                          <Badge variant="default" className="text-xs">
                            Earned
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">
                        {badge.description}
                      </p>

                      {!badge.earned && (
                        <div className="space-y-2">
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Progress</span>
                            <span>{badge.progress_current} / {badge.progress_target}</span>
                          </div>
                          <Progress value={badge.progress_percentage} className="h-2" />
                          <div className="text-xs font-medium text-primary">
                            {Math.round(badge.progress_percentage)}% Complete
                          </div>
                        </div>
                      )}

                      {badge.earned && badge.earned_date && (
                        <div className="text-xs text-muted-foreground mt-2">
                          Earned {new Date(badge.earned_date).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {filteredBadges.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                No badges found in this category
              </div>
            )}
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}
