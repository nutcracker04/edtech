
import { useState, useEffect } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tag, Loader2, AlertCircle, ArrowLeft, CheckCircle2, Trash2, Pencil } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { QuestionEditDialog } from "@/components/admin/QuestionEditDialog";

interface Question {
    id: string;
    question_text: string;
    options: any[];
    is_tagged: boolean;
    subject_id: string | null;
    chapter_id: string | null;
    topic_id: string | null;
    difficulty_level: string | null;
    image_url?: string | null;
}

interface Subject { id: string; name: string; }
interface Chapter { id: string; name: string; }
interface Topic { id: string; name: string; }

interface QuestionTaggingSidebarProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function QuestionTaggingSidebar({ open, onOpenChange }: QuestionTaggingSidebarProps) {
    const [questions, setQuestions] = useState<Question[]>([]);
    const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
    const [isLoadingQuestions, setIsLoadingQuestions] = useState(false);

    const [subjects, setSubjects] = useState<Subject[]>([]);
    const [chapters, setChapters] = useState<Chapter[]>([]);
    const [topics, setTopics] = useState<Topic[]>([]);

    const [selectedSubject, setSelectedSubject] = useState<string>("");
    const [selectedChapter, setSelectedChapter] = useState<string>("");
    const [selectedTopic, setSelectedTopic] = useState<string>("");
    const [difficulty, setDifficulty] = useState<string>("medium");

    const [isSaving, setIsSaving] = useState(false);
    const [questionToEdit, setQuestionToEdit] = useState<Question | null>(null);

    useEffect(() => {
        if (open) {
            fetchUntaggedQuestions();
            fetchSubjects();
        }
    }, [open]);

    // Cleanup selections when switching questions
    useEffect(() => {
        if (currentQuestion) {
            // Keep subject selected if previously selected (common workflow)
            // But reset deeper levels if not applicable - actually simple is keep subject, reset others
            // For now, let's keep subject as is, reset chapter/topic if subject not changed, 
            // but usually we want to keep context if tagging sequential questions from same chapter.
            // Let's NOT reset automatically on question switch, only on save if desired.
            // Actually, for safety, if we switch question, we might want to ensure we don't accidentally tag with wrong chapter.
            // But usually untagged questions from one paper belong to same subject/chapter sequence.
            // Let's keep the values. 
        }
    }, [currentQuestion]);

    useEffect(() => {
        if (selectedSubject) {
            fetchChapters(selectedSubject);
            // Only reset chapter if it doesn't belong to new subject (not handled here, but Select handles it)
            // But to be clean:
            // setSelectedChapter("");
            // setTopics([]);
            // Wait, if we change subject manually, we should reset.
        }
    }, [selectedSubject]);

    // We need to distinguish between "Effect triggered by manual selection" and "Effect triggered by initial load".
    // For simplicity: When subject changes, refetch chapters. If current chapter not in new list, reset it.

    useEffect(() => {
        if (selectedChapter) {
            fetchTopics(selectedChapter);
        }
    }, [selectedChapter]);

    const fetchUntaggedQuestions = async () => {
        setIsLoadingQuestions(true);
        const { data, error } = await supabase
            .from("repository_questions")
            .select("*")
            .eq("is_tagged", false)
            .limit(50);

        if (error) {
            toast.error("Error fetching questions");
        } else {
            setQuestions(data || []);
            // Don't auto-select first question, let user see list
            setCurrentQuestion(null);
        }
        setIsLoadingQuestions(false);
    };

    const fetchSubjects = async () => {
        const { data } = await supabase.from("subjects").select("*").order("name");
        setSubjects(data || []);
    };

    const fetchChapters = async (sid: string) => {
        const { data } = await supabase.from("chapters").select("*").eq("subject_id", sid).order("name");
        setChapters(data || []);
    };

    const fetchTopics = async (cid: string) => {
        const { data } = await supabase.from("topics").select("*").eq("chapter_id", cid).order("name");
        setTopics(data || []);
    };

    const handleDeleteQuestion = async (e: React.MouseEvent, id: string) => {
        e.stopPropagation();
        if (!confirm("Are you sure you want to delete this question permanently?")) return;

        const { error } = await supabase.from("repository_questions").delete().eq("id", id);

        if (error) {
            toast.error("Failed to delete question");
        } else {
            toast.success("Question deleted");
            const remaining = questions.filter(q => q.id !== id);
            setQuestions(remaining);
            if (currentQuestion?.id === id) {
                setCurrentQuestion(null);
            }
        }
    };

    const handleEditQuestion = () => {
        setQuestionToEdit(currentQuestion);
    };

    const handleSubjectChange = (val: string) => {
        setSelectedSubject(val);
        setSelectedChapter("");
        setSelectedTopic("");
    };

    const handleChapterChange = (val: string) => {
        setSelectedChapter(val);
        setSelectedTopic("");
    };

    const handleTagQuestion = async () => {
        if (!currentQuestion || !selectedSubject || !selectedChapter || !selectedTopic) {
            toast.error("Please select Subject, Chapter and Topic");
            return;
        }

        setIsSaving(true);
        const { error } = await supabase
            .from("repository_questions")
            // @ts-ignore
            .update({
                subject_id: selectedSubject,
                chapter_id: selectedChapter,
                topic_id: selectedTopic,
                difficulty_level: difficulty,
                is_tagged: true,
                updated_at: new Date().toISOString()
            } as any)
            .eq("id", currentQuestion.id);

        if (error) {
            toast.error("Error tagging question");
        } else {
            toast.success("Question tagged successfully");

            // Remove from list
            const remaining = questions.filter(q => q.id !== currentQuestion.id);
            setQuestions(remaining);

            // Move to next question automatically if available
            if (remaining.length > 0) {
                // Find index of current, or just take the first one?
                // Usually take the next one in the list.
                // Since this view was just a list, and we removed one, let's just take the first one of remaining
                // to facilitate rapid tagging.
                setCurrentQuestion(remaining[0]);
            } else {
                setCurrentQuestion(null);
                // Maybe close, or show empty state?
            }
        }
        setIsSaving(false);
    };

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent className="w-full sm:max-w-xl overflow-hidden flex flex-col p-0">
                <SheetHeader className="px-6 py-4 border-b">
                    <SheetTitle className="flex items-center justify-between">
                        Tag Questions
                        <Badge variant="secondary">{questions.length} Untagged</Badge>
                    </SheetTitle>
                    <SheetDescription>
                        Assign metadata to uploaded questions.
                    </SheetDescription>
                </SheetHeader>

                <div className="flex-1 overflow-hidden relative">
                    {/* View 1: List of Questions */}
                    {!currentQuestion && (
                        <ScrollArea className="h-full">
                            <div className="divide-y p-0">
                                {isLoadingQuestions ? (
                                    <div className="p-4 space-y-4">
                                        {[1, 2, 3].map(i => <Skeleton key={i} className="h-20 w-full" />)}
                                    </div>
                                ) : questions.length === 0 ? (
                                    <div className="flex flex-col items-center justify-center p-8 text-center h-[50vh] text-muted-foreground">
                                        <CheckCircle2 className="h-12 w-12 mb-4 text-green-500 opacity-50" />
                                        <p className="font-medium">All caught up!</p>
                                        <p className="text-sm">No untagged questions found.</p>
                                    </div>
                                ) : (
                                    questions.map((q) => (
                                        <button
                                            key={q.id}
                                            className="w-full text-left p-4 hover:bg-accent transition-colors flex flex-col gap-2 group"
                                            onClick={() => setCurrentQuestion(q)}
                                        >
                                            <div className="flex items-start justify-between gap-2">
                                                <p className="text-sm font-medium line-clamp-3 text-foreground group-hover:text-primary transition-colors">
                                                    {q.question_text || "Image only question"}
                                                </p>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive hover:bg-destructive/10"
                                                    onClick={(e) => handleDeleteQuestion(e, q.id)}
                                                    title="Delete Question"
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </div>
                                            {q.image_url && (
                                                <div className="h-12 w-12 rounded bg-muted flex items-center justify-center overflow-hidden border">
                                                    <img src={q.image_url} alt="Thumbnail" className="h-full w-full object-cover" />
                                                </div>
                                            )}
                                        </button>
                                    ))
                                )}
                            </div>
                        </ScrollArea>
                    )}

                    {/* View 2: Tagging Detail */}
                    {currentQuestion && (
                        <div className="absolute inset-0 bg-background flex flex-col animate-in slide-in-from-right duration-300">
                            <div className="flex items-center gap-2 p-2 border-b bg-muted/20">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setCurrentQuestion(null)}
                                    className="gap-1 pl-2 text-muted-foreground hover:text-foreground"
                                >
                                    <ArrowLeft className="h-4 w-4" />
                                    Back to list
                                </Button>
                                <div className="ml-auto">
                                    <Button variant="outline" size="sm" onClick={handleEditQuestion} className="gap-2 h-8">
                                        <Pencil className="h-3 w-3" />
                                        Edit Content
                                    </Button>
                                </div>
                            </div>

                            <ScrollArea className="flex-1">
                                <div className="p-6 space-y-6 pb-24">
                                    {/* Question Preview */}
                                    <div className="space-y-4">
                                        {currentQuestion.image_url && (
                                            <div className="border rounded-lg overflow-hidden bg-muted/10 flex justify-center p-4">
                                                <img
                                                    src={currentQuestion.image_url}
                                                    alt="Question"
                                                    className="max-h-[300px] w-auto object-contain rounded-md shadow-sm"
                                                />
                                            </div>
                                        )}

                                        <div className="p-4 bg-accent/30 rounded-lg border text-sm md:text-base leading-relaxed">
                                            {currentQuestion.question_text}
                                        </div>

                                        {currentQuestion.options && currentQuestion.options.length > 0 && (
                                            <div className="grid grid-cols-1 gap-2">
                                                {currentQuestion.options.map((opt: any, idx: number) => (
                                                    <div key={idx} className="flex gap-3 p-3 rounded-md border bg-card text-sm">
                                                        <span className="font-bold text-primary shrink-0">{opt.id}</span>
                                                        <span>{opt.text}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    <div className="h-px bg-border my-6" />

                                    {/* Tagging Form */}
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <Label>Subject</Label>
                                            <Select value={selectedSubject} onValueChange={handleSubjectChange}>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select Subject" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {subjects.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                                                </SelectContent>
                                            </Select>
                                        </div>

                                        <div className="space-y-2">
                                            <Label>Chapter</Label>
                                            <Select
                                                value={selectedChapter}
                                                onValueChange={handleChapterChange}
                                                disabled={!selectedSubject}
                                            >
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select Chapter" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {chapters.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
                                                </SelectContent>
                                            </Select>
                                        </div>

                                        <div className="space-y-2">
                                            <Label>Topic</Label>
                                            <Select
                                                value={selectedTopic}
                                                onValueChange={setSelectedTopic}
                                                disabled={!selectedChapter}
                                            >
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select Topic" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {topics.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}
                                                </SelectContent>
                                            </Select>
                                        </div>

                                        <div className="space-y-2">
                                            <Label>Difficulty</Label>
                                            <Select value={difficulty} onValueChange={setDifficulty}>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select Difficulty" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="easy">Easy</SelectItem>
                                                    <SelectItem value="medium">Medium</SelectItem>
                                                    <SelectItem value="hard">Hard</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </div>
                                </div>
                            </ScrollArea>

                            {/* Sticky Footer */}
                            <div className="p-4 border-t bg-background mt-auto">
                                <Button
                                    className="w-full h-11 text-base"
                                    onClick={handleTagQuestion}
                                    disabled={isSaving}
                                >
                                    {isSaving ? (
                                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                    ) : (
                                        <Tag className="mr-2 h-5 w-5" />
                                    )}
                                    Tag & Next
                                </Button>
                            </div>
                        </div>
                    )}
                </div>

                <QuestionEditDialog
                    open={!!questionToEdit}
                    onOpenChange={(open) => !open && setQuestionToEdit(null)}
                    question={questionToEdit}
                    onQuestionUpdated={() => {
                        fetchUntaggedQuestions();
                        if (currentQuestion && questionToEdit && currentQuestion.id === questionToEdit.id) {
                            // no-op, fetchUntaggedQuestions handles list update.
                        }
                    }}
                    // Enable tagging in the edit dialog too, why not?
                    enableTagging={true}
                />
            </SheetContent>
        </Sheet>
    );
}
