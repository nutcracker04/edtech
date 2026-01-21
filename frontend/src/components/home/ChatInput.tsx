import { useState } from "react";
import { Mic, Send, Paperclip, Image } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
  isCompact?: boolean;
}

export function ChatInput({ onSend, isLoading, placeholder = "Ask a new question...", isCompact }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSend(input.trim());
      setInput("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className={cn(
        "bg-card border border-border rounded-xl overflow-hidden shadow-lg",
        isCompact && "rounded-2xl"
      )}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading}
          className={cn(
            "w-full bg-transparent text-foreground placeholder:text-muted-foreground p-4 resize-none focus:outline-none text-base",
            isCompact ? "min-h-[60px] pb-12" : "min-h-[100px] pb-14"
          )}
          rows={isCompact ? 1 : 2}
        />
        
        {/* Bottom Bar */}
        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <select 
              className="bg-secondary text-secondary-foreground text-sm px-3 py-1.5 rounded-lg border-none focus:outline-none cursor-pointer"
              disabled={isLoading}
            >
              <option value="jee-main">JEE Main</option>
              <option value="jee-advanced">JEE Advanced</option>
              <option value="neet">NEET</option>
            </select>
            <button
              type="button"
              className="p-2 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
            >
              <Image className="h-4 w-4" />
            </button>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsRecording(!isRecording)}
              disabled={isLoading}
              className={cn(
                "p-2 rounded-full transition-all duration-200",
                isRecording
                  ? "bg-primary text-primary-foreground animate-pulse"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              )}
            >
              <Mic className="h-5 w-5" />
            </button>
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className={cn(
                "p-2 rounded-full transition-colors",
                input.trim() && !isLoading
                  ? "bg-primary text-primary-foreground hover:bg-primary/90"
                  : "bg-secondary text-secondary-foreground opacity-50"
              )}
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}
