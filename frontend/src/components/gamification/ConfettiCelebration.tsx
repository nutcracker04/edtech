import { useEffect, useState, useCallback } from "react";
import { cn } from "@/lib/utils";

interface Particle {
    id: number;
    x: number;
    y: number;
    color: string;
    size: number;
    rotation: number;
    velocity: { x: number; y: number };
}

interface ConfettiCelebrationProps {
    active: boolean;
    duration?: number;
    onComplete?: () => void;
    className?: string;
}

const COLORS = [
    "#FF6B6B", // Coral
    "#4ECDC4", // Teal
    "#FFE66D", // Yellow
    "#95E1D3", // Mint
    "#DDA0DD", // Plum
    "#87CEEB", // Sky Blue
    "#FFB6C1", // Light Pink
    "#98D8C8", // Sea Green
];

export function ConfettiCelebration({
    active,
    duration = 3000,
    onComplete,
    className,
}: ConfettiCelebrationProps) {
    const [particles, setParticles] = useState<Particle[]>([]);
    const [isVisible, setIsVisible] = useState(false);

    const createParticles = useCallback(() => {
        const newParticles: Particle[] = [];
        const count = 50;

        for (let i = 0; i < count; i++) {
            newParticles.push({
                id: i,
                x: Math.random() * 100,
                y: -10 - Math.random() * 20,
                color: COLORS[Math.floor(Math.random() * COLORS.length)],
                size: 6 + Math.random() * 8,
                rotation: Math.random() * 360,
                velocity: {
                    x: (Math.random() - 0.5) * 4,
                    y: 2 + Math.random() * 4,
                },
            });
        }

        return newParticles;
    }, []);

    useEffect(() => {
        if (active) {
            setIsVisible(true);
            setParticles(createParticles());

            const timer = setTimeout(() => {
                setIsVisible(false);
                setParticles([]);
                onComplete?.();
            }, duration);

            return () => clearTimeout(timer);
        }
    }, [active, duration, onComplete, createParticles]);

    if (!isVisible) return null;

    return (
        <div
            className={cn(
                "fixed inset-0 pointer-events-none z-50 overflow-hidden",
                className
            )}
        >
            {particles.map((particle) => (
                <div
                    key={particle.id}
                    className="absolute animate-confetti"
                    style={{
                        left: `${particle.x}%`,
                        top: `${particle.y}%`,
                        width: particle.size,
                        height: particle.size,
                        backgroundColor: particle.color,
                        transform: `rotate(${particle.rotation}deg)`,
                        borderRadius: Math.random() > 0.5 ? "50%" : "2px",
                        animationDelay: `${Math.random() * 0.5}s`,
                        animationDuration: `${2 + Math.random()}s`,
                    }}
                />
            ))}
        </div>
    );
}

// CSS for confetti animation - add to index.css:
// @keyframes confetti-fall {
//   0% { transform: translateY(0) rotate(0deg); opacity: 1; }
//   100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
// }
// .animate-confetti { animation: confetti-fall 3s ease-out forwards; }
