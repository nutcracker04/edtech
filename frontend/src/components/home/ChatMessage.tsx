import { cn } from "@/lib/utils";
import { Copy, ThumbsUp, ThumbsDown, Share2, Download, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AnalyticsWidget } from "@/components/chat/AnalyticsWidget";
import { ProgressWidget } from "@/components/chat/ProgressWidget";
import { RevisionCapsuleWidget } from "@/components/chat/RevisionCapsuleWidget";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

// Detect widget triggers from AI response
function parseWidgets(content: string) {
  const widgets: Array<{ type: string; props: Record<string, string> }> = [];
  
  // Analytics widget triggers
  if (content.toLowerCase().includes("[analytics]") || 
      content.toLowerCase().includes("performance analytics") ||
      content.toLowerCase().includes("performance overview")) {
    widgets.push({ type: "analytics-overview", props: {} });
  }
  
  // Subject-specific analytics
  const subjectMatch = content.match(/\[analytics:(physics|chemistry|mathematics)\]/i);
  if (subjectMatch) {
    widgets.push({ type: "analytics-subject", props: { subject: subjectMatch[1] } });
  }
  
  // Progress widgets
  if (content.toLowerCase().includes("[streak]") || 
      content.toLowerCase().includes("study streak") ||
      content.toLowerCase().includes("day streak")) {
    widgets.push({ type: "progress-streak", props: {} });
  }
  
  if (content.toLowerCase().includes("[weekly]") || 
      content.toLowerCase().includes("weekly progress") ||
      content.toLowerCase().includes("this week")) {
    widgets.push({ type: "progress-weekly", props: {} });
  }
  
  if (content.toLowerCase().includes("[achievements]") || 
      content.toLowerCase().includes("achievements") ||
      content.toLowerCase().includes("milestones")) {
    widgets.push({ type: "progress-achievements", props: {} });
  }
  
  // Revision capsule triggers
  const revisionMatch = content.match(/\[revision(?::(physics|chemistry|mathematics))?\]/i);
  if (revisionMatch || content.toLowerCase().includes("revision capsule")) {
    const subject = revisionMatch?.[1] || "physics";
    widgets.push({ type: "revision-capsule", props: { subject } });
  }
  
  // Weak areas trigger
  if (content.toLowerCase().includes("weak areas") || 
      content.toLowerCase().includes("focus on") ||
      content.toLowerCase().includes("need to improve")) {
    if (!widgets.some(w => w.type.includes("analytics"))) {
      widgets.push({ type: "analytics-overview", props: {} });
    }
  }
  
  return widgets;
}

// Clean widget markers from content
function cleanContent(content: string) {
  return content
    .replace(/\[(analytics|streak|weekly|achievements|revision)(?::[a-z]+)?\]/gi, "")
    .trim();
}

export function ChatMessage({ role, content, isStreaming }: ChatMessageProps) {
  const widgets = role === "assistant" ? parseWidgets(content) : [];
  const cleanedContent = role === "assistant" ? cleanContent(content) : content;

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
  };

  const renderWidget = (widget: { type: string; props: Record<string, string> }, index: number) => {
    switch (widget.type) {
      case "analytics-overview":
        return <AnalyticsWidget key={index} type="overview" />;
      case "analytics-subject":
        return <AnalyticsWidget key={index} type="subject" subject={widget.props.subject} />;
      case "progress-streak":
        return <ProgressWidget key={index} type="streak" />;
      case "progress-weekly":
        return <ProgressWidget key={index} type="weekly" />;
      case "progress-achievements":
        return <ProgressWidget key={index} type="achievements" />;
      case "revision-capsule":
        return <RevisionCapsuleWidget key={index} subject={widget.props.subject} />;
      default:
        return null;
    }
  };

  return (
    <div
      className={cn(
        "flex w-full",
        role === "user" ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "rounded-2xl",
          role === "user"
            ? "max-w-[85%] bg-secondary text-foreground px-4 py-3"
            : "w-full text-foreground"
        )}
      >
        {/* Text Content */}
        {cleanedContent && (
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {cleanedContent}
            {isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse rounded-sm" />
            )}
          </div>
        )}
        
        {/* Render Interactive Widgets */}
        {role === "assistant" && !isStreaming && widgets.length > 0 && (
          <div className="mt-2">
            {widgets.map((widget, index) => renderWidget(widget, index))}
          </div>
        )}
        
        {role === "assistant" && !isStreaming && cleanedContent && (
          <div className="flex items-center gap-1 mt-3 pt-2 border-t border-border/30">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
              onClick={handleCopy}
            >
              <Copy className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
            >
              <ThumbsUp className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
            >
              <ThumbsDown className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
            >
              <Share2 className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
            >
              <Download className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
