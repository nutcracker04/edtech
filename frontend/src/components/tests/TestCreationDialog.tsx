import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { testApi } from "@/api/test";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

interface TestCreationDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: (testId?: string) => void;
}

export const TestCreationDialog = ({ open, onOpenChange, onSuccess }: TestCreationDialogProps) => {
    const [loading, setLoading] = useState(false);
    const [hierarchy, setHierarchy] = useState<any[]>([]);

    // Custom Mode State
    const [customMode, setCustomMode] = useState<"adaptive" | "practice">("adaptive");

    // Form State
    const [selectedSubject, setSelectedSubject] = useState<string>(""); // For Practice Mode (Single Subject)
    const [selectedSubjectIds, setSelectedSubjectIds] = useState<string[]>([]); // For Adaptive Mode (Multi-Subject)
    const [selectedChapters, setSelectedChapters] = useState<string[]>([]);
    const [selectedTopics, setSelectedTopics] = useState<string[]>([]);

    // Defaults
    const [questionCount, setQuestionCount] = useState(20);
    const [duration, setDuration] = useState(30);
    const [difficulty, setDifficulty] = useState("medium");

    useEffect(() => {
        if (open) {
            loadHierarchy();
        }
    }, [open]);

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

            if (customMode === 'adaptive') {
                payload.type = 'adaptive';
                if (selectedSubjectIds.length === 1) {
                    payload.subject_id = selectedSubjectIds[0];
                    const sub = hierarchy.find(h => h.id === selectedSubjectIds[0]);
                    if (sub) payload.subject = sub.name;
                }
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
        return customMode === 'adaptive' ? 'Adaptive Test' : 'Chapter Practice';
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

                {/* Fixed Header Section */}
                <div className="flex flex-col border-b bg-background z-10">
                    <DialogHeader className="px-6 py-4">
                        <DialogTitle>Create New Test</DialogTitle>
                    </DialogHeader>
                </div>

                {/* Scrollable Content */}
                <ScrollArea className="flex-1 w-full">
                    <div className="p-6 space-y-6 pb-20">

                        {/* Custom Mode Type Selection */}
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

                        {/* Settings */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Questions</Label>
                                <Input
                                    type="number"
                                    min={5}
                                    max={100}
                                    value={questionCount}
                                    onChange={e => setQuestionCount(parseInt(e.target.value))}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Duration (mins)</Label>
                                <Select
                                    value={duration.toString()}
                                    onValueChange={v => setDuration(parseInt(v))}
                                >
                                    <SelectTrigger>
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

                        {/* Adaptive Subject Selection (Cards) */}
                        {customMode === 'adaptive' && (
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

                        {/* Practice Subject Selection (Dropdown/Standard) */}
                        {customMode === 'practice' && (
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
            </DialogContent>
        </Dialog>
    );
};
