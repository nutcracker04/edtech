import { BarChart3, BookMarked, Target, TrendingUp, Flame, Trophy, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface QuickActionsProps {
  onAction: (action: string) => void;
  isLoading: boolean;
  variant?: "horizontal" | "vertical";
}

const actions = [
  {
    id: "analytics",
    icon: BarChart3,
    label: "My Analytics",
    prompt: "Show me my performance analytics with detailed stats and progress across all subjects",
    color: "text-blue-500",
  },
  {
    id: "progress",
    icon: TrendingUp,
    label: "Weekly Progress",
    prompt: "Show my weekly progress report with daily performance breakdown",
    color: "text-green-500",
  },
  {
    id: "streak",
    icon: Flame,
    label: "Study Streak",
    prompt: "Show my current study streak and consistency calendar",
    color: "text-orange-500",
  },
  {
    id: "revision",
    icon: BookMarked,
    label: "Revision Capsule",
    prompt: "Create a personalized revision capsule based on my weak topics",
    color: "text-purple-500",
  },
  {
    id: "weaknesses",
    icon: Target,
    label: "Weak Areas",
    prompt: "Analyze my weak areas and suggest topics I need to focus on",
    color: "text-red-500",
  },
  {
    id: "achievements",
    icon: Trophy,
    label: "Achievements",
    prompt: "Show my achievements and milestones",
    color: "text-yellow-500",
  },
];

export function QuickActions({ onAction, isLoading, variant = "horizontal" }: QuickActionsProps) {
  return (
    <div className={cn(
      "flex gap-2 py-2",
      variant === "horizontal" 
        ? "overflow-x-auto scrollbar-hide px-1" 
        : "flex-wrap justify-center"
    )}>
      {actions.map((action) => (
        <Button
          key={action.id}
          variant="outline"
          size="sm"
          disabled={isLoading}
          onClick={() => onAction(action.prompt)}
          className={cn(
            "shrink-0 gap-2 rounded-full border-border/50 hover:border-border",
            "bg-card/50 backdrop-blur-sm"
          )}
        >
          <action.icon className={cn("h-4 w-4", action.color)} />
          <span className="text-foreground">{action.label}</span>
        </Button>
      ))}
    </div>
  );
}
