import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Trophy, Star, Zap, Target, BookOpen, Award } from "lucide-react";

interface Achievement {
    id: string;
    title: string;
    description: string;
    icon: "trophy" | "star" | "zap" | "target" | "book" | "award";
    unlocked: boolean;
    unlockedAt?: string;
    progress?: number;
    maxProgress?: number;
}

interface AchievementCardProps {
    achievement: Achievement;
    onCelebrate?: () => void;
    className?: string;
}

const iconMap = {
    trophy: Trophy,
    star: Star,
    zap: Zap,
    target: Target,
    book: BookOpen,
    award: Award,
};

export function AchievementCard({
    achievement,
    onCelebrate,
    className,
}: AchievementCardProps) {
    const [justUnlocked, setJustUnlocked] = useState(false);
    const Icon = iconMap[achievement.icon];

    useEffect(() => {
        if (achievement.unlocked) {
            setJustUnlocked(true);
            onCelebrate?.();
            const timer = setTimeout(() => setJustUnlocked(false), 2000);
            return () => clearTimeout(timer);
        }
    }, [achievement.unlocked]);

    const progressPercent = achievement.maxProgress
        ? ((achievement.progress || 0) / achievement.maxProgress) * 100
        : 0;

    return (
        <div
            className={cn(
                "relative p-4 rounded-xl border transition-all",
                achievement.unlocked
                    ? "bg-gradient-to-br from-amber-50 to-yellow-50 dark:from-amber-950/30 dark:to-yellow-950/30 border-amber-200 dark:border-amber-800"
                    : "bg-muted/30 border-border opacity-60",
                justUnlocked && "animate-bounce-success",
                className
            )}
        >
            <div className="flex items-start gap-3">
                {/* Icon */}
                <div
                    className={cn(
                        "p-2.5 rounded-lg shrink-0",
                        achievement.unlocked
                            ? "bg-gradient-to-br from-amber-400 to-yellow-500"
                            : "bg-muted"
                    )}
                >
                    <Icon
                        className={cn(
                            "h-5 w-5",
                            achievement.unlocked ? "text-white" : "text-muted-foreground"
                        )}
                    />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <h4
                        className={cn(
                            "font-semibold text-sm",
                            achievement.unlocked ? "text-foreground" : "text-muted-foreground"
                        )}
                    >
                        {achievement.title}
                    </h4>
                    <p className="text-xs text-muted-foreground mt-0.5">
                        {achievement.description}
                    </p>

                    {/* Progress Bar (for locked achievements) */}
                    {!achievement.unlocked && achievement.maxProgress && (
                        <div className="mt-2">
                            <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                                <span>Progress</span>
                                <span>
                                    {achievement.progress || 0}/{achievement.maxProgress}
                                </span>
                            </div>
                            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-primary/60 rounded-full transition-all duration-500"
                                    style={{ width: `${progressPercent}%` }}
                                />
                            </div>
                        </div>
                    )}

                    {/* Unlocked date */}
                    {achievement.unlocked && achievement.unlockedAt && (
                        <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                            Unlocked {achievement.unlockedAt}
                        </p>
                    )}
                </div>

                {/* Unlocked Badge */}
                {achievement.unlocked && (
                    <div className="absolute -top-1 -right-1">
                        <div className="bg-amber-400 rounded-full p-1">
                            <Star className="h-3 w-3 text-white fill-white" />
                        </div>
                    </div>
                )}
            </div>

            {/* Celebration effect */}
            {justUnlocked && (
                <div className="absolute inset-0 -z-10 animate-ping rounded-xl bg-amber-300/30" />
            )}
        </div>
    );
}

interface AchievementGridProps {
    achievements: Achievement[];
    className?: string;
}

export function AchievementGrid({ achievements, className }: AchievementGridProps) {
    return (
        <div className={cn("grid grid-cols-1 sm:grid-cols-2 gap-3", className)}>
            {achievements.map((achievement) => (
                <AchievementCard key={achievement.id} achievement={achievement} />
            ))}
        </div>
    );
}
