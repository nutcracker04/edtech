import { useState, useRef, useEffect } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ChevronUp, Lightbulb, CheckCircle, XCircle, ArrowUp } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

interface Capsule {
    id: string;
    topic: string;
    question: string;
    options: string[];
    correctAnswer: number; // Index of correct option
    explanation: string;
    difficulty: 'Easy' | 'Medium' | 'Hard';
}

const MOCK_CAPSULES: Capsule[] = [
    {
        id: '1',
        topic: 'Alternating Current',
        question: 'In an L-C-R series AC circuit, the voltage across each of the components L, C and R is 50V. The voltage across the L-C combination will be:',
        options: ['50V', '50√2V', '100V', '0V'],
        correctAnswer: 3,
        explanation: 'In a series LCR circuit, the voltage across the inductor (VL) and the capacitor (VC) are 180 degrees out of phase. Since VL = VC = 50V, the net voltage across the L-C combination is VL - VC = 50 - 50 = 0V.',
        difficulty: 'Medium'
    },
    {
        id: '2',
        topic: 'Semiconductors',
        question: 'At absolute zero temperature, a semiconductor behaves as:',
        options: ['A perfect conductor', 'A perfect insulator', 'A semiconductor', 'A superconductor'],
        correctAnswer: 1,
        explanation: 'At absolute zero (0K), all electrons in the valence band of a semiconductor are tightly bound to the nucleus, and the conduction band is empty. Thus, no free charge carriers are available for conduction, making it a perfect insulator.',
        difficulty: 'Easy'
    },
    {
        id: '3',
        topic: 'Ray Optics',
        question: 'The critical angle for light going from medium X into medium Y is θ. The speed of light in medium X is v. The speed of light in medium Y is:',
        options: ['v(1 - cosθ)', 'v/sinθ', 'v/cosθ', 'v sinθ'],
        correctAnswer: 1,
        explanation: 'Critical angle θ is given by sinθ = n2/n1 = v1/v2. Here, medium X is the denser medium (v1 = v) and Y is rarer (speed v2). So, sinθ = v/v2 => v2 = v/sinθ.',
        difficulty: 'Hard'
    },
    {
        id: '4',
        topic: 'Wave Optics',
        question: 'In Young\'s double slit experiment, if the slit width is doubled, the intensity of the central maximum becomes:',
        options: ['Double', 'Four times', 'Half', 'Remains same'],
        correctAnswer: 1,
        explanation: 'Intensity is directly proportional to the square of the amplitude (width). If slit width is doubled, amplitude doubles. Intensity I ∝ A². So, (2A)² = 4A². Intensity becomes four times.',
        difficulty: 'Medium'
    }
];

export const RevisionCapsules = () => {
    const [activeIndex, setActiveIndex] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);

    const handleScroll = () => {
        if (containerRef.current) {
            const container = containerRef.current;
            const containerRect = container.getBoundingClientRect();
            const containerCenter = containerRect.top + containerRect.height / 2;

            let closestIndex = 0;
            let minDistance = Number.MAX_VALUE;

            Array.from(container.children).forEach((child, index) => {
                const rect = child.getBoundingClientRect();
                const childCenter = rect.top + rect.height / 2;
                const distance = Math.abs(containerCenter - childCenter);

                if (distance < minDistance) {
                    minDistance = distance;
                    closestIndex = index;
                }
            });

            if (closestIndex !== activeIndex) {
                setActiveIndex(closestIndex);
            }
        }
    };

    return (
        <div className="flex flex-col h-full w-full">
            {/* Header removed as requested */}

            <div
                ref={containerRef}
                onScroll={handleScroll}
                className="flex-1 w-full mx-auto overflow-y-scroll rounded-xl bg-black/5 dark:bg-white/5 scroll-smooth shadow-inner border border-border/50 pb-20"
                style={{
                    maxHeight: '100%',
                    scrollbarWidth: 'thin',
                    scrollbarColor: 'hsl(var(--primary) / 0.3) transparent',
                }}
            >
                {MOCK_CAPSULES.map((capsule, index) => (
                    <CapsuleCard key={capsule.id} capsule={capsule} isActive={index === activeIndex} />
                ))}
            </div>
        </div>
    );
};

const CapsuleCard = ({ capsule, isActive }: { capsule: Capsule, isActive: boolean }) => {
    const [selectedOption, setSelectedOption] = useState<number | null>(null);
    const [showExplanation, setShowExplanation] = useState(false);

    const handleOptionClick = (index: number) => {
        if (selectedOption !== null) return; // Prevent changing answer
        setSelectedOption(index);
        setShowExplanation(true);
    };

    const getOptionColor = (index: number) => {
        if (selectedOption === null) return "bg-secondary text-secondary-foreground hover:bg-secondary/80";
        if (index === capsule.correctAnswer) return "bg-emerald-500 text-white border-emerald-600";
        if (selectedOption === index) return "bg-red-500 text-white border-red-600";
        return "bg-secondary/50 text-muted-foreground";
    };

    const getOptionIcon = (index: number) => {
        if (selectedOption === null) return null;
        if (index === capsule.correctAnswer) return <CheckCircle className="h-4 w-4" />;
        if (selectedOption === index) return <XCircle className="h-4 w-4" />;
        return null;
    };

    return (
        <div className="w-full p-2 sm:p-4 py-8 flex justify-center min-h-[80vh]">
            <Card className="w-full max-w-3xl h-auto flex flex-col shadow-xl border-2 dark:border-white/10 relative transition-all duration-300">
                <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${capsule.difficulty === 'Easy' ? 'from-green-400 to-green-600' :
                    capsule.difficulty === 'Medium' ? 'from-yellow-400 to-yellow-600' :
                        'from-red-400 to-red-600'
                    }`} />

                <CardContent className="flex flex-col p-4 sm:p-6 gap-4">
                    <div className="flex justify-between items-start shrink-0">
                        <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20">
                            {capsule.topic}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                            {capsule.difficulty}
                        </Badge>
                    </div>

                    <div className="flex flex-col gap-6">
                        <h3 className="text-lg font-semibold leading-relaxed">
                            {capsule.question}
                        </h3>

                        <div className="space-y-3">
                            {capsule.options.map((option, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => handleOptionClick(idx)}
                                    disabled={selectedOption !== null}
                                    className={`w-full p-4 rounded-lg text-left text-sm font-medium transition-all duration-200 border flex items-center justify-between ${getOptionColor(idx)}`}
                                >
                                    <span>{option}</span>
                                    {getOptionIcon(idx)}
                                </button>
                            ))}
                        </div>
                    </div>

                    <AnimatePresence>
                        {showExplanation && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-muted/50 p-4 rounded-lg text-sm border border-border"
                            >
                                <p className="font-semibold mb-1 text-primary">Explanation:</p>
                                <p className="text-muted-foreground">{capsule.explanation}</p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </CardContent>
            </Card>
        </div>
    );
};
