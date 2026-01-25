import { CheckCircle, XCircle, Clock, BookOpen, FileText, Target } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";

interface Activity {
  id: string;
  type: "test" | "practice";
  title: string;
  subject: string;
  score?: number;
  time: string;
  status: "completed" | "in_progress" | "failed";
}

const recentActivities: Activity[] = [
  {
    id: "1",
    type: "test",
    title: "Mechanics Full Test",
    subject: "Physics",
    score: 85,
    time: "2 hours ago",
    status: "completed",
  },
  {
    id: "2",
    type: "practice",
    title: "Organic Chemistry - Alcohols",
    subject: "Chemistry",
    score: 72,
    time: "Yesterday",
    status: "completed",
  },
  {
    id: "4",
    type: "test",
    title: "Thermodynamics Quiz",
    subject: "Physics",
    score: 45,
    time: "2 days ago",
    status: "failed",
  },
];

export function RecentActivity() {
  const getStatusIcon = (status: Activity["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "in_progress":
        return <Clock className="h-4 w-4 text-primary" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const getTypeIcon = (type: Activity["type"]) => {
    switch (type) {
      case "test":
        return <FileText className="h-4 w-4" />;
      case "practice":
        return <Target className="h-4 w-4" />;
    }
  };

  const getTypeColor = (type: Activity["type"]) => {
    switch (type) {
      case "test":
        return "bg-blue-500/10 text-blue-500 border-blue-500/20";
      case "practice":
        return "bg-purple-500/10 text-purple-500 border-purple-500/20";
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Recent Activity</CardTitle>
          <Button variant="ghost" size="sm" className="text-primary">
            View all
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {recentActivities.map((activity, index) => (
            <div
              key={activity.id}
              className="flex items-start gap-4 p-4 hover:bg-secondary/30 transition-colors cursor-pointer group"
            >
              <Avatar className={cn("h-10 w-10 shrink-0 border", getTypeColor(activity.type))}>
                <AvatarFallback className={cn("bg-transparent", getTypeColor(activity.type))}>
                  {getTypeIcon(activity.type)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-foreground truncate group-hover:text-primary transition-colors">
                        {activity.title}
                      </h4>
                      {getStatusIcon(activity.status)}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Badge variant="outline" className="text-xs px-2 py-0 h-5">
                        {activity.subject}
                      </Badge>
                      <Separator orientation="vertical" className="h-3" />
                      <span className="text-xs">{activity.time}</span>
                    </div>
                  </div>
                  {activity.score !== undefined && (
                    <Badge
                      variant="outline"
                      className={cn(
                        "shrink-0 font-semibold",
                        activity.score >= 70
                          ? "bg-green-500/20 text-green-400 border-green-500/20"
                          : activity.score >= 50
                            ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/20"
                            : "bg-red-500/20 text-red-400 border-red-500/20"
                      )}
                    >
                      {activity.score}%
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
