import { Calendar, Clock, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface UpcomingTest {
  id: string;
  title: string;
  date: Date;
  duration: number;
  type: 'adaptive' | 'mock' | 'topic';
}

const mockUpcomingTests: UpcomingTest[] = [
  {
    id: '1',
    title: 'Adaptive Physics Test',
    date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000), // 2 days from now
    duration: 60,
    type: 'adaptive',
  },
  {
    id: '2',
    title: 'Full JEE Mock - Set 3',
    date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000), // 5 days from now
    duration: 180,
    type: 'mock',
  },
  {
    id: '3',
    title: 'Chemistry: Equilibrium',
    date: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000),
    duration: 45,
    type: 'topic',
  },
  {
    id: '4',
    title: 'Maths: Integration',
    date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000),
    duration: 90,
    type: 'topic',
  },
  {
    id: '5',
    title: 'Physics: Rotation',
    date: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000),
    duration: 60,
    type: 'adaptive',
  },
];

export function UpcomingTestsWidget() {
  const navigate = useNavigate();

  const getTypeBadgeColor = (type: 'adaptive' | 'mock' | 'topic') => {
    switch (type) {
      case 'adaptive':
        return 'bg-blue-500/20 text-blue-400';
      case 'mock':
        return 'bg-purple-500/20 text-purple-400';
      case 'topic':
        return 'bg-orange-500/20 text-orange-400';
    }
  };

  const formatDate = (date: Date) => {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    }
    if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    }

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-foreground">Upcoming</h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/tests')}
          className="text-primary"
        >
          View All →
        </Button>
      </div>

      {mockUpcomingTests.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center space-y-3">
            <Calendar className="h-8 w-8 text-muted-foreground mx-auto opacity-50" />
            <div>
              <p className="font-medium text-foreground">No upcoming tests</p>
              <p className="text-sm text-muted-foreground">
                Schedule a test to stay on track with your preparation
              </p>
            </div>
            <Button
              onClick={() => navigate('/tests')}
              size="sm"
              className="w-full"
            >
              Schedule a Test
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="max-h-[350px] overflow-y-auto pr-2 space-y-3 scrollbar-thin scrollbar-thumb-primary/20">
          {mockUpcomingTests.map((test) => (
            <Card
              key={test.id}
              className="hover:border-primary/50 hover:bg-secondary/30 transition-all group cursor-pointer border-border/50"
              onClick={() => navigate(`/test/${test.id}`)}
            >
              <CardContent className="pt-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-sm text-foreground truncate group-hover:text-primary transition-colors">
                      {test.title}
                    </h3>
                    <Badge className={cn('mt-2 h-5 text-[10px]', getTypeBadgeColor(test.type))}>
                      {test.type.charAt(0).toUpperCase() + test.type.slice(1)}
                    </Badge>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-1 transition-transform shrink-0" />
                </div>

                <div className="flex items-center gap-4 text-[10px] text-muted-foreground font-medium">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatDate(test.date)}
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {test.duration} min
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
