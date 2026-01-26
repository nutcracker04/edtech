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
import { Loader2 } from "lucide-react";

interface TestCreationDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess: (testId?: string) => void;
}

export const TestCreationDialog = ({ open, onOpenChange, onSuccess }: TestCreationDialogProps) => {
    const [activeTab, setActiveTab] = useState("adaptive");
    const [loading, setLoading] = useState(false);
    const [hierarchy, setHierarchy] = useState<any[]>([]);

    // Form State
    const [selectedSubject, setSelectedSubject] = useState<string>("");
    const [selectedChapters, setSelectedChapters] = useState<string[]>([]);
    const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
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
                title: `${activeTab === 'adaptive' ? 'Adaptive' : 'Practice'} Test - ${new Date().toLocaleDateString()}`,
                type: activeTab === 'custom' ? 'practice' : activeTab,
                duration: duration,
                number_of_questions: questionCount,
                difficulty: difficulty
            };

            if (selectedSubject) {
                payload.subject_id = selectedSubject;
                // Find subject name for metadata
                const sub = hierarchy.find(h => h.id === selectedSubject);
                if (sub) payload.subject = sub.name;
            }

            if (selectedChapters.length > 0) {
                payload.chapter_ids = selectedChapters;
            }

            if (selectedTopics.length > 0) {
                payload.topic_ids = selectedTopics;
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

    const currentSubjectObj = hierarchy.find(h => h.id === selectedSubject);

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle>Create New Test</DialogTitle>
                </DialogHeader>

                <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0">
                    <TabsList className="grid w-full grid-cols-2">
                        <TabsTrigger value="adaptive">Adaptive Test</TabsTrigger>
                        <TabsTrigger value="custom">Custom Practice</TabsTrigger>
                    </TabsList>

                    <ScrollArea className="flex-1 pr-4 mt-4">
                        <div className="space-y-6 pb-6">

                            {/* Common Settings */}
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
                                    <Select value={duration.toString()} onValueChange={v => setDuration(parseInt(v))}>
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

                            {/* Subject Selection */}
                            <div className="space-y-2">
                                <Label>Subject</Label>
                                <div className="grid grid-cols-3 gap-2">
                                    {hierarchy.map(sub => (
                                        <div
                                            key={sub.id}
                                            onClick={() => {
                                                setSelectedSubject(selectedSubject === sub.id ? "" : sub.id);
                                                setSelectedChapters([]);
                                                setSelectedTopics([]);
                                            }}
                                            className={`p-3 rounded-lg border cursor-pointer transition-colors text-center ${selectedSubject === sub.id
                                                ? 'bg-primary/20 border-primary text-primary font-medium'
                                                : 'hover:bg-secondary/50'
                                                }`}
                                        >
                                            {sub.name}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {activeTab === 'custom' && selectedSubject && currentSubjectObj && (
                                <>
                                    <div className="space-y-2">
                                        <Label>Chapters (Optional)</Label>
                                        <div className="grid grid-cols-2 gap-2 text-sm">
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
                                                    <label htmlFor={chap.id} className="cursor-pointer">
                                                        {chap.name}
                                                    </label>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {selectedChapters.length > 0 && (
                                        <div className="space-y-2">
                                            <Label>Topics (Optional)</Label>
                                            <div className="grid grid-cols-2 gap-2 text-sm">
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
                                                            <label htmlFor={topic.id} className="cursor-pointer">
                                                                {topic.name}
                                                            </label>
                                                        </div>
                                                    ))
                                                }
                                            </div>
                                        </div>
                                    )}

                                    <div className="space-y-2">
                                        <Label>Difficulty</Label>
                                        <Select value={difficulty} onValueChange={setDifficulty}>
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="easy">Easy</SelectItem>
                                                <SelectItem value="medium">Medium</SelectItem>
                                                <SelectItem value="hard">Hard</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </>
                            )}

                            {activeTab === 'adaptive' && (
                                <div className="p-4 bg-blue-500/10 text-blue-400 rounded-lg text-sm">
                                    Adaptive tests will automatically select questions based on your weak areas in the selected subject (or all subjects if none selected).
                                </div>
                            )}

                        </div>
                    </ScrollArea>

                    <div className="mt-4 pt-4 border-t flex justify-end gap-2">
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
