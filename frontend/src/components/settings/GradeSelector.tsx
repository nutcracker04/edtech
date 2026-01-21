import { Grade, TargetExam } from '@/types';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface GradeSelectorProps {
  selectedGrade: Grade | null;
  onGradeSelect: (grade: Grade) => void;
}

export function GradeSelector({ selectedGrade, onGradeSelect }: GradeSelectorProps) {
  const grades: { value: Grade; label: string; description: string }[] = [
    {
      value: '9',
      label: 'Class 9',
      description: 'Foundation basics',
    },
    {
      value: '10',
      label: 'Class 10',
      description: 'Build strong fundamentals',
    },
    {
      value: '11',
      label: 'Class 11',
      description: 'Main JEE preparation',
    },
    {
      value: '12',
      label: 'Class 12',
      description: 'Final year preparation',
    },
  ];

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        {grades.map(grade => (
          <button
            key={grade.value}
            onClick={() => onGradeSelect(grade.value)}
            className={cn(
              'p-4 rounded-lg border-2 transition-all text-left',
              selectedGrade === grade.value
                ? 'border-primary bg-primary/10'
                : 'border-border hover:border-primary/50 hover:bg-secondary/30'
            )}
          >
            <div className="font-medium text-foreground">{grade.label}</div>
            <div className="text-xs text-muted-foreground mt-1">{grade.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

interface TargetExamSelectorProps {
  selectedExam: TargetExam | null;
  onExamSelect: (exam: TargetExam) => void;
}

export function TargetExamSelector({ selectedExam, onExamSelect }: TargetExamSelectorProps) {
  const exams: { value: TargetExam; label: string; description: string }[] = [
    {
      value: 'jee-main',
      label: 'JEE Main',
      description: 'National Level Exam',
    },
    {
      value: 'jee-advanced',
      label: 'JEE Advanced',
      description: 'Premium IIT Entrance',
    },
    {
      value: 'both',
      label: 'Both Main & Advanced',
      description: 'Complete preparation',
    },
  ];

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 gap-3">
        {exams.map(exam => (
          <button
            key={exam.value}
            onClick={() => onExamSelect(exam.value)}
            className={cn(
              'p-4 rounded-lg border-2 transition-all text-left',
              selectedExam === exam.value
                ? 'border-primary bg-primary/10'
                : 'border-border hover:border-primary/50 hover:bg-secondary/30'
            )}
          >
            <div className="font-medium text-foreground">{exam.label}</div>
            <div className="text-xs text-muted-foreground mt-1">{exam.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
