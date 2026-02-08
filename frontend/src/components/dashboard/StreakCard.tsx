import { Flame } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  switch (intensity) {
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
    <Card className="flex flex-col h-[400px]">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Flame className="h-5 w-5 text-orange-500" />
          Statistics
        </CardTitle>
        <p className="text-sm text-muted-foreground">Activity Summary</p>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col gap-4">
        {/* Header with Streak Info */}
        <div className="flex items-center gap-4 bg-secondary/20 p-3 rounded-lg">
          <div className="relative h-10 w-10 rounded-lg bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center shadow-lg hover:scale-110 transition-transform cursor-pointer shrink-0">
            <Flame className="h-5 w-5 text-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-baseline gap-2">
              <h3 className="text-2xl font-bold bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">{streakDays}</h3>
              <span className="text-sm font-semibold text-muted-foreground">Day Streak</span>
            </div>
            <p className="text-xs text-green-600 font-medium tracking-wide">Keep it up! 🔥</p>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <p className="text-lg font-bold text-foreground">{completedDays}</p>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Days</p>
          </div>
          <div>
            <p className="text-lg font-bold text-foreground">84</p>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Total</p>
          </div>
          <div>
            <p className="text-lg font-bold text-foreground">{((completedDays / 84) * 100).toFixed(0)}%</p>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Rate</p>
          </div>
        </div>

        {/* Heatmap Grid */}
        <div className="flex-1 bg-secondary/10 rounded-lg p-3 flex flex-col justify-center">
          <div className="flex items-center justify-between mb-2 px-1">
            <span className="text-[10px] font-semibold text-muted-foreground uppercase">Activity</span>
            <div className="flex gap-0.5">
              {[0, 2, 4].map(i => (
                <div key={i} className={cn("w-2 h-2 rounded-[1px]", getHeatColor(i))} />
              ))}
            </div>
          </div>
          <div className="grid gap-1.5" style={{ gridTemplateColumns: 'repeat(12, minmax(0, 1fr))' }}>
            {heatmapData.map((day, i) => (
              <div
                key={i}
                className={cn(
                  "aspect-square rounded-[2px] transition-all hover:ring-1 hover:ring-primary",
                  getHeatColor(day.intensity)
                )}
                title={`${day.date}${day.completed ? ' - Completed' : ' - Missed'}`}
              />
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
