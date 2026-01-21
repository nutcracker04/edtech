import { TrendingUp, TrendingDown, Target, BookOpen, Clock, Flame } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface SubjectStat {
  name: string;
  score: number;
  change: number;
  topics: { name: string; mastery: number }[];
}

interface AnalyticsWidgetProps {
  type: "overview" | "subject";
  subject?: string;
  data?: SubjectStat;
}

const mockOverviewData = {
  streak: 12,
  questionsToday: 45,
  accuracy: 78,
  improvement: 5.2,
  subjects: [
    { name: "Physics", score: 82, change: 3.2 },
    { name: "Chemistry", score: 75, change: -1.5 },
    { name: "Mathematics", score: 88, change: 4.1 },
  ],
};

const mockSubjectData: Record<string, SubjectStat> = {
  physics: {
    name: "Physics",
    score: 82,
    change: 3.2,
    topics: [
      { name: "Mechanics", mastery: 85 },
      { name: "Electromagnetism", mastery: 78 },
      { name: "Thermodynamics", mastery: 72 },
      { name: "Optics", mastery: 88 },
      { name: "Modern Physics", mastery: 65 },
    ],
  },
  chemistry: {
    name: "Chemistry",
    score: 75,
    change: -1.5,
    topics: [
      { name: "Organic Chemistry", mastery: 70 },
      { name: "Inorganic Chemistry", mastery: 78 },
      { name: "Physical Chemistry", mastery: 75 },
      { name: "Coordination Compounds", mastery: 68 },
    ],
  },
  mathematics: {
    name: "Mathematics",
    score: 88,
    change: 4.1,
    topics: [
      { name: "Calculus", mastery: 92 },
      { name: "Algebra", mastery: 85 },
      { name: "Trigonometry", mastery: 88 },
      { name: "Coordinate Geometry", mastery: 82 },
      { name: "Probability", mastery: 78 },
    ],
  },
};

export function AnalyticsWidget({ type, subject }: AnalyticsWidgetProps) {
  const getMasteryColor = (value: number) => {
    if (value >= 80) return "bg-green-500";
    if (value >= 60) return "bg-yellow-500";
    return "bg-red-500";
  };

  if (type === "overview") {
    return (
      <div className="bg-card/80 backdrop-blur-sm border border-border rounded-xl p-4 my-3 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-foreground flex items-center gap-2">
            <Target className="h-4 w-4 text-primary" />
            Your Performance Overview
          </h3>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-3">
          <div className="bg-secondary/50 rounded-lg p-3 text-center">
            <Flame className="h-5 w-5 mx-auto text-orange-500 mb-1" />
            <div className="text-xl font-bold text-foreground">{mockOverviewData.streak}</div>
            <div className="text-xs text-muted-foreground">Day Streak</div>
          </div>
          <div className="bg-secondary/50 rounded-lg p-3 text-center">
            <BookOpen className="h-5 w-5 mx-auto text-blue-500 mb-1" />
            <div className="text-xl font-bold text-foreground">{mockOverviewData.questionsToday}</div>
            <div className="text-xs text-muted-foreground">Today</div>
          </div>
          <div className="bg-secondary/50 rounded-lg p-3 text-center">
            <Target className="h-5 w-5 mx-auto text-green-500 mb-1" />
            <div className="text-xl font-bold text-foreground">{mockOverviewData.accuracy}%</div>
            <div className="text-xs text-muted-foreground">Accuracy</div>
          </div>
          <div className="bg-secondary/50 rounded-lg p-3 text-center">
            <TrendingUp className="h-5 w-5 mx-auto text-primary mb-1" />
            <div className="text-xl font-bold text-foreground">+{mockOverviewData.improvement}%</div>
            <div className="text-xs text-muted-foreground">This Week</div>
          </div>
        </div>

        {/* Subject Scores */}
        <div className="space-y-2">
          {mockOverviewData.subjects.map((subj) => (
            <div key={subj.name} className="flex items-center gap-3">
              <span className="text-sm text-foreground w-24">{subj.name}</span>
              <div className="flex-1">
                <Progress value={subj.score} className="h-2" />
              </div>
              <span className="text-sm font-medium text-foreground w-10">{subj.score}%</span>
              <span className={cn(
                "text-xs flex items-center gap-0.5",
                subj.change >= 0 ? "text-green-500" : "text-red-500"
              )}>
                {subj.change >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                {Math.abs(subj.change)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Subject-specific analytics
  const subjectData = mockSubjectData[subject?.toLowerCase() || "physics"];
  
  return (
    <div className="bg-card/80 backdrop-blur-sm border border-border rounded-xl p-4 my-3 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-foreground flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-primary" />
          {subjectData.name} Analysis
        </h3>
        <span className={cn(
          "text-sm flex items-center gap-1 px-2 py-0.5 rounded-full",
          subjectData.change >= 0 ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"
        )}>
          {subjectData.change >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
          {Math.abs(subjectData.change)}% this week
        </span>
      </div>

      {/* Overall Score */}
      <div className="flex items-center gap-4">
        <div className="relative h-20 w-20">
          <svg className="h-20 w-20 -rotate-90">
            <circle
              cx="40"
              cy="40"
              r="36"
              stroke="currentColor"
              strokeWidth="8"
              fill="transparent"
              className="text-secondary"
            />
            <circle
              cx="40"
              cy="40"
              r="36"
              stroke="currentColor"
              strokeWidth="8"
              fill="transparent"
              strokeDasharray={`${(subjectData.score / 100) * 226} 226`}
              className="text-primary"
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-lg font-bold text-foreground">
            {subjectData.score}%
          </span>
        </div>
        <div className="flex-1 space-y-1">
          <p className="text-sm text-muted-foreground">Overall Mastery</p>
          <p className="text-xs text-muted-foreground">
            {subjectData.score >= 80 ? "Excellent! Keep it up!" : 
             subjectData.score >= 60 ? "Good progress, focus on weak areas" : 
             "Needs more practice"}
          </p>
        </div>
      </div>

      {/* Topic Breakdown */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-foreground">Topic Mastery</h4>
        {subjectData.topics.map((topic) => (
          <div key={topic.name} className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-36 truncate">{topic.name}</span>
            <div className="flex-1 bg-secondary rounded-full h-2 overflow-hidden">
              <div 
                className={cn("h-full rounded-full transition-all", getMasteryColor(topic.mastery))}
                style={{ width: `${topic.mastery}%` }}
              />
            </div>
            <span className="text-xs font-medium text-foreground w-8">{topic.mastery}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
