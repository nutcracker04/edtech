import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export type TimeRange = '7d' | '30d' | '90d' | 'all';

interface TimeRangeSelectorProps {
  value: TimeRange;
  onChange: (range: TimeRange) => void;
}

const ranges: { value: TimeRange; label: string }[] = [
  { value: '7d', label: '7 Days' },
  { value: '30d', label: '30 Days' },
  { value: '90d', label: '90 Days' },
  { value: 'all', label: 'All Time' },
];

export function TimeRangeSelector({ value, onChange }: TimeRangeSelectorProps) {
  return (
    <div className="flex gap-2">
      {ranges.map((range) => (
        <Button
          key={range.value}
          variant={value === range.value ? 'default' : 'outline'}
          size="sm"
          onClick={() => onChange(range.value)}
          className={cn(
            'text-xs',
            value === range.value && 'shadow-sm'
          )}
        >
          {range.label}
        </Button>
      ))}
    </div>
  );
}
