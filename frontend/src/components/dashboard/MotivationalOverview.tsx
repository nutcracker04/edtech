import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Flame, Target, BookOpen, Award } from 'lucide-react';
import { DashboardMetrics, StreakData } from '@/types/dashboard';

interface MotivationalOverviewProps {
  metrics: DashboardMetrics;
  streak: StreakData;
  onStartPractice?: () => void;
  onReviewWeakAreas?: () => void;
  onTakeMockTest?: () => void;
}

export const MotivationalOverview: React.FC<MotivationalOverviewProps> = ({
  metrics,
  streak,
  onStartPractice,
  onReviewWeakAreas,
  onTakeMockTest,
}) => {
  const isMilestone = streak.streak_milestone_reached;
  const milestoneValue = streak.milestone_value;

  return (
    <div className="space-y-6">
      {/* Streak Card */}
      <Card className={isMilestone ? 'border-yellow-400 bg-yellow-50' : ''}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-orange-500" />
            Current Streak
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-4xl font-bold text-orange-600">
                {streak.current_streak}
              </p>
              <p className="text-sm text-gray-600">consecutive days</p>
            </div>
            {isMilestone && (
              <div className="text-right">
                <p className="text-lg font-semibold text-yellow-600">
                  🎉 Milestone!
                </p>
                <p className="text-sm text-yellow-600">{milestoneValue} days</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Accuracy */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Target className="h-4 w-4 text-blue-500" />
              Accuracy
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-blue-600">
              {metrics.accuracy_percentage}%
            </p>
          </CardContent>
        </Card>

        {/* Questions Solved */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <BookOpen className="h-4 w-4 text-green-500" />
              Questions Solved
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-green-600">
              {metrics.questions_solved}
            </p>
          </CardContent>
        </Card>

        {/* Study Hours */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Award className="h-4 w-4 text-purple-500" />
              Study Hours
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-purple-600">
              {metrics.study_hours}h
            </p>
          </CardContent>
        </Card>

        {/* Tests Completed */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Target className="h-4 w-4 text-red-500" />
              Tests Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-red-600">
              {metrics.tests_completed}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Action Buttons */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Button
          size="lg"
          className="bg-blue-600 hover:bg-blue-700"
          aria-label="Start Practice"
          onClick={onStartPractice}
        >
          Start Practice
        </Button>
        <Button
          size="lg"
          variant="outline"
          aria-label="Review Weak Areas"
          onClick={onReviewWeakAreas}
        >
          Review Weak Areas
        </Button>
        <Button
          size="lg"
          variant="outline"
          aria-label="Take Mock Test"
          onClick={onTakeMockTest}
        >
          Take Mock Test
        </Button>
      </div>
    </div>
  );
};
