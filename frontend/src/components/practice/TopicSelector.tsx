import { useState } from 'react';
import { Subject } from '@/types';
import { questionBankService } from '@/services/mockData';
import { cn } from '@/lib/utils';
import { ChevronDown } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface TopicSelectorProps {
  subject: Subject;
  selectedTopic: string | null;
  onTopicSelect: (topic: string) => void;
}

export function TopicSelector({
  subject,
  selectedTopic,
  onTopicSelect,
}: TopicSelectorProps) {
  const topics = questionBankService.getTopics(subject);
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <Button
        variant="outline"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full justify-between"
      >
        <span>{selectedTopic || 'Select a topic...'}</span>
        <ChevronDown className={cn('h-5 w-5 transition-transform', isOpen && 'rotate-180')} />
      </Button>

      {isOpen && (
        <Card className="absolute top-full left-0 right-0 mt-2 shadow-lg z-50 max-h-80 overflow-y-auto">
          <CardContent className="p-2">
            {topics.length === 0 ? (
              <div className="p-3 text-center text-muted-foreground text-sm">
                No topics available for {subject}
              </div>
            ) : (
              <div className="space-y-1">
                {topics.map(topic => (
                  <Button
                    key={topic}
                    variant={selectedTopic === topic ? "secondary" : "ghost"}
                    onClick={() => {
                      onTopicSelect(topic);
                      setIsOpen(false);
                    }}
                    className={cn(
                      'w-full justify-start',
                      selectedTopic === topic && 'bg-primary/20 text-primary font-medium'
                    )}
                  >
                    {topic}
                  </Button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface SubjectSelectorProps {
  selectedSubject: Subject | null;
  onSubjectSelect: (subject: Subject) => void;
}

export function SubjectSelector({
  selectedSubject,
  onSubjectSelect,
}: SubjectSelectorProps) {
  const subjects: Subject[] = ['physics', 'chemistry', 'mathematics'];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {subjects.map(subject => (
        <button
          key={subject}
          onClick={() => onSubjectSelect(subject)}
          className={cn(
            'p-3 sm:p-4 rounded-lg border-2 transition-all text-center',
            selectedSubject === subject
              ? 'border-primary bg-primary/10'
              : 'border-border hover:border-primary/50 hover:bg-secondary/30'
          )}
        >
          <div className="font-semibold text-foreground capitalize text-sm sm:text-base">{subject}</div>
          <div className="text-xs text-muted-foreground mt-1">
            {subject === 'physics' && '12 topics'}
            {subject === 'chemistry' && '10 topics'}
            {subject === 'mathematics' && '11 topics'}
          </div>
        </button>
      ))}
    </div>
  );
}
