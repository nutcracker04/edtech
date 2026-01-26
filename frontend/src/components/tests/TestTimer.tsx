import { useEffect, useState, useRef } from 'react';
import { Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TestTimerProps {
  duration: number; // in minutes
  onTimeUp?: () => void;
  showWarning?: boolean;
}

export function TestTimer({ duration, onTimeUp, showWarning = true }: TestTimerProps) {
  const [timeLeft, setTimeLeft] = useState(duration * 60); // Convert to seconds
  const [isWarning, setIsWarning] = useState(false);
  const onTimeUpRef = useRef(onTimeUp);

  // Keep the ref updated with the latest callback
  useEffect(() => {
    onTimeUpRef.current = onTimeUp;
  }, [onTimeUp]);

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          onTimeUpRef.current?.();
          return 0;
        }

        const newTime = prev - 1;
        if (showWarning && newTime <= 300) {
          setIsWarning(true);
        }
        return newTime;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [showWarning]);

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  const percentage = (timeLeft / (duration * 60)) * 100;

  return (
    <div className={cn(
      'rounded-lg p-4 transition-all',
      isWarning
        ? 'bg-red-500/10 border border-red-500/30'
        : 'bg-card border border-border'
    )}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Clock className={cn(
            'h-5 w-5',
            isWarning ? 'text-red-500 animate-pulse' : 'text-primary'
          )} />
          <span className={cn(
            'text-sm font-medium',
            isWarning ? 'text-red-500' : 'text-muted-foreground'
          )}>
            Time Remaining
          </span>
        </div>
        <span className={cn(
          'text-2xl font-bold tabular-nums',
          isWarning ? 'text-red-500' : 'text-foreground'
        )}>
          {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full transition-all',
            isWarning ? 'bg-red-500' : 'bg-primary'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {isWarning && (
        <p className="text-xs text-red-500 mt-2">
          ⚠️ Time is running out! Complete your test soon.
        </p>
      )}
    </div>
  );
}
