import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PerformanceBreadcrumb } from './PerformanceBreadcrumb';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { cn } from '@/lib/utils';

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
}

export function SpiderWeb({ data }: SpiderWebProps) {
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
  const handlePointClick = (dataPoint: any) => {
    if (viewLevel === 'subject') {
      const subject = data.find(s => s.name === dataPoint.name);
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
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Performance Spider Web</CardTitle>
            <CardDescription className="mt-1">
              {viewLevel === 'subject' && 'Click on any subject to view chapters'}
              {viewLevel === 'chapter' && 'Click on any chapter to view topics'}
              {viewLevel === 'topic' && 'Detailed topic-wise performance'}
            </CardDescription>
          </div>
          <Badge variant="outline" className="capitalize">
            {viewLevel} Level
          </Badge>
        </div>
        
        {/* Breadcrumb Navigation */}
        {(selectedSubject || selectedChapter) && (
          <PerformanceBreadcrumb items={getBreadcrumbs()} />
        )}
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Radar Chart */}
        <div className="h-[400px]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={chartData}>
              <PolarGrid stroke="hsl(var(--border))" />
              <PolarAngleAxis
                dataKey="name"
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
              />
              <PolarRadiusAxis
                angle={90}
                domain={[0, 100]}
                tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
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
                      <div className="bg-popover border border-border rounded-lg shadow-lg p-3">
                        <p className="font-medium">{data.name}</p>
                        <p className="text-sm text-muted-foreground">
                          Score: <span className="font-medium text-foreground">{data.score}%</span>
                        </p>
                        <Badge
                          variant="outline"
                          className="mt-1"
                          style={{ borderColor: getScoreColor(data.score) }}
                        >
                          {getPerformanceLabel(data.score)}
                        </Badge>
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
        <div className="flex justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-muted-foreground">75%+ Excellent</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span className="text-muted-foreground">50-75% Average</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-muted-foreground">&lt;50% Needs Work</span>
          </div>
        </div>

        {/* Data Table */}
        <div className="space-y-2">
          <h3 className="font-medium text-sm">Detailed Breakdown</h3>
          <div className="grid grid-cols-1 gap-2">
            {chartData.map((item) => (
              <div
                key={item.name}
                className={cn(
                  'flex items-center justify-between p-3 rounded-lg border',
                  viewLevel !== 'topic' && 'cursor-pointer hover:bg-secondary/50'
                )}
                onClick={() => viewLevel !== 'topic' && handlePointClick(item)}
              >
                <span className="font-medium">{item.name}</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full transition-all"
                      style={{
                        width: `${item.score}%`,
                        backgroundColor: getScoreColor(item.score),
                      }}
                    />
                  </div>
                  <Badge
                    variant="outline"
                    style={{ borderColor: getScoreColor(item.score) }}
                  >
                    {item.score}%
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>

        {viewLevel !== 'topic' && (
          <p className="text-xs text-muted-foreground text-center">
            💡 Click on any {viewLevel === 'subject' ? 'subject' : 'chapter'} to drill down
          </p>
        )}
      </CardContent>
    </Card>
  );
}
