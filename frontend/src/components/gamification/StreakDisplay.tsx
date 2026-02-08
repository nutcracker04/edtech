import { cn } from "@/lib/utils";
import { Flame, Snowflake, Trophy, Star } from "lucide-react";

interface StreakDisplayProps {
    currentStreak: number;
    longestStreak: number;
    freezeCardsAvailable?: number;
    size?: "sm" | "md" | "lg";
    showDetails?: boolean;
    className?: string;
}

export function StreakDisplay({
    currentStreak,
    longestStreak,
    freezeCardsAvailable = 0,
    size = "md",
    showDetails = true,
    className,
}: StreakDisplayProps) {
    const isOnFire = currentStreak >= 7;
    const isNewRecord = currentStreak >= longestStreak && currentStreak > 0;

    const sizeStyles = {
        sm: {
            container: "p-3 rounded-lg",
            icon: "h-6 w-6",
            number: "text-2xl",
            label: "text-xs",
        },
        md: {
            container: "p-4 rounded-xl",
            icon: "h-8 w-8",
            number: "text-3xl",
            label: "text-sm",
        },
        lg: {
            container: "p-6 rounded-2xl",
            icon: "h-12 w-12",
            number: "text-5xl",
            label: "text-base",
        },
    };

    const styles = sizeStyles[size];

    return (
        <div className={cn("relative", className)}>
            {/* Main Streak Card */}
            <div
                className={cn(
                    styles.container,
                    "bg-card border transition-all",
                    isOnFire
                        ? "border-orange-300 bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-950/30 dark:to-amber-950/30"
                        : "border-border"
                )}
            >
                <div className="flex items-center gap-4">
                    {/* Flame Icon */}
                    <div
                        className={cn(
                            "relative flex items-center justify-center rounded-full",
                            isOnFire
                                ? "bg-gradient-to-br from-orange-400 to-red-500"
                                : "bg-muted",
                            size === "sm" ? "p-2" : size === "lg" ? "p-4" : "p-3"
                        )}
                    >
                        <Flame
                            className={cn(
                                styles.icon,
                                isOnFire ? "text-white animate-pulse" : "text-muted-foreground"
                            )}
                        />
                        {isOnFire && (
                            <div className="absolute inset-0 rounded-full animate-ping bg-orange-400/30" />
                        )}
                    </div>

                    {/* Streak Number */}
                    <div className="flex-1">
                        <div className="flex items-baseline gap-2">
                            <span
                                className={cn(
                                    styles.number,
                                    "font-bold tabular-nums",
                                    isOnFire
                                        ? "bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent"
                                        : "text-foreground"
                                )}
                            >
                                {currentStreak}
                            </span>
                            <span className={cn(styles.label, "text-muted-foreground font-medium")}>
                                day streak
                            </span>
                        </div>

                        {/* New Record Badge */}
                        {isNewRecord && currentStreak > 0 && (
                            <div className="flex items-center gap-1 mt-1">
                                <Trophy className="h-3.5 w-3.5 text-yellow-500" />
                                <span className="text-xs font-medium text-yellow-600 dark:text-yellow-400">
                                    New personal best!
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Freeze Cards */}
                    {showDetails && freezeCardsAvailable > 0 && (
                        <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800">
                            <Snowflake className="h-4 w-4 text-blue-500" />
                            <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                                {freezeCardsAvailable}
                            </span>
                        </div>
                    )}
                </div>

                {/* Stats Row */}
                {showDetails && (
                    <div className="flex items-center gap-4 mt-3 pt-3 border-t border-border/50">
                        <div className="flex items-center gap-1.5">
                            <Star className="h-4 w-4 text-amber-500" />
                            <span className={cn(styles.label, "text-muted-foreground")}>
                                Best: <span className="font-semibold text-foreground">{longestStreak}</span> days
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {/* Celebration particles for milestones */}
            {isOnFire && currentStreak % 7 === 0 && currentStreak > 0 && (
                <div className="absolute -top-2 -right-2 animate-bounce">
                    <span className="text-2xl">🔥</span>
                </div>
            )}
        </div>
    );
}
