import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface SubjectCardProps {
  title: string;
  icon: ReactNode;
  score: number;
  change: number;
  topics: { name: string; mastery: number }[];
}

export function SubjectCard({ title, icon, score, change, topics }: SubjectCardProps) {
  const getTrendIcon = () => {
    if (change > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (change < 0) return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <Minus className="h-4 w-4 text-muted-foreground" />;
  };

  const getScoreColor = (s: number) => {
    if (s >= 80) return "bg-green-500/20 text-green-400";
    if (s >= 60) return "bg-primary/20 text-primary";
    if (s >= 40) return "bg-yellow-500/20 text-yellow-400";
    return "bg-red-500/20 text-red-400";
  };

  const getMasteryWidth = (mastery: number) => `${mastery}%`;

  return (
    <Card className="hover:border-primary/50 transition-colors">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-secondary text-foreground">
              {icon}
            </div>
            <div>
              <h3 className="font-semibold text-foreground">{title}</h3>
              <div className="flex items-center gap-2 mt-0.5">
                {getTrendIcon()}
                <span className={cn(
                  "text-xs",
                  change > 0 ? "text-green-500" : change < 0 ? "text-red-500" : "text-muted-foreground"
                )}>
                  {change > 0 ? "+" : ""}{change}% this week
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {topics.slice(0, 3).map((topic) => (
          <div key={topic.name}>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-muted-foreground truncate">{topic.name}</span>
              <span className="text-foreground font-medium">{topic.mastery}%</span>
            </div>
            <Progress 
              value={topic.mastery} 
              className={cn(
                "h-1.5",
                topic.mastery >= 80 && "bg-green-500",
                topic.mastery >= 60 && topic.mastery < 80 && "bg-primary",
                topic.mastery >= 40 && topic.mastery < 60 && "bg-yellow-500",
                topic.mastery < 40 && "bg-red-500"
              )}
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
