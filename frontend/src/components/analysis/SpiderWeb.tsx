import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PerformanceBreadcrumb } from './PerformanceBreadcrumb';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { cn } from '@/lib/utils';
import { ScrollArea } from '@/components/ui/scroll-area';

type ViewLevel = 'subject' | 'chapter' | 'topic';

interface SubjectData {
  name: string;
  score: number;
  chapters: ChapterData[];
}

interface ChapterData {
  name: string;
  score: number;
  topics: TopicData[];
}

interface TopicData {
  name: string;
  score: number;
}

interface SpiderWebProps {
  data: SubjectData[];
  className?: string;
}

export function SpiderWeb({ data, className }: SpiderWebProps) {
  const [viewLevel, setViewLevel] = useState<ViewLevel>('subject');
  const [selectedSubject, setSelectedSubject] = useState<SubjectData | null>(null);
  const [selectedChapter, setSelectedChapter] = useState<ChapterData | null>(null);

  // Get current chart data based on view level
  const getChartData = () => {
    if (viewLevel === 'subject') {
      return data.map(subject => ({
        name: subject.name,
        score: subject.score,
        fullMark: 100,
      }));
    } else if (viewLevel === 'chapter' && selectedSubject) {
      return selectedSubject.chapters.map(chapter => ({
        name: chapter.name,
        score: chapter.score,
        fullMark: 100,
      }));
    } else if (viewLevel === 'topic' && selectedChapter) {
      return selectedChapter.topics.map(topic => ({
        name: topic.name,
        score: topic.score,
        fullMark: 100,
      }));
    }
    return [];
  };

  // Get breadcrumb items
  const getBreadcrumbs = () => {
    const items = [
      {
        label: 'All Subjects',
        onClick: () => {
          setViewLevel('subject');
          setSelectedSubject(null);
          setSelectedChapter(null);
        },
      },
    ];

    if (selectedSubject) {
      items.push({
        label: selectedSubject.name,
        onClick: () => {
          setViewLevel('chapter');
          setSelectedChapter(null);
        },
      });
    }

    if (selectedChapter) {
      items.push({
        label: selectedChapter.name,
        onClick: () => {
          setViewLevel('topic');
        },
      });
    }

    return items;
  };

  // Handle point click for drill-down
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handlePointClick = (dataPoint: any) => {
    const name = dataPoint.name as string;
    if (viewLevel === 'subject') {
      const subject = data.find(s => s.name === name);
      if (subject) {
        setSelectedSubject(subject);
        setViewLevel('chapter');
      }
    } else if (viewLevel === 'chapter' && selectedSubject) {
      const chapter = selectedSubject.chapters.find(c => c.name === dataPoint.name);
      if (chapter) {
        setSelectedChapter(chapter);
        setViewLevel('topic');
      }
    }
  };

  const chartData = getChartData();

  const getScoreColor = (score: number) => {
    if (score >= 75) return '#22c55e'; // green
    if (score >= 50) return '#eab308'; // yellow
    return '#ef4444'; // red
  };

  const getPerformanceLabel = (score: number) => {
    if (score >= 85) return 'Excellent';
    if (score >= 75) return 'Good';
    if (score >= 60) return 'Average';
    if (score >= 50) return 'Below Average';
    return 'Needs Improvement';
  };

  return (
    <Card className={cn("flex flex-col overflow-hidden", className)}>
      <CardHeader className="shrink-0 pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base sm:text-lg">Performance Spider Web</CardTitle>
            <CardDescription className="text-xs">
              {viewLevel === 'subject' && 'Click on any subject to view chapters'}
              {viewLevel === 'chapter' && 'Click on any chapter to view topics'}
              {viewLevel === 'topic' && 'Detailed topic-wise performance'}
            </CardDescription>
          </div>
          <Badge variant="outline" className="capitalize text-[10px] px-1.5 py-0 h-5">
            {viewLevel} Level
          </Badge>
        </div>

        {/* Breadcrumb Navigation */}
        {(selectedSubject || selectedChapter) && (
          <PerformanceBreadcrumb items={getBreadcrumbs()} />
        )}
      </CardHeader>

      <CardContent className="flex-1 min-h-0 p-0">
        <ScrollArea className="h-full px-6 pb-6">
          <div className="space-y-6 pt-2">
            {/* Radar Chart */}
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                  <PolarGrid stroke="hsl(var(--border))" />
                  <PolarAngleAxis
                    dataKey="name"
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                  />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 100]}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 8 }}
                  />
                  <Radar
                    name="Performance"
                    dataKey="score"
                    stroke="hsl(var(--primary))"
                    fill="hsl(var(--primary))"
                    fillOpacity={0.6}
                    onClick={(data) => viewLevel !== 'topic' && handlePointClick(data)}
                    style={{ cursor: viewLevel !== 'topic' ? 'pointer' : 'default' }}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-popover border border-border rounded-lg shadow-lg p-2 text-xs">
                            <p className="font-semibold">{data.name}</p>
                            <p className="text-muted-foreground mt-0.5">
                              Score: <span className="font-bold text-foreground">{data.score}%</span>
                            </p>
                            <div
                              className="mt-1.5 px-2 py-0.5 rounded-full border text-[10px] font-medium inline-block"
                              style={{ borderColor: getScoreColor(data.score), color: getScoreColor(data.score) }}
                            >
                              {getPerformanceLabel(data.score)}
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Performance Legend */}
            <div className="flex flex-wrap justify-center gap-x-4 gap-y-2 text-[10px] uppercase tracking-wider font-semibold opacity-80">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span className="text-muted-foreground">Excellent (75%+)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                <span className="text-muted-foreground">Average (50-75%)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-red-500"></div>
                <span className="text-muted-foreground">Needs Work (&lt;50%)</span>
              </div>
            </div>

            {/* Data Table */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-xs uppercase tracking-widest text-muted-foreground">Breakdown</h3>
                {viewLevel !== 'topic' && (
                  <span className="text-[10px] text-primary/70 animate-pulse font-medium">Click to explore ↓</span>
                )}
              </div>
              <div className="grid grid-cols-1 gap-2">
                {chartData.map((item) => (
                  <div
                    key={item.name}
                    className={cn(
                      'group flex items-center justify-between p-3 rounded-xl border border-border/50 bg-secondary/10 transition-all duration-200',
                      viewLevel !== 'topic' && 'cursor-pointer hover:bg-secondary/30 hover:border-primary/20'
                    )}
                    onClick={() => viewLevel !== 'topic' && handlePointClick(item)}
                  >
                    <span className="font-semibold text-sm group-hover:text-primary transition-colors">{item.name}</span>
                    <div className="flex items-center gap-4">
                      <div className="hidden sm:block w-24 h-1.5 bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full transition-all duration-500"
                          style={{
                            width: `${item.score}%`,
                            backgroundColor: getScoreColor(item.score),
                          }}
                        />
                      </div>
                      <Badge
                        variant="outline"
                        className="text-[11px] font-bold px-1.5 py-0 min-w-[40px] text-center justify-center"
                        style={{ borderColor: getScoreColor(item.score), color: getScoreColor(item.score) }}
                      >
                        {item.score}%
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
