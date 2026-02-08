import { useState } from 'react';
import { MainLayout } from "@/components/layout/MainLayout";
import { RevisionCapsules } from "@/components/dashboard/mistakes/RevisionCapsules";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Atom, FlaskConical, Calculator, ChevronRight, PlayCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const REVISION_TOPICS = [
    { id: '1', subject: 'Physics', name: 'Alternating Current', count: 5, icon: Atom, color: 'text-emerald-500' },
    { id: '2', subject: 'Physics', name: 'Semiconductors', count: 3, icon: Atom, color: 'text-emerald-500' },
    { id: '3', subject: 'Physics', name: 'Ray Optics', count: 8, icon: Atom, color: 'text-emerald-500' },
    { id: '4', subject: 'Chemistry', name: 'Thermodynamics', count: 4, icon: FlaskConical, color: 'text-orange-500' },
    { id: '5', subject: 'Maths', name: 'Calculus', count: 6, icon: Calculator, color: 'text-blue-500' },
];

const RevisionCapsulesPage = () => {
    const [selectedTopic, setSelectedTopic] = useState(REVISION_TOPICS[0].id);

    return (
        <MainLayout>
            <div className="h-[calc(100vh-6rem)] p-4 sm:p-6 lg:p-8 animate-fade-in flex flex-col gap-6 overflow-hidden">
                <div className="grid grid-cols-1 grid-rows-[300px_1fr] lg:grid-rows-none lg:grid-cols-12 gap-6 flex-1 min-h-0">
                    {/* Left Sidebar - Topics */}
                    <Card className="lg:col-span-3 h-full flex flex-col border-border/50 shadow-sm overflow-hidden">
                        <CardHeader className="pb-3 border-b bg-muted/30">
                            <CardTitle className="text-lg font-medium flex items-center gap-2">
                                <PlayCircle className="h-5 w-5 text-primary" />
                                Topics Covered
                            </CardTitle>
                        </CardHeader>
                        <ScrollArea className="flex-1">
                            <div className="p-3 space-y-1">
                                {REVISION_TOPICS.map((topic) => (
                                    <button
                                        key={topic.id}
                                        onClick={() => setSelectedTopic(topic.id)}
                                        className={cn(
                                            "w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all hover:bg-muted/50 group",
                                            selectedTopic === topic.id ? "bg-primary/10 hover:bg-primary/15" : "bg-transparent"
                                        )}
                                    >
                                        <div className={cn(
                                            "h-10 w-10 rounded-full flex items-center justify-center shrink-0 border",
                                            selectedTopic === topic.id ? "bg-background border-primary/20" : "bg-muted border-transparent"
                                        )}>
                                            <topic.icon className={cn("h-5 w-5", topic.color)} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium truncate text-sm">{topic.name}</div>
                                            <div className="text-xs text-muted-foreground">{topic.count} Capsules</div>
                                        </div>
                                        {selectedTopic === topic.id && (
                                            <ChevronRight className="h-4 w-4 text-primary animate-in slide-in-from-left-2" />
                                        )}
                                    </button>
                                ))}
                            </div>
                        </ScrollArea>
                    </Card>

                    {/* Right Section - Capsules */}
                    <div className="lg:col-span-9 h-full overflow-hidden">
                        <RevisionCapsules />
                    </div>
                </div>
            </div>
        </MainLayout>
    );
};

export default RevisionCapsulesPage;
