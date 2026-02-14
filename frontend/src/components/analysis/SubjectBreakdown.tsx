import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { SubjectBreakdown as SubjectBreakdownData, TopicData } from '@/types/analysis';
import { ChevronDown, ChevronUp, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface SubjectBreakdownProps {
  subjects: SubjectBreakdownData[];
  onTopicClick?: (subject: SubjectBreakdownData, topic: TopicData) => void;
  selectedSubjectId?: string | null;
}

const getTrendIcon = (trend: TopicData['trend']) => {
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

export const SubjectBreakdown: React.FC<SubjectBreakdownProps> = ({
  subjects,
  onTopicClick,
  selectedSubjectId,
}) => {
  const [expandedSubjects, setExpandedSubjects] = useState<Set<string>>(
    new Set(subjects.slice(0, 1).map((s) => s.subject_id))
  );

  // Auto-expand selected subject from URL parameter
  useEffect(() => {
    if (selectedSubjectId) {
      setExpandedSubjects(prev => {
        const newSet = new Set(prev);
        newSet.add(selectedSubjectId);
        return newSet;
      });
      
      // Scroll to the selected subject
      setTimeout(() => {
        const element = document.getElementById(`subject-${selectedSubjectId}`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    }
  }, [selectedSubjectId]);

  const toggleSubject = (subjectId: string) => {
    const newExpanded = new Set(expandedSubjects);
    if (newExpanded.has(subjectId)) {
      newExpanded.delete(subjectId);
    } else {
      newExpanded.add(subjectId);
    }
    setExpandedSubjects(newExpanded);
  };

  if (subjects.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Subject-wise Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-gray-500">No subject data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="flex flex-col h-[600px]">
      <CardHeader className="flex-shrink-0">
        <CardTitle>Subject-wise Breakdown</CardTitle>
        <p className="text-sm text-gray-600 mt-2">
          Click on a subject to expand and see topic-level details
        </p>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full px-6 pb-6">
          <div className="space-y-3">
            {subjects.map((subject) => (
              <div 
                key={subject.subject_id} 
                id={`subject-${subject.subject_id}`}
                className="border border-gray-200 rounded-lg"
              >
                {/* Subject Header */}
                <button
                  onClick={() => toggleSubject(subject.subject_id)}
                  className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                  aria-expanded={expandedSubjects.has(subject.subject_id)}
                  aria-label={`${subject.subject_name} - ${subject.accuracy_percentage}% accuracy`}
                >
                  <div className="flex-1 text-left">
                    <h3 className="font-semibold text-gray-900">
                      {subject.subject_name}
                    </h3>
                    <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
                      <span>{subject.accuracy_percentage}% accuracy</span>
                      <span>{subject.questions_solved} questions</span>
                      <div className="flex items-center gap-1">
                        {getTrendIcon(subject.trend)}
                        <span>
                          {subject.trend === 'up'
                            ? 'Improving'
                            : subject.trend === 'down'
                              ? 'Declining'
                              : 'Stable'}
                        </span>
                      </div>
                    </div>
                  </div>
                  {expandedSubjects.has(subject.subject_id) ? (
                    <ChevronUp className="h-5 w-5 text-gray-600" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-gray-600" />
                  )}
                </button>

                {/* Topics (Expandable) */}
                {expandedSubjects.has(subject.subject_id) && (
                  <div className="border-t border-gray-200 bg-gray-50 p-4 space-y-3">
                    {subject.topics.map((topic) => (
                      <div
                        key={topic.topic_id}
                        className="rounded-lg border border-gray-200 bg-white p-3 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1">
                            <h4 className="font-medium text-gray-900">
                              {topic.topic_name}
                            </h4>
                            <div className="mt-2 space-y-1 text-sm text-gray-600">
                              <div className="flex items-center justify-between">
                                <span>Accuracy: {topic.accuracy_percentage}%</span>
                                {getTrendIcon(topic.trend)}
                              </div>
                              <div>Questions: {topic.questions_solved}</div>
                              <Progress
                                value={topic.accuracy_percentage}
                                className="h-1.5 mt-2"
                              />
                            </div>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onTopicClick?.(subject, topic)}
                            aria-label={`View details for ${topic.topic_name}`}
                          >
                            Details
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};
