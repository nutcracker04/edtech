import { useState } from 'react';
import { Subject } from '@/types';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { estimateTestDuration } from '@/services/adaptiveAlgorithm';
import { Clock, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AdaptiveTestConfigProps {
  onSubmit: (config: {
    numberOfQuestions: number;
    focusOnWeakAreas: number;
    includeStrongAreas: boolean;
    subject?: Subject;
  }) => void;
  isLoading?: boolean;
}

export function AdaptiveTestConfig({ onSubmit, isLoading }: AdaptiveTestConfigProps) {
  const [numberOfQuestions, setNumberOfQuestions] = useState(25);
  const [focusOnWeakAreas, setFocusOnWeakAreas] = useState(60);
  const [includeStrongAreas, setIncludeStrongAreas] = useState(true);
  const [subject, setSubject] = useState<Subject | undefined>(undefined);

  const duration = estimateTestDuration(numberOfQuestions);

  const handleSubmit = () => {
    onSubmit({
      numberOfQuestions,
      focusOnWeakAreas,
      includeStrongAreas,
      subject,
    });
  };

  return (
    <div className="space-y-6">
      {/* Questions Count */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-foreground">Number of Questions</label>
            <span className="text-lg font-semibold text-primary">{numberOfQuestions}</span>
          </div>
          <Slider
            value={[numberOfQuestions]}
            onValueChange={(val) => setNumberOfQuestions(val[0])}
            min={5}
            max={100}
            step={5}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-2">
            <span>5 Questions</span>
            <span>100 Questions</span>
          </div>
        </div>

        <div className="flex items-center gap-3 p-4 rounded-lg bg-primary/10 border border-primary/20">
          <Clock className="h-5 w-5 text-primary" />
          <div>
            <p className="text-sm font-medium text-foreground">Estimated Duration</p>
            <p className="text-xs text-muted-foreground">{duration} minutes</p>
          </div>
        </div>
      </div>

      {/* Weak Areas Focus */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-foreground">Focus on Weak Areas</label>
            <span className="text-lg font-semibold text-primary">{focusOnWeakAreas}%</span>
          </div>
          <Slider
            value={[focusOnWeakAreas]}
            onValueChange={(val) => setFocusOnWeakAreas(val[0])}
            min={0}
            max={100}
            step={10}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-2">
            <span>0% - Balanced</span>
            <span>100% - All Weak</span>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-secondary/30 text-sm text-muted-foreground">
          <div className="flex items-start gap-2">
            <Zap className="h-4 w-4 text-yellow-500 mt-0.5 shrink-0" />
            <p>
              {focusOnWeakAreas === 0 && "Balanced test with mixed difficulty"}
              {focusOnWeakAreas <= 40 && focusOnWeakAreas > 0 && "More focus on weak areas with balanced coverage"}
              {focusOnWeakAreas > 40 && focusOnWeakAreas <= 70 && "Strong focus on weak areas - targeted improvement"}
              {focusOnWeakAreas > 70 && "Intense focus on weak areas - deep practice needed"}
            </p>
          </div>
        </div>
      </div>

      {/* Include Strong Areas */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-foreground">Include Strong Areas</p>
            <p className="text-sm text-muted-foreground mt-1">
              Add questions from topics you're already good at to maintain skills
            </p>
          </div>
          <Switch
            checked={includeStrongAreas}
            onCheckedChange={setIncludeStrongAreas}
          />
        </div>
      </div>

      {/* Subject Selection (Optional) */}
      <div className="bg-card border border-border rounded-xl p-6">
        <p className="font-medium text-foreground mb-3">Focus Subject (Optional)</p>
        <div className="grid grid-cols-3 gap-3">
          {(['physics', 'chemistry', 'mathematics'] as const).map(subj => (
            <button
              key={subj}
              onClick={() => setSubject(subject === subj ? undefined : subj)}
              className={cn(
                'p-3 rounded-lg border-2 transition-all text-center text-sm',
                subject === subj
                  ? 'border-primary bg-primary/10 font-medium'
                  : 'border-border hover:border-primary/50'
              )}
            >
              {subj.charAt(0).toUpperCase() + subj.slice(1)}
            </button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground mt-3">
          Leave blank for mixed subject test
        </p>
      </div>

      {/* Submit Button */}
      <Button
        onClick={handleSubmit}
        disabled={isLoading}
        size="lg"
        className="w-full"
      >
        {isLoading ? 'Generating Test...' : 'Generate Adaptive Test'}
      </Button>
    </div>
  );
}
