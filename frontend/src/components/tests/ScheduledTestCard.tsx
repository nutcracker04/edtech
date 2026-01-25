import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calendar, Clock, Play, Trash2, Edit } from 'lucide-react';
import { format, formatDistanceToNow, isPast, isFuture, differenceInMinutes } from 'date-fns';
import { cn } from '@/lib/utils';

interface ScheduledTest {
  id: string;
  title: string;
  type: string;
  subject?: string;
  duration: number;
  scheduledAt: Date;
  status: 'upcoming' | 'missed' | 'in_progress';
}

interface ScheduledTestCardProps {
  test: ScheduledTest;
  onStart: (testId: string) => void;
  onEdit: (testId: string) => void;
  onDelete: (testId: string) => void;
}

export function ScheduledTestCard({ test, onStart, onEdit, onDelete }: ScheduledTestCardProps) {
  const scheduledDate = new Date(test.scheduledAt);
  const minutesUntil = differenceInMinutes(scheduledDate, new Date());
  const canStart = minutesUntil <= 5 && minutesUntil >= -10; // 5 minutes before to 10 minutes after
  const isMissed = isPast(scheduledDate) && !canStart;

  const getStatusBadge = () => {
    if (isMissed) {
      return <Badge variant="destructive">Missed</Badge>;
    }
    if (canStart) {
      return <Badge className="bg-green-500">Ready to Start</Badge>;
    }
    return <Badge variant="outline">Upcoming</Badge>;
  };

  const getTimeDisplay = () => {
    if (isMissed) {
      return (
        <span className="text-sm text-red-600">
          Missed • {formatDistanceToNow(scheduledDate, { addSuffix: true })}
        </span>
      );
    }
    if (canStart) {
      return (
        <span className="text-sm text-green-600 font-medium">
          Available now • Start within {Math.abs(minutesUntil) < 5 ? 'next 5 minutes' : `${10 - Math.abs(minutesUntil)} minutes`}
        </span>
      );
    }
    return (
      <span className="text-sm text-muted-foreground">
        {formatDistanceToNow(scheduledDate, { addSuffix: true })}
      </span>
    );
  };

  return (
    <Card className={cn(
      'hover:shadow-md transition-shadow',
      canStart && 'border-green-500 bg-green-50 dark:bg-green-950',
      isMissed && 'opacity-60'
    )}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <CardTitle className="text-lg">{test.title}</CardTitle>
            <div className="flex flex-wrap items-center gap-2">
              {getStatusBadge()}
              {test.subject && (
                <Badge variant="outline" className="capitalize">
                  {test.subject}
                </Badge>
              )}
              <Badge variant="secondary" className="capitalize">
                {test.type}
              </Badge>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Schedule Info */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span>{format(scheduledDate, 'PPP')}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span>{format(scheduledDate, 'p')} • {test.duration} minutes</span>
          </div>
          <div className="pt-1">
            {getTimeDisplay()}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          {canStart && !isMissed ? (
            <Button 
              className="flex-1 bg-green-600 hover:bg-green-700" 
              onClick={() => onStart(test.id)}
            >
              <Play className="h-4 w-4 mr-2" />
              Start Test
            </Button>
          ) : !isMissed ? (
            <Button 
              variant="outline" 
              className="flex-1" 
              onClick={() => onEdit(test.id)}
            >
              <Edit className="h-4 w-4 mr-2" />
              Reschedule
            </Button>
          ) : (
            <Button 
              variant="outline" 
              className="flex-1" 
              onClick={() => onEdit(test.id)}
              disabled
            >
              Missed
            </Button>
          )}
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => onDelete(test.id)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
