
import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import { Loader2, Plus, Trash2, Save } from "lucide-react";

interface Option {
    id: string; // 'A', 'B', etc.
    text: string;
}

interface Question {
    id: string;
    question_text: string;
    options: Option[];
    correct_answer?: string;
    subject_id: string | null;
    chapter_id: string | null;
    topic_id: string | null;
    difficulty_level: string | null;
    status?: string | null;
    is_tagged?: boolean;
}

interface QuestionEditDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    question: Question | null;
    onQuestionUpdated: () => void;
    // Optional: Enable/Disable tagging (default true)
    enableTagging?: boolean;
}

// Internal interfaces for metadata
interface Subject { id: string; name: string; }
interface Chapter { id: string; name: string; }
interface Topic { id: string; name: string; }

export function QuestionEditDialog({
    open,
    onOpenChange,
    question,
    onQuestionUpdated,
    enableTagging = true
}: QuestionEditDialogProps) {
    const [questionText, setQuestionText] = useState("");
    const [options, setOptions] = useState<Option[]>([]);
    const [correctAnswer, setCorrectAnswer] = useState("");

    // Tagging state
    const [subjectId, setSubjectId] = useState<string | null>(null);
    const [chapterId, setChapterId] = useState<string | null>(null);
    const [topicId, setTopicId] = useState<string | null>(null);
    const [difficulty, setDifficulty] = useState<string>("medium");

    // Metadata state
    const [subjects, setSubjects] = useState<Subject[]>([]);
    const [chapters, setChapters] = useState<Chapter[]>([]);
    const [topics, setTopics] = useState<Topic[]>([]);

    const [saving, setSaving] = useState(false);

    // Fetch Subjects on Mount (once)
    useEffect(() => {
        if (open && enableTagging) {
            fetchSubjects();
        }
    }, [open, enableTagging]);

    // Initialize state from question
    useEffect(() => {
        if (question && open) {
            setQuestionText(question.question_text || "");
            const opts = Array.isArray(question.options) ? question.options : [];
            setOptions(opts);
            setCorrectAnswer(question.correct_answer || "");

            setSubjectId(question.subject_id);
            setChapterId(question.chapter_id);
            setTopicId(question.topic_id);
            setDifficulty(question.difficulty_level || "medium");

            // If we have tags, we must ensure metadata is loaded to show labels
            if (enableTagging) {
                if (question.subject_id) fetchChapters(question.subject_id);
                if (question.chapter_id) fetchTopics(question.chapter_id);
            }
        }
    }, [question, open]);

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

    const handleSubjectChange = (val: string) => {
        setSubjectId(val);
        setChapterId(null);
        setTopicId(null);
        fetchChapters(val);
        setChapters([]); // clear old chapters while fetching? optional
        setTopics([]);
    };

    const handleChapterChange = (val: string) => {
        setChapterId(val);
        setTopicId(null);
        fetchTopics(val);
        setTopics([]);
    };

    const handleUpdateOption = (index: number, text: string) => {
        const newOptions = [...options];
        newOptions[index] = { ...newOptions[index], text };
        setOptions(newOptions);
    };

    const handleAddOption = () => {
        const nextLetter = String.fromCharCode(65 + options.length);
        setOptions([...options, { id: nextLetter, text: "" }]);
    };

    const handleRemoveOption = (index: number) => {
        if (options.length <= 2) {
            toast.error("Minimum 2 options required");
            return;
        }
        const newOptions = options.filter((_, i) => i !== index);
        const reindexed = newOptions.map((opt, i) => ({
            ...opt,
            id: String.fromCharCode(65 + i)
        }));
        setOptions(reindexed);
        if (!reindexed.find(o => o.id === correctAnswer)) {
            setCorrectAnswer("");
        }
    };

    const handleSave = async () => {
        if (!question) return;
        if (!questionText.trim()) {
            toast.error("Question text is required");
            return;
        }

        setSaving(true);
        try {
            const updates: any = {
                question_text: questionText,
                options: options,
                correct_answer: correctAnswer,
                updated_at: new Date().toISOString()
            };

            if (enableTagging) {
                updates.subject_id = subjectId;
                updates.chapter_id = chapterId;
                updates.topic_id = topicId;
                updates.difficulty_level = difficulty;

                // Automatically set status based on tagging completeness
                if (subjectId && chapterId && topicId) {
                    // Fully tagged - mark as in_review if currently untagged
                    if (!question.is_tagged) {
                        updates.status = 'in_review';
                    }
                    updates.is_tagged = false; // Keep in untagged until approved
                } else {
                    // Not fully tagged - clear status
                    updates.status = null;
                    updates.is_tagged = false;
                }
            }

            const { error } = await supabase
                .from("repository_questions")
                // @ts-ignore
                .update(updates)
                .eq("id", question.id);

            if (error) throw error;

            toast.success("Question updated successfully");
            onQuestionUpdated();
            onOpenChange(false);
        } catch (error: any) {
            toast.error("Failed to update question: " + error.message);
        } finally {
            setSaving(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Edit Question</DialogTitle>
                    <DialogDescription>Update question details{enableTagging ? " and tags" : ""}.</DialogDescription>
                </DialogHeader>

                <div className="space-y-6 py-4">
                    <div className="space-y-2">
                        <Label>Question Text</Label>
                        <Textarea
                            value={questionText}
                            onChange={(e) => setQuestionText(e.target.value)}
                            rows={4}
                            className="font-mono text-sm"
                        />
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <Label>Options</Label>
                            <Button variant="outline" size="sm" onClick={handleAddOption}>
                                <Plus className="h-3 w-3 mr-1" /> Add Option
                            </Button>
                        </div>
                        <div className="space-y-2">
                            {options.map((opt, idx) => (
                                <div key={idx} className="flex gap-2 items-center">
                                    <Badge variant="outline" className="w-8 h-8 flex justify-center shrink-0">
                                        {opt.id}
                                    </Badge>
                                    <Input
                                        value={opt.text}
                                        onChange={(e) => handleUpdateOption(idx, e.target.value)}
                                        className="font-mono"
                                    />
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => handleRemoveOption(idx)}
                                        className="shrink-0 text-destructive hover:text-destructive"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label>Correct Answer</Label>
                        <Select value={correctAnswer} onValueChange={setCorrectAnswer}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select correct answer" />
                            </SelectTrigger>
                            <SelectContent>
                                {options.map(opt => (
                                    <SelectItem key={opt.id} value={opt.id}>
                                        {opt.id} - {opt.text.substring(0, 30)}{opt.text.length > 30 ? '...' : ''}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {enableTagging && (
                        <div className="border-t pt-6 space-y-4">
                            <h3 className="font-semibold">Tags</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>Subject</Label>
                                    <Select
                                        value={subjectId || ""}
                                        onValueChange={handleSubjectChange}
                                    >
                                        <SelectTrigger><SelectValue placeholder="Subject" /></SelectTrigger>
                                        <SelectContent>
                                            {subjects.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Chapter</Label>
                                    <Select
                                        value={chapterId || ""}
                                        onValueChange={handleChapterChange}
                                        disabled={!subjectId}
                                    >
                                        <SelectTrigger><SelectValue placeholder="Chapter" /></SelectTrigger>
                                        <SelectContent>
                                            {chapters.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Topic</Label>
                                    <Select
                                        value={topicId || ""}
                                        onValueChange={setTopicId}
                                        disabled={!chapterId}
                                    >
                                        <SelectTrigger><SelectValue placeholder="Topic" /></SelectTrigger>
                                        <SelectContent>
                                            {topics.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Difficulty</Label>
                                    <Select value={difficulty} onValueChange={setDifficulty}>
                                        <SelectTrigger><SelectValue placeholder="Difficulty" /></SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="easy">Easy</SelectItem>
                                            <SelectItem value="medium">Medium</SelectItem>
                                            <SelectItem value="hard">Hard</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
                    <Button onClick={handleSave} disabled={saving}>
                        {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                        Save Changes
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
