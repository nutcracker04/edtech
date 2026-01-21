import { Flame } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

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

export function StreakCard() {
  const completedDays = heatmapData.filter(d => d.completed).length;
  const streakDays = 12; // Current streak

  return (
    <Card>
      <CardHeader>
        {/* Header with Streak Info */}
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center shadow-lg">
            <Flame className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-baseline gap-2">
              <h3 className="text-2xl font-bold text-foreground">{streakDays}</h3>
              <span className="text-sm font-semibold text-muted-foreground">Day Streak</span>
            </div>
            <p className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">You're crushing it! 🚀</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-secondary/50 rounded-lg p-2.5 text-center">
            <p className="text-lg font-bold text-emerald-600">{completedDays}</p>
            <p className="text-xs text-muted-foreground mt-1">Days</p>
          </div>
          <div className="bg-secondary/50 rounded-lg p-2.5 text-center">
            <p className="text-lg font-bold text-primary">84</p>
            <p className="text-xs text-muted-foreground mt-1">Period</p>
          </div>
          <div className="bg-secondary/50 rounded-lg p-2.5 text-center">
            <p className="text-lg font-bold text-amber-600">{((completedDays / 84) * 100).toFixed(0)}%</p>
            <p className="text-xs text-muted-foreground mt-1">Rate</p>
          </div>
        </div>

        {/* Heatmap Calendar */}
        <div className="space-y-3 pt-2">
          <Separator />
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">Activity Heatmap</h4>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <span>Low</span>
            <div className="flex gap-1">
              <div className="w-2.5 h-2.5 rounded-sm bg-secondary/20"></div>
              <div className="w-2.5 h-2.5 rounded-sm bg-emerald-400/40"></div>
              <div className="w-2.5 h-2.5 rounded-sm bg-emerald-500/60"></div>
              <div className="w-2.5 h-2.5 rounded-sm bg-emerald-600/80"></div>
              <div className="w-2.5 h-2.5 rounded-sm bg-emerald-700"></div>
            </div>
            <span>High</span>
          </div>
        </div>

        {/* Heatmap Grid */}
        <div className="bg-secondary/20 rounded-lg p-3 overflow-hidden">
          <div className="grid gap-1" style={{ gridTemplateColumns: 'repeat(12, minmax(0, 1fr))' }}>
            {heatmapData.map((day, i) => (
              <div
                key={i}
                className={cn(
                  "aspect-square rounded-sm transition-all duration-200 cursor-pointer",
                  "hover:ring-2 hover:ring-primary hover:scale-125",
                  getHeatColor(day.intensity)
                )}
                title={`${day.date}${day.completed ? ' - Completed' : ' - Missed'}`}
              />
            ))}
          </div>
        </div>

        {/* Legend */}
        <p className="text-xs text-muted-foreground text-center">12 weeks of activity • Each square = 1 day</p>
        </div>
      </CardContent>
    </Card>
  );
}
