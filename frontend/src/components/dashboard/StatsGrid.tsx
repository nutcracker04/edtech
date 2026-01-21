import { Target, Clock, TrendingUp, Award } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

interface StatItem {
  label: string;
  value: string;
  change: string;
  icon: React.ElementType;
  positive: boolean;
}

const stats: StatItem[] = [
  { label: "Questions Solved", value: "1,247", change: "+89 this week", icon: Target, positive: true },
  { label: "Study Hours", value: "42.5h", change: "+5.2h this week", icon: Clock, positive: true },
  { label: "Avg. Accuracy", value: "76%", change: "+3% improvement", icon: TrendingUp, positive: true },
  { label: "Tests Completed", value: "23", change: "Rank #156", icon: Award, positive: true },
];

export function StatsGrid() {
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
