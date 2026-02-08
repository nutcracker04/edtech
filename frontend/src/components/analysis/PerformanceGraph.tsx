import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { TimeRangeSelector, TimeRange } from './TimeRangeSelector';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

type ChartType = 'line' | 'area' | 'bar';

interface PerformanceDataPoint {
  date: string;
  physics?: number;
  chemistry?: number;
  mathematics?: number;
  overall?: number;
}

interface PerformanceGraphProps {
  title: string;
  description?: string;
  data: PerformanceDataPoint[];
  chartType?: ChartType;
  showSubjects?: boolean;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  label?: string;
}

export function PerformanceGraph({
  title,
  description,
  data,
  chartType = 'line',
  showSubjects = true,
}: PerformanceGraphProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');
  const [activeChart, setActiveChart] = useState<ChartType>(chartType);

  // Filter data based on time range
  const getFilteredData = () => {
    const now = new Date();
    const daysMap: Record<TimeRange, number> = {
      '7d': 7,
      '30d': 30,
      '90d': 90,
      'all': 3650,
    };

    const days = daysMap[timeRange];
    const cutoffDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

    return data.filter((point) => {
      const pointDate = new Date(point.date);
      return pointDate >= cutoffDate;
    });
  };

  const filteredData = getFilteredData();

  const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-popover border border-border rounded-xl shadow-xl p-3 text-xs">
          <p className="font-bold text-foreground mb-2 px-1">{label}</p>
          <div className="space-y-1.5">
            {payload.map((entry, index: number) => (
              <div key={index} className="flex items-center justify-between gap-6 px-1">
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: entry.color }} />
                  <span className="text-muted-foreground capitalize">{entry.name}:</span>
                </div>
                <span className="font-bold text-foreground">{entry.value}%</span>
              </div>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  const renderChart = () => {
    const commonProps = {
      data: filteredData,
      margin: { top: 10, right: 10, left: -20, bottom: 0 },
    };

    const dataKeys = showSubjects
      ? ['physics', 'chemistry', 'mathematics']
      : ['overall'];

    const colors = {
      physics: '#3b82f6',
      chemistry: '#10b981',
      mathematics: '#f59e0b',
      overall: '#8b5cf6',
    };

    switch (activeChart) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border)/0.3)" />
            <XAxis
              dataKey="date"
              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
              stroke="transparent"
              dy={10}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
              stroke="transparent"
              dx={-10}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="top"
              align="right"
              iconType="circle"
              wrapperStyle={{ paddingBottom: '20px', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}
            />
            {dataKeys.map((key) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[key as keyof typeof colors]}
                strokeWidth={3}
                dot={{ r: 4, strokeWidth: 2, fill: 'hsl(var(--background))' }}
                activeDot={{ r: 6, strokeWidth: 0 }}
                name={key}
              />
            ))}
          </LineChart>
        );

      case 'area':
        return (
          <AreaChart {...commonProps}>
            <defs>
              {dataKeys.map(key => (
                <linearGradient key={`gradient-${key}`} id={`gradient-${key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={colors[key as keyof typeof colors]} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={colors[key as keyof typeof colors]} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border)/0.3)" />
            <XAxis
              dataKey="date"
              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
              stroke="transparent"
              dy={10}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
              stroke="transparent"
              dx={-10}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="top"
              align="right"
              iconType="circle"
              wrapperStyle={{ paddingBottom: '20px', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}
            />
            {dataKeys.map((key) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[key as keyof typeof colors]}
                strokeWidth={2}
                fill={`url(#gradient-${key})`}
                name={key}
              />
            ))}
          </AreaChart>
        );

      case 'bar':
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border)/0.3)" />
            <XAxis
              dataKey="date"
              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
              stroke="transparent"
              dy={10}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
              stroke="transparent"
              dx={-10}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="top"
              align="right"
              iconType="circle"
              wrapperStyle={{ paddingBottom: '20px', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}
            />
            {dataKeys.map((key) => (
              <Bar
                key={key}
                dataKey={key}
                fill={colors[key as keyof typeof colors]}
                radius={[4, 4, 0, 0]}
                barSize={30}
                name={key}
              />
            ))}
          </BarChart>
        );
    }
  };

  return (
    <Card className="overflow-hidden bg-card/50 backdrop-blur-sm border-border/50">
      <CardHeader className="pb-0">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <CardTitle className="text-lg font-bold tracking-tight">{title}</CardTitle>
            {description && (
              <CardDescription className="text-xs">{description}</CardDescription>
            )}
          </div>
          <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
        </div>

        <div className="mt-6 flex items-center justify-between pb-4">
          <Tabs value={activeChart} onValueChange={(v) => setActiveChart(v as ChartType)}>
            <TabsList className="bg-secondary/50 p-1 h-8">
              <TabsTrigger value="line" className="text-[10px] px-3 h-6">Line</TabsTrigger>
              <TabsTrigger value="area" className="text-[10px] px-3 h-6">Area</TabsTrigger>
              <TabsTrigger value="bar" className="text-[10px] px-3 h-6">Bar</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </CardHeader>

      <CardContent className="pt-2 pb-6">
        <div className="h-[350px] w-full mt-2">
          {filteredData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              {renderChart()!}
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 bg-secondary/10 rounded-2xl border border-dashed border-border/50">
              <div className="h-12 w-12 rounded-full bg-secondary/20 flex items-center justify-center mb-4 text-muted-foreground">
                <LineChart className="h-6 w-6" />
              </div>
              <p className="font-semibold text-foreground">No insight data available</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-[200px]">
                Complete more tests to generate performance trends
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
