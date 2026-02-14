import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar, Clock } from 'lucide-react';
import { UpcomingTest } from '@/types/dashboard';
import { formatDistanceToNow } from 'date-fns';

interface UpcomingTestsSectionProps {
  tests: UpcomingTest[];
  onTestClick?: (test: UpcomingTest) => void;
}

const getDifficultyColor = (difficulty: UpcomingTest['difficulty']) => {
  switch (difficulty) {
    case 'easy':
      return 'bg-green-100 text-green-800';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800';
    case 'hard':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const getTestTypeLabel = (type: UpcomingTest['test_type']) => {
  switch (type) {
    case 'mock':
      return 'Mock Test';
    case 'pyq':
      return 'Previous Year';
    case 'topic':
      return 'Topic Test';
    default:
      return 'Test';
  }
};

export const UpcomingTestsSection: React.FC<UpcomingTestsSectionProps> = ({
  tests,
  onTestClick,
}) => {
  if (tests.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Upcoming Tests</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-gray-500">No upcoming tests</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upcoming Tests</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {tests.map((test) => (
            <div
              key={test.test_id}
              className="flex items-center justify-between rounded-lg border border-gray-200 p-4 hover:bg-gray-50"
            >
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">{test.test_name}</h3>
                <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    <span>
                      {formatDistanceToNow(new Date(test.date), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                  <span className={`rounded-full px-2 py-1 text-xs font-medium ${getDifficultyColor(test.difficulty)}`}>
                    {test.difficulty}
                  </span>
                  <span className="text-xs text-gray-500">
                    {getTestTypeLabel(test.test_type)}
                  </span>
                </div>
              </div>
              <Button
                onClick={() => onTestClick?.(test)}
                aria-label={`Start ${test.test_name}`}
              >
                Start
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
