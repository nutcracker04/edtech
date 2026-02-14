import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PerformanceOverview as PerformanceOverviewData } from '@/types/analysis';
import { Target, BookOpen, Award, Clock } from 'lucide-react';

interface PerformanceOverviewProps {
  data: PerformanceOverviewData;
  timePeriod: '7d' | '30d' | '90d' | 'all';
  onTimePeriodChange: (period: '7d' | '30d' | '90d' | 'all') => void;
}

export const PerformanceOverview: React.FC<PerformanceOverviewProps> = ({
  data,
  timePeriod,
  onTimePeriodChange,
}) => {
  const periods: Array<'7d' | '30d' | '90d' | 'all'> = ['7d', '30d', '90d', 'all'];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Performance Overview</CardTitle>
          <div className="flex gap-2">
            {periods.map((period) => (
              <Button
                key={period}
                size="sm"
                variant={timePeriod === period ? 'default' : 'outline'}
                onClick={() => onTimePeriodChange(period)}
                aria-label={`View ${period} period`}
              >
                {period === '7d' ? '7d' : period === '30d' ? '30d' : period === '90d' ? '90d' : 'All'}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Accuracy */}
          <div className="rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-2">
              <Target className="h-5 w-5 text-blue-600" />
              <p className="text-sm text-gray-600">Accuracy</p>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {data.accuracy_percentage}%
            </p>
          </div>

          {/* Questions Solved */}
          <div className="rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-green-600" />
              <p className="text-sm text-gray-600">Questions Solved</p>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {data.questions_solved}
            </p>
          </div>

          {/* Study Hours */}
          <div className="rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-2">
              <Award className="h-5 w-5 text-purple-600" />
              <p className="text-sm text-gray-600">Study Hours</p>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {data.study_hours}h
            </p>
          </div>

          {/* Avg Time per Question */}
          <div className="rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-orange-600" />
              <p className="text-sm text-gray-600">Avg Time/Q</p>
            </div>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {data.avg_time_per_question}s
            </p>
          </div>
        </div>

        {/* Percentile Rank (if available) */}
        {data.percentile_rank !== undefined && (
          <div className="mt-4 rounded-lg bg-blue-50 p-4">
            <p className="text-sm text-gray-600">
              You're in the top {100 - data.percentile_rank}% of your class
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
