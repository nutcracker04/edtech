import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';

interface IntegerInputProps {
  value?: string;
  onChange: (value: string) => void;
  min?: number;
  max?: number;
  questionText: string;
}

export function IntegerInput({ value = '', onChange, min, max, questionText }: IntegerInputProps) {
  const [inputValue, setInputValue] = useState(value);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  const validateInput = (val: string): string => {
    if (val === '') return '';

    // Check if it's a valid integer
    if (!/^-?\d+$/.test(val)) {
      return 'Please enter a valid integer';
    }

    const num = parseInt(val);

    // Check min/max bounds
    if (min !== undefined && num < min) {
      return `Value must be at least ${min}`;
    }
    if (max !== undefined && num > max) {
      return `Value must be at most ${max}`;
    }

    return '';
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInputValue(val);

    const validationError = validateInput(val);
    setError(validationError);

    // Only propagate valid values
    if (!validationError || val === '') {
      onChange(val);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Allow: backspace, delete, tab, escape, enter
    if ([8, 9, 27, 13, 46].includes(e.keyCode)) {
      return;
    }

    // Allow: Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
    if ((e.ctrlKey || e.metaKey) && [65, 67, 86, 88].includes(e.keyCode)) {
      return;
    }

    // Allow: home, end, left, right
    if (e.keyCode >= 35 && e.keyCode <= 39) {
      return;
    }

    // Allow: minus sign at the beginning
    if (e.key === '-' && inputValue === '') {
      return;
    }

    // Prevent if not a number
    if (!/^\d$/.test(e.key)) {
      e.preventDefault();
    }
  };

  return (
    <div className="space-y-4">
      <div className="p-4 bg-muted rounded-lg">
        <p className="text-sm whitespace-pre-wrap">{questionText}</p>
      </div>

      <Card className="p-6">
        <div className="space-y-4">
          <Label htmlFor="integer-answer" className="text-base">
            Enter your answer (Integer)
          </Label>
          
          <Input
            id="integer-answer"
            type="text"
            inputMode="numeric"
            value={inputValue}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={
              min !== undefined && max !== undefined
                ? `Enter a number between ${min} and ${max}`
                : 'Enter your answer'
            }
            className="text-2xl font-mono text-center h-16"
          />

          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          )}

          {min !== undefined && max !== undefined && (
            <p className="text-xs text-muted-foreground text-center">
              Valid range: {min} to {max}
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
