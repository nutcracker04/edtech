import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
interface AIAssistantButtonProps {
  onClick: () => void;
  isOpen: boolean;
}
export function AIAssistantButton({
  onClick,
  isOpen
}: AIAssistantButtonProps) {
  if (isOpen) return null;
  return;
}