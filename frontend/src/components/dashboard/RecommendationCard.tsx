import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Lightbulb, Clock } from 'lucide-react';
import { Recommendation } from '@/types/dashboard';

interface RecommendationCardProps {
  recommendation: Recommendation;
  onAction?: () => void;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onAction,
}) => {
  return (
    <Card className="border-blue-200 bg-blue-50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-blue-600" />
          Next Steps
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h3 className="font-semibold text-gray-900">
            {recommendation.topic_name}
          </h3>
          <p className="mt-1 text-sm text-gray-700">
            {recommendation.reason}
          </p>
        </div>

        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span className="inline-block rounded-full bg-blue-100 px-3 py-1">
            {recommendation.difficulty}
          </span>
          <div className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            <span>{recommendation.estimated_time_minutes} mins</span>
          </div>
        </div>

        <Button
          onClick={onAction}
          className="w-full bg-blue-600 hover:bg-blue-700"
          aria-label={recommendation.action}
        >
          {recommendation.action}
        </Button>
      </CardContent>
    </Card>
  );
};
