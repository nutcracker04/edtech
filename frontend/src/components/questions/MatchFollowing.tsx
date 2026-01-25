import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MatchPair {
  leftId: string;
  leftText: string;
  rightId: string;
  rightText: string;
}

interface MatchFollowingProps {
  leftColumn: Array<{ id: string; text: string }>;
  rightColumn: Array<{ id: string; text: string }>;
  matches?: Record<string, string>; // leftId -> rightId
  onChange: (matches: Record<string, string>) => void;
  questionText: string;
}

export function MatchFollowing({
  leftColumn,
  rightColumn,
  matches = {},
  onChange,
  questionText,
}: MatchFollowingProps) {
  const [selectedMatches, setSelectedMatches] = useState<Record<string, string>>(matches);

  useEffect(() => {
    setSelectedMatches(matches);
  }, [matches]);

  const handleMatchChange = (leftId: string, rightId: string) => {
    const newMatches = { ...selectedMatches };
    
    if (rightId === '') {
      delete newMatches[leftId];
    } else {
      newMatches[leftId] = rightId;
    }

    setSelectedMatches(newMatches);
    onChange(newMatches);
  };

  const isRightOptionUsed = (rightId: string): boolean => {
    return Object.values(selectedMatches).includes(rightId);
  };

  const getAvailableRightOptions = (currentLeftId: string): typeof rightColumn => {
    return rightColumn.filter(
      (opt) => !isRightOptionUsed(opt.id) || selectedMatches[currentLeftId] === opt.id
    );
  };

  const completedCount = Object.keys(selectedMatches).length;
  const totalCount = leftColumn.length;
  const isComplete = completedCount === totalCount;

  return (
    <div className="space-y-4">
      <div className="p-4 bg-muted rounded-lg">
        <p className="text-sm whitespace-pre-wrap">{questionText}</p>
      </div>

      <div className="space-y-4">
        {/* Instructions */}
        <div className="flex items-center justify-between">
          <Label className="text-base">Match the items from Column A to Column B</Label>
          <Badge variant={isComplete ? 'default' : 'secondary'}>
            {completedCount}/{totalCount} matched
          </Badge>
        </div>

        {/* Matching Interface */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Column A (Left) */}
          <div className="space-y-2">
            <div className="font-medium text-sm text-muted-foreground px-2">Column A</div>
            <div className="space-y-3">
              {leftColumn.map((item) => (
                <Card
                  key={item.id}
                  className={cn(
                    'p-3 border-2',
                    selectedMatches[item.id] ? 'border-primary bg-primary/5' : 'border-border'
                  )}
                >
                  <div className="flex items-start gap-2">
                    {selectedMatches[item.id] ? (
                      <CheckCircle2 className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                    ) : (
                      <Circle className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1 min-w-0">
                      <Badge variant="outline" className="mb-2">
                        {item.id}
                      </Badge>
                      <p className="text-sm">{item.text}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Column B (Right) with Dropdowns */}
          <div className="space-y-2">
            <div className="font-medium text-sm text-muted-foreground px-2">Column B</div>
            <div className="space-y-3">
              {leftColumn.map((leftItem) => {
                const availableOptions = getAvailableRightOptions(leftItem.id);
                const selectedRightId = selectedMatches[leftItem.id];

                return (
                  <div key={leftItem.id} className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="w-12 justify-center">
                        {leftItem.id}
                      </Badge>
                      <span className="text-sm text-muted-foreground">matches</span>
                    </div>
                    <Select
                      value={selectedRightId || ''}
                      onValueChange={(value) => handleMatchChange(leftItem.id, value)}
                    >
                      <SelectTrigger className={cn(selectedRightId && 'border-primary')}>
                        <SelectValue placeholder="Select match..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">-- Clear selection --</SelectItem>
                        {availableOptions.map((rightItem) => (
                          <SelectItem key={rightItem.id} value={rightItem.id}>
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className="text-xs">
                                {rightItem.id}
                              </Badge>
                              <span className="text-sm">{rightItem.text}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Preview Matches */}
        {completedCount > 0 && (
          <Card className="bg-secondary/30 mt-4">
            <div className="p-4">
              <p className="text-sm font-medium mb-3">Your Matches:</p>
              <div className="grid grid-cols-1 gap-2">
                {Object.entries(selectedMatches).map(([leftId, rightId]) => {
                  const leftItem = leftColumn.find((i) => i.id === leftId);
                  const rightItem = rightColumn.find((i) => i.id === rightId);
                  
                  return (
                    <div key={leftId} className="flex items-center gap-2 text-sm">
                      <Badge variant="outline">{leftId}</Badge>
                      <span>→</span>
                      <Badge variant="outline">{rightId}</Badge>
                      <span className="text-muted-foreground text-xs">
                        ({leftItem?.text.substring(0, 20)}... → {rightItem?.text.substring(0, 20)}...)
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
