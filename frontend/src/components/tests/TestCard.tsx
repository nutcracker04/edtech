import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calendar, Clock, Target, Play, ChevronRight, CheckCircle, BarChart } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';

interface Test {
    id: string;
    title: string;
    subject: string;
    type: "full" | "topic" | "adaptive";
    questions: number;
    duration: number;
    score?: number;
    date: string;
    status: "completed" | "in_progress" | "upcoming";
    scheduledAt?: Date | null;
}

interface TestCardProps {
    test: Test;
}

export function TestCard({ test }: TestCardProps) {
    const navigate = useNavigate();

    const getStatusBadge = (status: Test["status"]) => {
        switch (status) {
            case "completed":
                return "bg-green-500/20 text-green-700 hover:bg-green-500/30 border-green-200";
            case "in_progress":
                return "bg-blue-500/20 text-blue-700 hover:bg-blue-500/30 border-blue-200";
            case "upcoming":
                return "bg-secondary text-secondary-foreground hover:bg-secondary/80";
            default:
                return "bg-secondary text-secondary-foreground";
        }
    };

    const getTypeBadge = (type: Test["type"]) => {
        switch (type) {
            case "full":
                return "bg-purple-500/10 text-purple-700 border-purple-200";
            case "topic":
                return "bg-blue-500/10 text-blue-700 border-blue-200";
            case "adaptive":
                return "bg-orange-500/10 text-orange-700 border-orange-200";
            default:
                return "bg-secondary";
        }
    };

    return (
        <Card className="hover:shadow-md transition-all duration-200 border-border/50 group">
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1.5 flex-1 min-w-0">
                        <CardTitle className="text-lg font-semibold truncate pr-2 group-hover:text-primary transition-colors">
                            {test.title}
                        </CardTitle>
                        <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline" className={cn("text-xs font-medium border", getTypeBadge(test.type))}>
                                {test.type === 'full' ? 'Full Test' : test.type === 'topic' ? 'Topic Test' : 'Adaptive'}
                            </Badge>
                            <Badge variant="outline" className={cn("text-xs capitalize border", getStatusBadge(test.status))}>
                                {test.status.replace("_", " ")}
                            </Badge>
                        </div>
                    </div>
                    {test.score !== undefined && (
                        <div className="flex flex-col items-end shrink-0">
                            <div className={cn(
                                "text-lg font-bold",
                                test.score >= 80 ? "text-green-600" :
                                    test.score >= 60 ? "text-blue-600" :
                                        "text-orange-600"
                            )}>
                                {test.score}%
                            </div>
                            <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">Score</span>
                        </div>
                    )}
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Metadata */}
                <div className="grid grid-cols-2 gap-y-2 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2 col-span-2">
                        <div className="h-1.5 w-1.5 rounded-full bg-primary/60" />
                        <span className="truncate text-foreground/80 font-medium">{test.subject}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Target className="h-4 w-4 shrink-0 opacity-70" />
                        <span>{test.questions} Qs</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 shrink-0 opacity-70" />
                        <span>{test.duration} min</span>
                    </div>
                    <div className="flex items-center gap-2 col-span-2 pt-1 border-t mt-1">
                        <Calendar className="h-4 w-4 shrink-0 opacity-70" />
                        <span>{test.date}</span>
                    </div>
                </div>

                {/* Actions */}
                <div className="pt-2">
                    {test.status === 'completed' ? (
                        <Button
                            className="w-full bg-secondary/50 hover:bg-secondary text-foreground hover:text-primary border border-transparent hover:border-border/50 shadow-sm"
                            variant="secondary"
                            onClick={() => navigate(`/tests/${test.id}/results`)}
                        >
                            <BarChart className="h-4 w-4 mr-2 opacity-60" />
                            View Analysis
                            <ChevronRight className="h-4 w-4 ml-auto opacity-50" />
                        </Button>
                    ) : (
                        <Button
                            className={cn(
                                "w-full shadow-sm",
                                test.status === 'in_progress'
                                    ? "bg-blue-600 hover:bg-blue-700"
                                    : "bg-primary hover:bg-primary/90"
                            )}
                            onClick={() => navigate(`/test/${test.id}`)}
                        >
                            {test.status === 'in_progress' ? (
                                <>
                                    <Play className="h-4 w-4 mr-2" />
                                    Continue Test
                                </>
                            ) : (
                                <>
                                    <Play className="h-4 w-4 mr-2" />
                                    Start Test
                                </>
                            )}
                            <ChevronRight className="h-4 w-4 ml-auto opacity-50" />
                        </Button>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
