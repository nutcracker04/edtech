import { Zap, BookOpen, Layers } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';

export type PracticeMode = 'adaptive' | 'topic-focus' | 'subject-focus';

interface Mode {
  value: PracticeMode;
  label: string;
  icon: React.ReactNode;
  description: string;
  details: string[];
}

const modes: Mode[] = [
  {
    value: 'adaptive',
    label: 'Adaptive Mode',
    icon: <Zap className="h-5 w-5" />,
    description: 'Questions tailored to your strengths and weaknesses',
    details: [
      'Focus on weak areas',
      'Difficulty adjusts to your performance',
      'Optimized learning path',
    ],
  },
  {
    value: 'topic-focus',
    label: 'Topic Focus',
    icon: <BookOpen className="h-5 w-5" />,
    description: 'Master a specific topic in depth',
    details: [
      'Choose any JEE topic',
      'Focused learning',
      'Build expertise',
    ],
  },
  {
    value: 'subject-focus',
    label: 'Subject Focus',
    icon: <Layers className="h-5 w-5" />,
    description: 'Practice all topics within a subject',
    details: [
      'Full subject coverage',
      'Balanced difficulty',
      'Comprehensive preparation',
    ],
  },
];

interface PracticeModeSelectorProps {
  selectedMode: PracticeMode | null;
  onModeSelect: (mode: PracticeMode) => void;
}

export function PracticeModeSelector({
  selectedMode,
  onModeSelect,
}: PracticeModeSelectorProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4">
        {modes.map(mode => (
          <Card
            key={mode.value}
            onClick={() => onModeSelect(mode.value)}
            className={cn(
              'cursor-pointer transition-all h-full flex flex-col',
              selectedMode === mode.value
                ? 'border-primary bg-primary/10 shadow-lg shadow-primary/20'
                : 'hover:border-primary/50 hover:bg-secondary/30'
            )}
          >
            <CardContent className="p-4 sm:p-6 flex flex-col h-full">
            <div className="flex items-start gap-2 sm:gap-3 mb-3 sm:mb-4">
              <div className={cn(
                'p-2 sm:p-3 rounded-lg shrink-0',
                selectedMode === mode.value ? 'bg-primary/20 text-primary' : 'bg-secondary text-foreground'
              )}>
                {mode.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-foreground text-base sm:text-lg">{mode.label}</div>
                <div className="text-xs text-muted-foreground mt-1">{mode.description}</div>
              </div>
            </div>
            <div className="space-y-2 flex-1">
              {mode.details.map((detail, i) => (
                <div key={i} className="text-xs sm:text-sm text-muted-foreground flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground shrink-0 mt-1" />
                  <span>{detail}</span>
                </div>
              ))}
            </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
