import { Flame, Trophy, Target, Clock, CheckCircle2, XCircle, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProgressWidgetProps {
  type: "streak" | "weekly" | "achievements";
}

// Generate heatmap data for the last 12 weeks (84 days)
const generateHeatmapData = () => {
  const data = [];
  for (let i = 83; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    // Random completion and intensity
    const completed = Math.random() > 0.3;
    const intensity = completed ? Math.floor(Math.random() * 4) + 1 : 0; // 0-4
    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      day: date.getDay(),
      completed,
      intensity, // 0: empty, 1: low, 2: medium, 3: high, 4: very high
    });
  }
  return data;
};

const heatmapData = generateHeatmapData();

const weeklyData = [
  { day: "Mon", completed: true, score: 85 },
  { day: "Tue", completed: true, score: 78 },
  { day: "Wed", completed: true, score: 92 },
  { day: "Thu", completed: true, score: 70 },
  { day: "Fri", completed: true, score: 88 },
  { day: "Sat", completed: false, score: 0 },
  { day: "Sun", completed: false, score: 0 },
];

const recentAchievements = [
  { name: "7-Day Streak", icon: "🔥", unlocked: true, date: "Today" },
  { name: "Physics Master", icon: "⚡", unlocked: true, date: "Yesterday" },
  { name: "100 Questions", icon: "📚", unlocked: true, date: "2 days ago" },
  { name: "Perfect Score", icon: "🎯", unlocked: false },
];

export function ProgressWidget({ type }: ProgressWidgetProps) {
  if (type === "streak") {
    const completedDays = heatmapData.filter(d => d.completed).length;
    const streakDays = 12; // Current streak
    
    const getHeatColor = (intensity: number) => {
      switch(intensity) {
        case 0: return "bg-secondary/20";
        case 1: return "bg-emerald-400/40";
        case 2: return "bg-emerald-500/60";
        case 3: return "bg-emerald-600/80";
        case 4: return "bg-emerald-700";
        default: return "bg-secondary/20";
      }
    };

    return (
      <div className="bg-card/50 border border-border rounded-xl p-6 my-3 space-y-6">
        {/* Header with Streak Info */}
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="h-14 w-14 rounded-xl bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center shadow-lg">
              <Flame className="h-7 w-7 text-white" />
            </div>
            <div>
              <div className="flex items-baseline gap-2">
                <h3 className="text-3xl font-bold text-foreground">{streakDays}</h3>
                <span className="text-sm font-semibold text-muted-foreground">Day Streak</span>
              </div>
              <p className="text-sm text-emerald-600 dark:text-emerald-400 font-medium">You're crushing it! 🚀</p>
            </div>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-secondary/50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-emerald-600">{completedDays}</p>
            <p className="text-xs text-muted-foreground mt-1">Total Days</p>
          </div>
          <div className="bg-secondary/50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-primary">84</p>
            <p className="text-xs text-muted-foreground mt-1">Last 12 Weeks</p>
          </div>
          <div className="bg-secondary/50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-amber-600">{((completedDays / 84) * 100).toFixed(0)}%</p>
            <p className="text-xs text-muted-foreground mt-1">Completion</p>
          </div>
        </div>

        {/* Heatmap Calendar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-foreground">12-Week Activity</h4>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span>Less</span>
              <div className="flex gap-1">
                <div className="w-3 h-3 rounded bg-secondary/20"></div>
                <div className="w-3 h-3 rounded bg-emerald-400/40"></div>
                <div className="w-3 h-3 rounded bg-emerald-500/60"></div>
                <div className="w-3 h-3 rounded bg-emerald-600/80"></div>
                <div className="w-3 h-3 rounded bg-emerald-700"></div>
              </div>
              <span>More</span>
            </div>
          </div>

          {/* Heatmap Grid */}
          <div className="bg-secondary/30 rounded-lg p-3">
            <div className="grid gap-1" style={{ gridTemplateColumns: 'repeat(12, minmax(0, 1fr))' }}>
              {heatmapData.map((day, i) => (
                <div
                  key={i}
                  className={cn(
                    "aspect-square rounded transition-all duration-200 cursor-pointer",
                    "hover:ring-2 hover:ring-primary/50 hover:scale-110",
                    getHeatColor(day.intensity)
                  )}
                  title={`${day.date}${day.completed ? ' - Completed' : ' - Missed'}`}
                />
              ))}
            </div>
          </div>

          {/* Legend */}
          <p className="text-xs text-muted-foreground text-center">Each square = 1 day of the last 12 weeks</p>
        </div>
      </div>
    );
  }

  if (type === "weekly") {
    const totalScore = weeklyData.filter(d => d.completed).reduce((acc, d) => acc + d.score, 0);
    const avgScore = totalScore / weeklyData.filter(d => d.completed).length;

    return (
      <div className="bg-card/80 backdrop-blur-sm border border-border rounded-xl p-4 my-3 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-foreground flex items-center gap-2">
            <Clock className="h-4 w-4 text-primary" />
            This Week's Progress
          </h3>
          <span className="text-sm font-medium text-primary">Avg: {avgScore.toFixed(0)}%</span>
        </div>

        {/* Daily Performance */}
        <div className="flex gap-2 h-24">
          {weeklyData.map((day, i) => (
            <div key={i} className="flex-1 flex flex-col items-center justify-end gap-1">
              <div 
                className={cn(
                  "w-full rounded-t-md transition-all",
                  day.completed 
                    ? day.score >= 80 ? "bg-green-500" : day.score >= 60 ? "bg-yellow-500" : "bg-red-500"
                    : "bg-secondary"
                )}
                style={{ height: day.completed ? `${day.score}%` : "10%" }}
              />
              <span className="text-xs text-muted-foreground">{day.day}</span>
              {day.completed && (
                <span className="text-xs font-medium text-foreground">{day.score}%</span>
              )}
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between text-sm pt-2 border-t border-border">
          <span className="text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 inline mr-1 text-green-500" />
            {weeklyData.filter(d => d.completed).length} days completed
          </span>
          <span className="text-muted-foreground">
            {7 - weeklyData.filter(d => d.completed).length} days remaining
          </span>
        </div>
      </div>
    );
  }

  // Achievements
  return (
    <div className="bg-card/80 backdrop-blur-sm border border-border rounded-xl p-4 my-3 space-y-3">
      <div className="flex items-center gap-2">
        <Trophy className="h-5 w-5 text-yellow-500" />
        <h3 className="font-semibold text-foreground">Recent Achievements</h3>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {recentAchievements.map((achievement, i) => (
          <div 
            key={i}
            className={cn(
              "flex items-center gap-2 p-2 rounded-lg border transition-all",
              achievement.unlocked 
                ? "bg-secondary/50 border-border" 
                : "bg-secondary/20 border-border/50 opacity-60"
            )}
          >
            <span className="text-2xl">{achievement.icon}</span>
            <div className="min-w-0">
              <p className="text-sm font-medium text-foreground truncate">{achievement.name}</p>
              {achievement.unlocked ? (
                <p className="text-xs text-muted-foreground">{achievement.date}</p>
              ) : (
                <p className="text-xs text-muted-foreground">Locked</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
