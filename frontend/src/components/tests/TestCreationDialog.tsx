import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { testApi } from "@/api/test";
import { toast } from "sonner";
import { Loader2, BookOpen, Clock, AlertCircle } from "lucide-react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

interface TestCreationDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: (testId?: string) => void;
}

export const TestCreationDialog = ({ open, onOpenChange, onSuccess }: TestCreationDialogProps) => {
    const [activeTab, setActiveTab] = useState("jee-main");
    const [loading, setLoading] = useState(false);
    const [hierarchy, setHierarchy] = useState<any[]>([]);

    // Custom Mode State
    const [customMode, setCustomMode] = useState<"adaptive" | "practice">("adaptive");

    // Form State
    const [selectedSubject, setSelectedSubject] = useState<string>(""); // For Practice Mode (Single Subject)
    const [selectedSubjectIds, setSelectedSubjectIds] = useState<string[]>([]); // For Adaptive Mode (Multi-Subject)
    const [selectedChapters, setSelectedChapters] = useState<string[]>([]);
    const [selectedTopics, setSelectedTopics] = useState<string[]>([]);

    // Defaults based on Tab
    const [questionCount, setQuestionCount] = useState(75);
    const [duration, setDuration] = useState(180);
    const [difficulty, setDifficulty] = useState("medium");

    useEffect(() => {
        if (open) {
            loadHierarchy();
        }
    }, [open]);

    // Reset defaults when tab changes
    useEffect(() => {
        if (activeTab === "jee-main") {
            setQuestionCount(75);
            setDuration(180);
            setDifficulty("hard");
        } else if (activeTab === "jee-advanced") {
            setQuestionCount(54);
            setDuration(180);
            setDifficulty("hard");
        } else {
            // Custom defaults
            setQuestionCount(20);
            setDuration(30);
            setDifficulty("medium");
        }
    }, [activeTab]);

    const loadHierarchy = async () => {
        try {
            const data = await testApi.getHierarchy();
            setHierarchy(data);
        } catch (error) {
            toast.error("Failed to load subjects");
        }
    };

    const handleCreate = async () => {
        setLoading(true);
        try {
            const payload: any = {
                title: `${getFormattedTitle()} - ${new Date().toLocaleDateString()}`,
                duration: duration,
                number_of_questions: questionCount,
                difficulty: difficulty
            };

            // Configure Type and Subjects based on Tab
            if (activeTab === 'jee-main' || activeTab === 'jee-advanced') {
                payload.type = activeTab;
                // No specific subject_id means "All Subjects" / "Full Mock" usually
                // You might want to explicitly send all subject IDs if backend requires it, 
                // but usually "Mock" implies all.
            } else {
                // Custom Tab
                if (customMode === 'adaptive') {
                    payload.type = 'adaptive';
                    // For Adaptive, we might want to support multiple subjects if the backend supports it.
                    // Converting array to single if backend only supports one, or standardizing.
                    // Current backend `generate_adaptive_test` takes `subject_id` (singular).
                    // If multiple selected, we might need a backend change or just pick one/none (for all).
                    // For now, if 1 selected, send it. If multiple/none, send NULL (implying all/mixed).
                    if (selectedSubjectIds.length === 1) {
                        payload.subject_id = selectedSubjectIds[0];
                        const sub = hierarchy.find(h => h.id === selectedSubjectIds[0]);
                        if (sub) payload.subject = sub.name;
                    }
                    // If backend update allows list, we would send list. 
                    // Current backend seems to ignore list for adaptive, so 'All' (null) is default for multi.
                } else {
                    payload.type = 'practice'; // Standard
                    if (selectedSubject) {
                        payload.subject_id = selectedSubject;
                        const sub = hierarchy.find(h => h.id === selectedSubject);
                        if (sub) payload.subject = sub.name;
                    }
                    if (selectedChapters.length > 0) payload.chapter_ids = selectedChapters;
                    if (selectedTopics.length > 0) payload.topic_ids = selectedTopics;
                }
            }

            const result = await testApi.createTest(payload);
            toast.success("Test created successfully!");
            onSuccess(result.test_id);
            onOpenChange(false);
        } catch (error: any) {
            toast.error(error.message || "Failed to create test");
        } finally {
            setLoading(false);
        }
    };

    const getFormattedTitle = () => {
        if (activeTab === 'jee-main') return 'JEE Main Mock';
        if (activeTab === 'jee-advanced') return 'JEE Advanced Mock';
        return customMode === 'adaptive' ? 'Adaptive Practice' : 'Custom Practice';
    };

    const currentSubjectObj = hierarchy.find(h => h.id === selectedSubject);

    // Toggle for Multi-Select (Adaptive)
    const toggleSubjectSelection = (id: string) => {
        if (selectedSubjectIds.includes(id)) {
            setSelectedSubjectIds(selectedSubjectIds.filter(s => s !== id));
        } else {
            setSelectedSubjectIds([...selectedSubjectIds, id]);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="h-[85vh] w-full max-w-2xl flex flex-col p-0 gap-0 overflow-hidden">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 w-full flex flex-col min-h-0 overflow-hidden">

                    {/* Fixed Header Section */}
                    <div className="flex flex-col border-b bg-background z-10">
                        <DialogHeader className="px-6 pt-6 pb-2">
                            <DialogTitle>Create New Test</DialogTitle>
                        </DialogHeader>
                        <div className="px-6 pb-4 pt-2">
                            <TabsList className="grid w-full grid-cols-3">
                                <TabsTrigger value="jee-main">JEE Mains</TabsTrigger>
                                <TabsTrigger value="jee-advanced">JEE Advanced</TabsTrigger>
                                <TabsTrigger value="custom">Custom</TabsTrigger>
                            </TabsList>
                        </div>
                    </div>

                    {/* Scrollable Content */}
                    <ScrollArea className="flex-1 w-full">
                        <div className="p-6 space-y-6 pb-20">
                            {/* JEE Context Info */}
                            {(activeTab === 'jee-main' || activeTab === 'jee-advanced') && (
                                <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 space-y-3">
                                    <div className="flex items-center gap-2 text-primary font-medium">
                                        <BookOpen className="h-5 w-5" />
                                        {activeTab === 'jee-main' ? 'Full Syllabus Mock Test (Mains Pattern)' : 'Full Syllabus Mock Test (Advanced Pattern)'}
                                    </div>
                                    <p className="text-sm text-muted-foreground ml-7">
                                        {activeTab === 'jee-main'
                                            ? 'Standard 75 questions (25 Physics, 25 Chemistry, 25 Maths). +4 for correct, -1 for wrong.'
                                            : 'Standard 54 questions pattern. Multiple correct options, integer types included.'
                                        }
                                    </p>
                                </div>
                            )}

                            {/* Custom Mode Type Selection */}
                            {activeTab === 'custom' && (
                                <div className="space-y-4">
                                    <Label>Test Mode</Label>
                                    <RadioGroup
                                        defaultValue="adaptive"
                                        value={customMode}
                                        onValueChange={(v: any) => setCustomMode(v)}
                                        className="grid grid-cols-2 gap-4"
                                    >
                                        <div>
                                            <RadioGroupItem value="adaptive" id="adaptive" className="peer sr-only" />
                                            <Label
                                                htmlFor="adaptive"
                                                className="flex flex-col h-full items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer transition-all"
                                            >
                                                <span className="text-lg font-semibold mb-1">Adaptive</span>
                                                <span className="text-xs text-muted-foreground text-center">AI-driven difficulty based on your performance</span>
                                            </Label>
                                        </div>
                                        <div>
                                            <RadioGroupItem value="practice" id="practice" className="peer sr-only" />
                                            <Label
                                                htmlFor="practice"
                                                className="flex flex-col h-full items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer transition-all"
                                            >
                                                <span className="text-lg font-semibold mb-1">Standard</span>
                                                <span className="text-xs text-muted-foreground text-center">Manual selection of subjects and topics</span>
                                            </Label>
                                        </div>
                                    </RadioGroup>
                                </div>
                            )}

                            {/* Settings (Common for Custom, Read-only for JEE) */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Questions</Label>
                                    <Input
                                        type="number"
                                        min={5}
                                        max={100}
                                        value={questionCount}
                                        onChange={e => setQuestionCount(parseInt(e.target.value))}
                                        disabled={activeTab !== 'custom'}
                                        className={activeTab !== 'custom' ? "bg-muted" : ""}
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label>Duration (mins)</Label>
                                    <Select
                                        value={duration.toString()}
                                        onValueChange={v => setDuration(parseInt(v))}
                                        disabled={activeTab !== 'custom'}
                                    >
                                        <SelectTrigger className={activeTab !== 'custom' ? "bg-muted" : ""}>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="15">15 mins</SelectItem>
                                            <SelectItem value="30">30 mins</SelectItem>
                                            <SelectItem value="45">45 mins</SelectItem>
                                            <SelectItem value="60">1 hour</SelectItem>
                                            <SelectItem value="90">1.5 hours</SelectItem>
                                            <SelectItem value="180">3 hours</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            {/* Custom: Adaptive Subject Selection (Cards) */}
                            {activeTab === 'custom' && customMode === 'adaptive' && (
                                <div className="space-y-3">
                                    <Label>Select Subjects (Target for Adaptation)</Label>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                        {hierarchy.map(sub => {
                                            const isSelected = selectedSubjectIds.includes(sub.id);
                                            return (
                                                <div
                                                    key={sub.id}
                                                    onClick={() => toggleSubjectSelection(sub.id)}
                                                    className={`
                                                        cursor-pointer rounded-xl p-4 border-2 transition-all duration-200 flex flex-col items-center justify-center text-center gap-2
                                                        ${isSelected
                                                            ? 'border-primary bg-primary/10 shadow-sm'
                                                            : 'border-border hover:border-primary/50 hover:bg-secondary/50'
                                                        }
                                                    `}
                                                >
                                                    <div className={`
                                                        h-3 w-3 rounded-full 
                                                        ${isSelected ? 'bg-primary' : 'bg-muted-foreground/30'}
                                                    `} />
                                                    <span className={`font-semibold truncate w-full ${isSelected ? 'text-primary' : 'text-foreground'}`}>
                                                        {sub.name}
                                                    </span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                    <p className="text-xs text-muted-foreground mt-2">
                                        * Select multiple to practice mixed concepts. Leave all unselected to include everything.
                                    </p>
                                </div>
                            )}

                            {/* Custom: Practice Subject Selection (Dropdown/Standard) */}
                            {activeTab === 'custom' && customMode === 'practice' && (
                                <div className="space-y-4">
                                    <div className="space-y-2">
                                        <Label>Subject</Label>
                                        <Select value={selectedSubject} onValueChange={v => {
                                            setSelectedSubject(v);
                                            setSelectedChapters([]);
                                            setSelectedTopics([]);
                                        }}>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select a subject" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {hierarchy.map(sub => (
                                                    <SelectItem key={sub.id} value={sub.id}>{sub.name}</SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    {selectedSubject && currentSubjectObj && (
                                        <>
                                            <div className="space-y-2">
                                                <Label>Chapters</Label>
                                                <div className="grid grid-cols-2 gap-2 text-sm border rounded-lg p-3 max-h-[200px] overflow-y-auto">
                                                    {currentSubjectObj.chapters.map((chap: any) => (
                                                        <div key={chap.id} className="flex items-center space-x-2">
                                                            <Checkbox
                                                                id={chap.id}
                                                                checked={selectedChapters.includes(chap.id)}
                                                                onCheckedChange={(checked) => {
                                                                    if (checked) {
                                                                        setSelectedChapters([...selectedChapters, chap.id]);
                                                                    } else {
                                                                        setSelectedChapters(selectedChapters.filter(id => id !== chap.id));
                                                                    }
                                                                }}
                                                            />
                                                            <label htmlFor={chap.id} className="cursor-pointer text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 break-words">
                                                                {chap.name}
                                                            </label>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>

                                            {selectedChapters.length > 0 && (
                                                <div className="space-y-2">
                                                    <Label>Topics (Optional)</Label>
                                                    <div className="grid grid-cols-2 gap-2 text-sm border rounded-lg p-3 max-h-[200px] overflow-y-auto">
                                                        {currentSubjectObj.chapters
                                                            .filter((c: any) => selectedChapters.includes(c.id))
                                                            .flatMap((c: any) => c.topics)
                                                            .map((topic: any) => (
                                                                <div key={topic.id} className="flex items-center space-x-2">
                                                                    <Checkbox
                                                                        id={topic.id}
                                                                        checked={selectedTopics.includes(topic.id)}
                                                                        onCheckedChange={(checked) => {
                                                                            if (checked) {
                                                                                setSelectedTopics([...selectedTopics, topic.id]);
                                                                            } else {
                                                                                setSelectedTopics(selectedTopics.filter(id => id !== topic.id));
                                                                            }
                                                                        }}
                                                                    />
                                                                    <label htmlFor={topic.id} className="cursor-pointer text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 break-words">
                                                                        {topic.name}
                                                                    </label>
                                                                </div>
                                                            ))
                                                        }
                                                    </div>
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            )}

                        </div>
                    </ScrollArea>

                    {/* Fixed Footer */}
                    <div className="flex border-t p-4 justify-end gap-2 bg-background z-10 shrink-0">
                        <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
                        <Button onClick={handleCreate} disabled={loading}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Create Test
                        </Button>
                    </div>

                </Tabs>
            </DialogContent>
        </Dialog>
    );
};

