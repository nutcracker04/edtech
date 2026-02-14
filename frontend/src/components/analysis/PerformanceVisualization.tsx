import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SubjectBreakdown } from '@/types/analysis';
import { getPerformanceColor, getPerformanceLabel } from '@/lib/colorScheme';
import { generatePerformanceAriaLabel, generateTrendAriaLabel } from '@/lib/accessibility';

interface PerformanceVisualizationProps {
  subjects: SubjectBreakdown[];
}

export const PerformanceVisualization: React.FC<PerformanceVisualizationProps> = ({
  subjects,
}) => {
  if (subjects.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-gray-500">No subject data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Performance Rings - All Subjects</CardTitle>
        <p className="text-sm text-gray-600 mt-2">
          Circular indicators showing your performance across all subjects
        </p>
      </CardHeader>
      <CardContent>
        <div className={`grid gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-${Math.min(subjects.length, 4)}`}>
          {subjects.map((subject) => {
            const color = getPerformanceColor(subject.accuracy_percentage);
            const label = getPerformanceLabel(subject.accuracy_percentage);
            const circumference = 2 * Math.PI * 45;
            const strokeDashoffset = circumference - (subject.accuracy_percentage / 100) * circumference;

            return (
              <div
                key={subject.subject_id}
                className="flex flex-col items-center group relative"
                role="img"
                aria-label={generatePerformanceAriaLabel(
                  subject.subject_name,
                  subject.accuracy_percentage,
                  subject.questions_solved
                )}
              >
                {/* Progress Ring */}
                <div className="relative h-32 w-32">
                  <svg className="h-full w-full" viewBox="0 0 100 100">
                    {/* Background circle */}
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="#e5e7eb"
                      strokeWidth="6"
                    />
                    {/* Progress circle */}
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke={color}
                      strokeWidth="6"
                      strokeDasharray={circumference}
                      strokeDashoffset={strokeDashoffset}
                      strokeLinecap="round"
                      style={{
                        transition: 'stroke-dashoffset 0.3s ease',
                        transform: 'rotate(-90deg)',
                        transformOrigin: '50% 50%',
                      }}
                    />
                  </svg>
                  {/* Center text */}
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-bold text-gray-900">
                      {subject.accuracy_percentage}%
                    </span>
                    <span className="text-xs text-gray-600">{label}</span>
                  </div>
                </div>

                {/* Subject info */}
                <div className="mt-4 text-center">
                  <h3 className="font-semibold text-gray-900">
                    {subject.subject_name}
                  </h3>
                  <p className="text-xs text-gray-600 mt-1">
                    {subject.questions_solved} questions
                  </p>
                  <div className="mt-2 flex items-center justify-center gap-1">
                    {subject.trend === 'up' && (
                      <span className="text-green-600 text-sm" aria-label={generateTrendAriaLabel('up')}>
                        ↑ Improving
                      </span>
                    )}
                    {subject.trend === 'down' && (
                      <span className="text-red-600 text-sm" aria-label={generateTrendAriaLabel('down')}>
                        ↓ Declining
                      </span>
                    )}
                    {subject.trend === 'flat' && (
                      <span className="text-gray-600 text-sm" aria-label={generateTrendAriaLabel('flat')}>
                        → Stable
                      </span>
                    )}
                  </div>
                </div>

                {/* Tooltip on hover */}
                <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 hidden group-hover:block bg-gray-900 text-white text-xs rounded px-3 py-2 whitespace-nowrap z-10 pointer-events-none">
                  {subject.subject_name}: {subject.accuracy_percentage}% accuracy, {subject.questions_solved} questions
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="mt-8 flex flex-wrap justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-green-500"></div>
            <span>Strong (80%+)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-yellow-500"></div>
            <span>Average (60-79%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-red-500"></div>
            <span>Weak (&lt;60%)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
