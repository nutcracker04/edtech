import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Minimize2, Maximize2 } from 'lucide-react';
import { useState } from 'react';

interface MistakesChartProps {
    data: {
        chapter: string;
        incorrect: number;
        correct: number;
        unattempted: number;
    }[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-background border rounded-lg p-3 shadow-lg text-sm">
                <p className="font-semibold mb-2">{label}</p>
                {payload.map((entry: any, index: number) => (
                    <div key={index} className="flex items-center gap-2 mb-1">
                        <div
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: entry.color }}
                        />
                        <span className="text-muted-foreground capitalize">
                            {entry.name}:
                        </span>
                        <span className="font-medium">
                            {entry.value}
                        </span>
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

export const MistakesChart = ({ data }: MistakesChartProps) => {
    const [isExpanded, setIsExpanded] = useState(true);

    return (
        <Card className="w-full">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="text-lg font-bold">Your Mistakes Overview</CardTitle>
                        <p className="text-sm text-muted-foreground mt-1">
                            This graph shows how you performed across different chapters.
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="flex gap-1">
                            <Button variant="outline" size="icon" className="h-8 w-8">
                                <ChevronLeft className="h-4 w-4" />
                            </Button>
                            <Button variant="outline" size="icon" className="h-8 w-8">
                                <ChevronRight className="h-4 w-4" />
                            </Button>
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            className="h-8 px-3 ml-2 text-primary"
                            onClick={() => setIsExpanded(!isExpanded)}
                        >
                            {isExpanded ? 'HIDE' : 'SHOW'}
                            {isExpanded ? <Minimize2 className="ml-2 h-3 w-3" /> : <Maximize2 className="ml-2 h-3 w-3" />}
                        </Button>
                    </div>
                </div>
            </CardHeader>

            {isExpanded && (
                <CardContent>
                    {/* Custom Legend */}
                    <div className="flex items-center gap-6 mb-6 text-sm">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-500" />
                            <span>Incorrect Qs</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-emerald-500" />
                            <span>Correct Qs</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-slate-500" />
                            <span>Not attempted Qs</span>
                        </div>
                    </div>

                    <div className="h-[400px] w-full overflow-x-auto pb-4">
                        <div style={{ width: `${data.length * 120}px`, minWidth: "100%", height: "100%" }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart
                                    data={data}
                                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                    <XAxis
                                        dataKey="chapter"
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: '#6B7280', fontSize: 12 }}
                                        interval={0}
                                    />
                                    <YAxis
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fill: '#6B7280', fontSize: 12 }}
                                    />
                                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'transparent' }} />
                                    <Legend wrapperStyle={{ paddingTop: '20px' }} />

                                    <Bar name="Correct Qs" dataKey="correct" stackId="a" fill="#10B981" radius={[0, 0, 4, 4]} barSize={40} />
                                    <Bar name="Incorrect Qs" dataKey="incorrect" stackId="a" fill="#EF4444" radius={[0, 0, 0, 0]} barSize={40} />
                                    <Bar name="Not attempted Qs" dataKey="unattempted" stackId="a" fill="#94A3B8" radius={[4, 4, 0, 0]} barSize={40} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </CardContent>
            )}
        </Card>
    );
};
