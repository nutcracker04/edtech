import { useState, useEffect } from 'react';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { CheckSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Option {
  id: string;
  text: string;
}

interface MultiSelectProps {
  options: Option[];
  selectedValues?: string[];
  onChange: (selected: string[]) => void;
  questionText: string;
  minSelections?: number;
  maxSelections?: number;
}

export function MultiSelect({
  options,
  selectedValues = [],
  onChange,
  questionText,
  minSelections,
  maxSelections,
}: MultiSelectProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set(selectedValues));

  useEffect(() => {
    setSelected(new Set(selectedValues));
  }, [selectedValues]);

  const handleToggle = (optionId: string) => {
    const newSelected = new Set(selected);

    if (newSelected.has(optionId)) {
      newSelected.delete(optionId);
    } else {
      // Check if we've reached max selections
      if (maxSelections && newSelected.size >= maxSelections) {
        return; // Don't allow more selections
      }
      newSelected.add(optionId);
    }

    setSelected(newSelected);
    onChange(Array.from(newSelected));
  };

  const getSelectionInfo = () => {
    const count = selected.size;
    
    if (minSelections && maxSelections) {
      return `Select ${minSelections} to ${maxSelections} options`;
    } else if (minSelections) {
      return `Select at least ${minSelections} option(s)`;
    } else if (maxSelections) {
      return `Select up to ${maxSelections} option(s)`;
    }
    return 'Select all that apply';
  };

  const isValidSelection = () => {
    const count = selected.size;
    
    if (minSelections && count < minSelections) return false;
    if (maxSelections && count > maxSelections) return false;
    
    return true;
  };

  return (
    <div className="space-y-4">
      <div className="p-4 bg-muted rounded-lg">
        <p className="text-sm whitespace-pre-wrap">{questionText}</p>
      </div>

      <div className="space-y-4">
        {/* Instructions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckSquare className="h-4 w-4 text-primary" />
            <Label className="text-base">{getSelectionInfo()}</Label>
          </div>
          <Badge variant={isValidSelection() ? 'default' : 'secondary'}>
            {selected.size} selected
          </Badge>
        </div>

        {/* Options */}
        <div className="space-y-3">
          {options.map((option) => {
            const isSelected = selected.has(option.id);
            const isDisabled = !isSelected && maxSelections && selected.size >= maxSelections;

            return (
              <div
                key={option.id}
                className={cn(
                  'flex items-start space-x-3 p-4 rounded-lg border-2 transition-colors',
                  isSelected
                    ? 'border-primary bg-primary/5'
                    : isDisabled
                    ? 'border-border bg-muted/50 opacity-50 cursor-not-allowed'
                    : 'border-border hover:border-primary/50 cursor-pointer'
                )}
                onClick={() => !isDisabled && handleToggle(option.id)}
              >
                <Checkbox
                  id={`option-${option.id}`}
                  checked={isSelected}
                  onCheckedChange={() => !isDisabled && handleToggle(option.id)}
                  disabled={isDisabled}
                  className="mt-0.5"
                />
                <Label
                  htmlFor={`option-${option.id}`}
                  className={cn(
                    'flex-1 cursor-pointer font-normal',
                    isDisabled && 'cursor-not-allowed'
                  )}
                >
                  <span className="font-medium mr-2">{option.id}.</span>
                  {option.text}
                </Label>
              </div>
            );
          })}
        </div>

        {/* Validation Message */}
        {!isValidSelection() && selected.size > 0 && (
          <div className="text-sm text-amber-600 flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-950 rounded-lg">
            <AlertCircle className="h-4 w-4" />
            <span>
              {minSelections && selected.size < minSelections
                ? `Please select at least ${minSelections - selected.size} more option(s)`
                : `You can select up to ${maxSelections} option(s)`}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
