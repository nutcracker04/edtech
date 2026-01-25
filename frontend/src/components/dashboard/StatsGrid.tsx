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
  const { data: overallStats } = useOverallStats();

  // Format stats from real data
  const stats: StatItem[] = [
    {
      label: "Questions Solved",
      value: overallStats?.totalQuestions?.toString() || "0",
      change: `${overallStats?.totalCorrect || 0} correct`,
      icon: Target,
      positive: true,
    },
    {
      label: "Study Hours",
      value: overallStats?.totalTimeSpent
        ? `${(overallStats.totalTimeSpent / 3600).toFixed(1)}h`
        : "0h",
      change: "Total time spent",
      icon: Clock,
      positive: true,
    },
    {
      label: "Avg. Accuracy",
      value: overallStats?.averageAccuracy
        ? `${overallStats.averageAccuracy.toFixed(0)}%`
        : "0%",
      change: overallStats?.averageAccuracy && overallStats.averageAccuracy > 70
        ? "Great job!"
        : "Keep practicing",
      icon: TrendingUp,
      positive: true,
    },
    {
      label: "Tests Completed",
      value: overallStats?.testsCompleted?.toString() || "0",
      change: overallStats?.averageScore
        ? `Avg: ${overallStats.averageScore.toFixed(0)}%`
        : "No tests yet",
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
