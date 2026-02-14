import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { WeakArea } from '@/types/analysis';
import { AlertTriangle } from 'lucide-react';

interface WeakAreasSectionProps {
  weakAreas: WeakArea[];
  onActionClick?: (area: WeakArea) => void;
}

export const WeakAreasSection: React.FC<WeakAreasSectionProps> = ({
  weakAreas,
  onActionClick,
}) => {
  if (weakAreas.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600" />
            Weak Areas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-gray-500">No weak areas identified</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="flex flex-col h-[600px]">
      <CardHeader className="flex-shrink-0">
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-yellow-600" />
          Weak Areas (Ranked by Impact)
        </CardTitle>
        <p className="text-sm text-gray-600 mt-2">
          Topics where you need improvement, ranked by their impact on your overall score
        </p>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full px-6 pb-6">
          <div className="space-y-4">
            {weakAreas.map((area, index) => (
              <div
                key={area.topic_id}
                className="rounded-lg border border-red-200 bg-red-50 p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-red-600 text-xs font-bold text-white">
                        {index + 1}
                      </span>
                      <h3 className="font-semibold text-gray-900">
                        {area.topic_name}
                      </h3>
                    </div>

                    <div className="mt-3 space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Accuracy</span>
                        <span className="font-semibold text-gray-900">
                          {area.accuracy_percentage}%
                        </span>
                      </div>
                      <Progress
                        value={area.accuracy_percentage}
                        className="h-2"
                      />
                    </div>

                    <p className="mt-3 text-sm text-gray-700">
                      {area.recommended_action}
                    </p>
                  </div>

                  <Button
                    size="sm"
                    onClick={() => onActionClick?.(area)}
                    aria-label={`Practice ${area.topic_name}`}
                  >
                    Practice
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};
