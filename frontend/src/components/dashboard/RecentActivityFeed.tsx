import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, BookOpen, Eye } from 'lucide-react';
import { ActivityItem } from '@/types/dashboard';
import { formatDistanceToNow } from 'date-fns';

interface RecentActivityFeedProps {
  activities: ActivityItem[];
}

const getActivityIcon = (type: ActivityItem['type']) => {
  switch (type) {
    case 'test_completed':
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    case 'questions_solved':
      return <BookOpen className="h-4 w-4 text-blue-600" />;
    case 'topic_reviewed':
      return <Eye className="h-4 w-4 text-purple-600" />;
    default:
      return <CheckCircle className="h-4 w-4 text-gray-600" />;
  }
};

const getActivityLabel = (type: ActivityItem['type']) => {
  switch (type) {
    case 'test_completed':
      return 'Test Completed';
    case 'questions_solved':
      return 'Questions Solved';
    case 'topic_reviewed':
      return 'Topic Reviewed';
    default:
      return 'Activity';
  }
};

export const RecentActivityFeed: React.FC<RecentActivityFeedProps> = ({
  activities,
}) => {
  if (activities.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-gray-500">No recent activity</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {activities.map((activity) => (
            <div
              key={activity.id}
              className="flex items-start gap-3 border-b pb-3 last:border-b-0"
            >
              <div className="mt-1">{getActivityIcon(activity.type)}</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">
                  {activity.title}
                </p>
                <p className="text-xs text-gray-500">
                  {formatDistanceToNow(new Date(activity.timestamp), {
                    addSuffix: true,
                  })}
                </p>
              </div>
              {activity.score !== undefined && (
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">
                    {activity.score}%
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
