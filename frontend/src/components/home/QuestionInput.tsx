import { useState, useRef, useEffect } from "react";
import { Mic, Send, BookOpen, Calculator, FlaskConical, Atom, Image, Plus, BarChart3, Target, TrendingUp, Flame, Trophy } from "lucide-react";
import { cn } from "@/lib/utils";
import { useChat } from "@/hooks/useChat";
import { ChatMessage } from "./ChatMessage";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";

const quickActions = [
  { icon: Calculator, label: "Mathematics", subject: "math" },
  { icon: Atom, label: "Physics", subject: "physics" },
  { icon: FlaskConical, label: "Chemistry", subject: "chemistry" },
  { icon: BookOpen, label: "Full Test", subject: "full" },
];

const suggestedPrompts = [
  "Break down projectile motion like I'm seeing it for the first time",
  "Show me the trick to solve integration problems faster",
  "Explain why I keep getting organic reactions wrong",
  "Generate 5 challenging JEE-level problems on thermodynamics",
  "Help me master coordinate geometry step-by-step",
  "What's the fastest way to solve quadratic equations?",
  "Help me understand resonance structures intuitively",
  "Generate a practice test on my weak topics",
  "Explain Gauss's law with real-world examples",
  "Show me common mistakes in calculus problems",
  "Create a formula cheat sheet for waves",
];

const chatQuickActions = [
  {
    id: "analytics",
    icon: BarChart3,
    label: "Analytics",
    prompt: "Show me my performance analytics with detailed stats and progress across all subjects",
    color: "text-blue-500",
  },
  {
    id: "progress",
    icon: TrendingUp,
    label: "Progress",
    prompt: "Show my weekly progress report with daily performance breakdown",
    color: "text-green-500",
  },
  {
    id: "streak",
    icon: Flame,
    label: "Streak",
    prompt: "Show my current study streak and consistency calendar",
    color: "text-orange-500",
  },
  {
    id: "weaknesses",
    icon: Target,
    label: "Weak Areas",
    prompt: "Analyze my weak areas and suggest topics I need to focus on for improvement",
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

export function QuestionInput() {
  const [input, setInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const { messages, isLoading, sendMessage, clearMessages, hasMessages } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [isPaused, setIsPaused] = useState(false);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  // Auto-scroll suggestions
  useEffect(() => {
    if (hasMessages || !scrollContainerRef.current) return;

    const container = scrollContainerRef.current;
    let animationFrameId: number;
    const scrollSpeed = 0.5; // pixels per frame

    const scroll = () => {
      if (hasMessages) return;

      if (!isPaused) {
        const currentScroll = container.scrollLeft;
        const maxScroll = container.scrollWidth / 2; // Half because we duplicate items

        if (currentScroll >= maxScroll - 1) {
          // Reset to start seamlessly without visible jump
          container.scrollLeft = 0;
        } else {
          // Continue scrolling forward
          container.scrollLeft = currentScroll + scrollSpeed;
        }
      }

      animationFrameId = requestAnimationFrame(scroll);
    };

    animationFrameId = requestAnimationFrame(scroll);

    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [hasMessages, isPaused]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      sendMessage(input.trim());
      setInput("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleQuickAction = (subject: string) => {
    const prompts: Record<string, string> = {
      math: "I want to practice Mathematics. Give me a challenging problem to solve.",
      physics: "I want to practice Physics. Start with a concept explanation and then give me a problem.",
      chemistry: "I want to practice Chemistry. Help me understand a key concept and test my knowledge.",
      full: "Create a mini test with 3 questions from Physics, Chemistry, and Mathematics each.",
    };
    sendMessage(prompts[subject] || `Help me with ${subject}`);
  };

  const handleSuggestedPrompt = (prompt: string) => {
    sendMessage(prompt);
  };

  const handleNewChat = () => {
    clearMessages();
  };

  const handleChatQuickAction = (prompt: string) => {
    sendMessage(prompt);
  };

  return (
    <div className={cn(
      "w-full max-w-4xl mx-auto flex flex-col",
      hasMessages ? "h-[calc(100vh-80px)]" : "h-[calc(100vh-120px)] justify-center"
    )}>
      {/* Header with New Chat button - only show when in conversation */}
      {hasMessages && (
        <div className="flex justify-end mb-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleNewChat}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>
      )}

      {/* Initial State - Logo and Prompt */}
      {!hasMessages && (
        <div className="text-center mb-8 sm:mb-12">
          <h1 className="text-5xl sm:text-6xl font-light text-foreground tracking-tight">
            Catalyst
          </h1>
        </div>
      )}

      {/* Messages Area */}
      {hasMessages && (
        <ScrollArea className="flex-1 pr-4 mb-4">
          <div className="space-y-6 pb-4">
            {messages.map((message, index) => (
              <ChatMessage
                key={message.id}
                role={message.role}
                content={message.content}
                isStreaming={isLoading && index === messages.length - 1 && message.role === "assistant"}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      )}

      {/* Input Area - Fixed at bottom when in conversation */}
      <div className={cn(
        "w-full",
        hasMessages && "mt-auto pt-4"
      )}>
        {/* Quick Action Buttons - Show when in conversation */}
        {hasMessages && (
          <div className="flex gap-2 overflow-x-auto scrollbar-hide pb-2 px-1">
            {chatQuickActions.map((action) => (
              <Button
                key={action.id}
                variant="outline"
                size="sm"
                disabled={isLoading}
                onClick={() => handleChatQuickAction(action.prompt)}
                className={cn(
                  "shrink-0 gap-1.5 rounded-full border-border/50 hover:border-border",
                  "bg-card/50 backdrop-blur-sm text-xs"
                )}
              >
                <action.icon className={cn("h-3.5 w-3.5", action.color)} />
                <span className="text-foreground">{action.label}</span>
              </Button>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="relative">
          <div className="bg-card/40 backdrop-blur-sm border border-border/50 rounded-3xl overflow-hidden shadow-2xl hover:border-border/70 transition-all duration-300">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasMessages ? "Ask a follow-up question..." : "Ask a question or describe a topic..."}
              disabled={isLoading}
              className={cn(
                "w-full bg-transparent text-foreground placeholder:text-muted-foreground/60 p-5 pb-16 resize-none focus:outline-none text-base font-light",
                hasMessages ? "min-h-[60px]" : "min-h-[110px]"
              )}
              rows={hasMessages ? 1 : 2}
            />

            {/* Bottom Bar */}
            <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-5 py-4 border-t border-border/30">
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  className="p-2 rounded-full bg-secondary/40 text-secondary-foreground hover:bg-secondary/60 transition-all duration-200"
                  title="Attach image"
                >
                  <Image className="h-4 w-4" />
                </button>

                {/* Quick Feature Actions in Bottom Bar */}
                {!hasMessages && (
                  <div className="flex items-center gap-1.5 ml-1 border-l border-border/30 pl-3">
                    {chatQuickActions.slice(0, 4).map((action) => (
                      <button
                        key={action.id}
                        type="button"
                        onClick={() => handleChatQuickAction(action.prompt)}
                        disabled={isLoading}
                        className={cn(
                          "p-1.5 rounded-full transition-all duration-200",
                          "hover:bg-secondary/40",
                          action.color
                        )}
                        title={action.label}
                      >
                        <action.icon className="h-3.5 w-3.5" />
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={() => setIsRecording(!isRecording)}
                  disabled={isLoading}
                  className={cn(
                    "p-2 rounded-full transition-all duration-200",
                    isRecording
                      ? "bg-primary text-primary-foreground animate-pulse"
                      : "bg-secondary/40 text-secondary-foreground hover:bg-secondary/60"
                  )}
                  title="Voice input"
                >
                  <Mic className="h-4 w-4" />
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className={cn(
                    "p-2.5 rounded-full transition-all duration-200 font-medium",
                    input.trim() && !isLoading
                      ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg hover:shadow-xl"
                      : "bg-secondary/30 text-secondary-foreground/50 cursor-not-allowed"
                  )}
                  title="Send message"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </form>

        {/* Suggested Prompts - Only show in initial state */}
        {!hasMessages && (
          <div className="mt-4 sm:mt-6">
            <div className="relative">
              {/* Gradient fade on the right */}
              <div className="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-background to-transparent pointer-events-none z-10" />
              {/* Gradient fade on the left */}
              <div className="absolute left-0 top-0 bottom-0 w-20 bg-gradient-to-r from-background to-transparent pointer-events-none z-10" />

              <div
                ref={scrollContainerRef}
                onMouseEnter={() => setIsPaused(true)}
                onMouseLeave={() => setIsPaused(false)}
                className="flex items-center gap-2 sm:gap-3 overflow-x-auto scrollbar-hide px-4 sm:px-8 py-2 scroll-smooth"
              >
                {/* Duplicate suggestions for seamless loop */}
                {[...suggestedPrompts, ...suggestedPrompts].map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedPrompt(prompt)}
                    className={cn(
                      "px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium transition-all duration-200",
                      "bg-card/50 backdrop-blur-sm border border-border/50 rounded-full",
                      "text-muted-foreground hover:text-foreground hover:bg-card/80 hover:border-border",
                      "hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]",
                      "whitespace-nowrap flex-shrink-0"
                    )}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
