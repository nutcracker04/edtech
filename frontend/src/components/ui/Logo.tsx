import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function Logo({ className, size = "md" }: LogoProps) {
  const sizeClasses = {
    sm: "h-6 w-6",
    md: "h-8 w-8",
    lg: "h-12 w-12",
  };

  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn(sizeClasses[size], className)}
    >
      <defs>
        <linearGradient id="catalystGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="hsl(var(--primary))" />
          <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0.88" />
        </linearGradient>
      </defs>
      
      {/* Modern rounded square container */}
      <rect
        x="5"
        y="5"
        width="54"
        height="54"
        rx="12"
        fill="url(#catalystGradient)"
      />
      
      {/* Stylized "C" for Catalyst - open at top, representing openness to learning */}
      <path
        d="M22 32 Q22 22 32 22 Q42 22 42 32"
        stroke="hsl(var(--primary-foreground))"
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
        opacity="0.98"
      />
      
      {/* Upward arrow breaking through - representing catalyst acceleration */}
      <path
        d="M32 38 L32 18 M28 22 L32 18 L36 22"
        stroke="hsl(var(--primary-foreground))"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
        opacity="0.98"
      />
      
      {/* Energy particles - representing transformation */}
      <circle cx="26" cy="26" r="1.8" fill="hsl(var(--primary-foreground))" opacity="0.85" />
      <circle cx="38" cy="26" r="1.8" fill="hsl(var(--primary-foreground))" opacity="0.85" />
      <circle cx="32" cy="42" r="1.5" fill="hsl(var(--primary-foreground))" opacity="0.7" />
    </svg>
  );
}
