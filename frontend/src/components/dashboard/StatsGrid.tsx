import { Target, Clock, TrendingUp, Award } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useOverallStats } from "@/hooks/usePerformance";

interface StatItem {
  label: string;
  value: string;
  change: string;
  icon: React.ElementType;
  positive: boolean;
}

export function StatsGrid() {
  const overallStats = useOverallStats();

  // Format stats from real data (matches getOverallStats shape)
  const stats: StatItem[] = [
    {
      label: "Questions Solved",
      value: overallStats.totalQuestionsAttempted.toString(),
      change: `${overallStats.totalQuestionsCorrect} correct`,
      icon: Target,
      positive: true,
    },
    {
      label: "Topics Covered",
      value: overallStats.totalTopicsCovered.toString(),
      change: `${overallStats.strongTopicsCount} strong, ${overallStats.weakTopicsCount} weak`,
      icon: Clock,
      positive: true,
    },
    {
      label: "Avg. Accuracy",
      value: `${overallStats.overallAccuracy}%`,
      change: overallStats.overallAccuracy > 70 ? "Great job!" : "Keep practicing",
      icon: TrendingUp,
      positive: true,
    },
    {
      label: "Avg. Mastery",
      value: `${overallStats.averageMastery}%`,
      change: "Across all topics",
      icon: Award,
      positive: true,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <Card key={stat.label} className="hover:border-primary/30 transition-colors">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-secondary">
                <stat.icon className="h-5 w-5 text-primary" />
              </div>
              <span className="text-sm text-muted-foreground">{stat.label}</span>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-2xl font-bold text-foreground">{stat.value}</div>
            <div className="text-xs text-muted-foreground mt-1">{stat.change}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
