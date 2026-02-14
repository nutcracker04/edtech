import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { SubjectPerformance } from '@/types/dashboard';
import { getPerformanceColor } from '@/lib/colorScheme';
import { generatePerformanceAriaLabel, getFocusVisibleStyle } from '@/lib/accessibility';

interface SubjectPerformanceCardsProps {
  subjects: SubjectPerformance[];
  onSubjectClick?: (subject: SubjectPerformance) => void;
}

const getTrendIcon = (trend: SubjectPerformance['trend']) => {
  switch (trend) {
    case 'up':
      return <TrendingUp className="h-4 w-4 text-green-600" />;
    case 'down':
      return <TrendingDown className="h-4 w-4 text-red-600" />;
    case 'flat':
      return <Minus className="h-4 w-4 text-gray-600" />;
    default:
      return null;
  }
};

export const SubjectPerformanceCards: React.FC<SubjectPerformanceCardsProps> = ({
  subjects,
  onSubjectClick,
}) => {
  if (subjects.length === 0) {
    return (
      <div className="text-center text-gray-500">
        <p>No subject data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Subject Performance</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {subjects.map((subject) => (
          <Card
            key={subject.subject_id}
            className={`cursor-pointer transition-shadow hover:shadow-lg ${getFocusVisibleStyle()}`}
            onClick={() => onSubjectClick?.(subject)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                onSubjectClick?.(subject);
              }
            }}
            aria-label={generatePerformanceAriaLabel(
              subject.subject_name,
              subject.accuracy_percentage,
              subject.questions_solved
            )}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">
                  {subject.subject_name}
                </CardTitle>
                {getTrendIcon(subject.trend)}
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* Performance Ring */}
              <div className="flex items-center justify-center">
                <div className="relative h-24 w-24">
                  <svg className="h-full w-full" viewBox="0 0 100 100">
                    {/* Background circle */}
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="#e5e7eb"
                      strokeWidth="8"
                    />
                    {/* Progress circle */}
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke={getPerformanceColor(subject.accuracy_percentage)}
                      strokeWidth="8"
                      strokeDasharray={`${(subject.accuracy_percentage / 100) * 283} 283`}
                      strokeLinecap="round"
                      style={{ transition: 'stroke-dasharray 0.3s ease' }}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-lg font-bold text-gray-900">
                      {subject.accuracy_percentage}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Questions Solved */}
              <div className="text-center">
                <p className="text-sm text-gray-600">
                  {subject.questions_solved} questions solved
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};
