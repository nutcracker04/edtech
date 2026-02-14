import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  ComposedChart,
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine,
  Legend
} from 'recharts';
import { TrendDataPoint } from '@/types/analysis';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface TrendGraphsProps {
  accuracyData: TrendDataPoint[];
  questionCountData: TrendDataPoint[];
}

export const TrendGraphs: React.FC<TrendGraphsProps> = ({
  accuracyData,
  questionCountData,
}) => {
  // Format data for charts
  const accuracyChartData = accuracyData.map((point) => ({
    date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    accuracy: point.accuracy || 0,
  }));

  const questionChartData = questionCountData.map((point) => ({
    date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    count: point.count || 0,
  }));

  // Calculate statistics
  const avgAccuracy = accuracyChartData.length > 0 
    ? accuracyChartData.reduce((sum, d) => sum + d.accuracy, 0) / accuracyChartData.length 
    : 0;
  
  const recentAccuracy = accuracyChartData.length > 0 
    ? accuracyChartData[accuracyChartData.length - 1].accuracy 
    : 0;
  
  const accuracyTrend = accuracyChartData.length > 1
    ? recentAccuracy - accuracyChartData[0].accuracy
    : 0;

  const totalQuestions = questionChartData.reduce((sum, d) => sum + d.count, 0);
  const avgQuestions = questionChartData.length > 0 
    ? totalQuestions / questionChartData.length 
    : 0;

  // Custom tooltip for trading-style display
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border border-border rounded-lg shadow-lg p-3">
          <p className="font-semibold text-sm mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center gap-2 text-sm">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-muted-foreground">{entry.name}:</span>
              <span className="font-bold">{entry.value}{entry.name.includes('Accuracy') ? '%' : ''}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Accuracy Trend - Trading Style */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-blue-600" />
                Accuracy Trend
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">Your accuracy percentage over time</p>
            </div>
            <div className="text-right space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold">{recentAccuracy.toFixed(1)}%</span>
                {accuracyTrend !== 0 && (
                  <Badge variant={accuracyTrend > 0 ? "default" : "destructive"} className="gap-1">
                    {accuracyTrend > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                    {Math.abs(accuracyTrend).toFixed(1)}%
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground">Avg: {avgAccuracy.toFixed(1)}%</p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {accuracyChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart 
                data={accuracyChartData}
                margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="accuracyGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                />
                <YAxis 
                  domain={[0, 100]} 
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                  label={{ value: 'Accuracy %', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
                />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine 
                  y={avgAccuracy} 
                  stroke="#f59e0b" 
                  strokeDasharray="5 5" 
                  label={{ value: 'Avg', position: 'right', fill: '#f59e0b', fontSize: 11 }}
                />
                <Area
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  fill="url(#accuracyGradient)"
                  dot={{ fill: '#3b82f6', r: 4, strokeWidth: 2, stroke: '#fff' }}
                  activeDot={{ r: 6, strokeWidth: 2 }}
                  name="Accuracy"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-muted-foreground py-20">No data available</p>
          )}
        </CardContent>
      </Card>

      {/* Question Count Trend - Trading Style */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-emerald-600" />
                Questions Solved Trend
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">Daily question solving activity</p>
            </div>
            <div className="text-right space-y-1">
              <div className="text-2xl font-bold">{totalQuestions}</div>
              <p className="text-xs text-muted-foreground">Avg: {avgQuestions.toFixed(1)}/day</p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {questionChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart 
                data={questionChartData}
                margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="questionGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.2}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                  label={{ value: 'Questions', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
                />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine 
                  y={avgQuestions} 
                  stroke="#f59e0b" 
                  strokeDasharray="5 5" 
                  label={{ value: 'Avg', position: 'right', fill: '#f59e0b', fontSize: 11 }}
                />
                <Bar
                  dataKey="count"
                  fill="url(#questionGradient)"
                  radius={[8, 8, 0, 0]}
                  name="Questions"
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#059669"
                  strokeWidth={2}
                  dot={false}
                  name="Trend"
                />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-muted-foreground py-20">No data available</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
