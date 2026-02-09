
import { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { useParams, useNavigate } from 'react-router-dom';
import { supabase } from '@/integrations/supabase/client';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowLeft, Image as ImageIcon, Trash2, Pencil, Save, X, Loader2, Check, ChevronsUpDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
    DialogDescription
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

interface Question {
    id: string;
    question_text: string;
    options: { id: string; text: string }[] | string; // Allow string/JSON
    correct_answer: string;
    has_image: boolean;
    image_url: string;
    subject_id: string;
    chapter_id: string;
    topic_id: string;
    question_number: number;
    page_number: number;
    chapter_ids: string[];
    topic_ids: string[];
}

interface Subject { id: string; name: string; }
interface Chapter { id: string; name: string; subject_id: string; }
interface Topic { id: string; name: string; chapter_id: string; }

const renderTable = (text: string) => {
    const match = text.match(/\\begin{tabular}{[^}]*}(.*?)\\end{tabular}/s);
    if (!match) return text;

    const content = match[1];
    const rows = content
        .split('\\\\')
        .filter(r => r.trim() && !r.includes('\\hline'))
        .map(r => r.split('&').map(c => c.trim()));

    return (
        <table className="border text-sm my-2">
            <tbody>
                {rows.map((row, i) => (
                    <tr key={i}>
                        {row.map((cell, j) => (
                            <td key={j} className="border px-2 py-1">
                                {renderMathText(cell)}
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
};

const renderTextWithHeuristics = (text: string) => {
    // Heuristic pattern to detect potential LaTeX that isn't wrapped in $...$
    // Matches:
    // 1. Exponents: 10^4, 10^{-6}, L^{-1}, M^2
    // 2. LaTeX commands: \text{...}, \times, \alpha
    // 3. Subscripts: P_C, V_C
    const mathPattern = /([A-Za-z0-9]+\s*\^\s*(?:\{[^}]+\}|-?\d+)|\\text\{[^}]*\}|\\[a-zA-Z]+|[A-Z]_[A-Za-z0-9]+)/g;

    // Split includes capturing groups, so odd indices will be the matches
    const parts = text.split(mathPattern);

    return (
        <>
            {parts.map((part, i) => {
                // Odd indices are the regex matches (potential math)
                // Filter out empty strings or purely whitespace matches if any
                if (i % 2 === 1 && part.trim().length > 0) {
                    try {
                        return <InlineMath key={i} math={part} errorColor="#ef4444" />;
                    } catch (e) {
                        // Fallback if it wasn't actually valid math
                        return <span key={i}>{part}</span>;
                    }
                }
                return <span key={i}>{part}</span>;
            })}
        </>
    );
};

const renderMathText = (text: string) => {
    if (!text) return null;

    // Check for LaTeX tables
    if (text.includes('\\begin{tabular}')) {
        return renderTable(text);
    }

    // Validation warning (keep for debugging)
    if (/[₀-₉⁰-⁹°±×÷≠≤≥]/.test(text)) {
        console.warn('Unicode math characters detected, backend should use LaTeX:', text);
    }

    try {
        // Split by $...$ for inline math and $$...$$ for block math
        const parts = text.split(/(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g);

        return (
            <span>
                {parts.map((part, index) => {
                    if (part.startsWith('$$') && part.endsWith('$$')) {
                        const math = part.slice(2, -2);
                        try {
                            return <BlockMath key={index} math={math} errorColor="#ef4444" />;
                        } catch (e) {
                            console.error('BlockMath error:', e, 'Content:', math);
                            return <span key={index} className="text-red-500 text-xs">[Math Error]</span>;
                        }
                    } else if (part.startsWith('$') && part.endsWith('$')) {
                        const math = part.slice(1, -1);
                        try {
                            return <InlineMath key={index} math={math} errorColor="#ef4444" />;
                        } catch (e) {
                            console.error('InlineMath error:', e, 'Content:', math);
                            return <span key={index} className="text-red-500 text-xs">[Math Error]</span>;
                        }
                    } else {
                        // Regular text, but check for missed LaTeX patterns
                        return <span key={index}>{renderTextWithHeuristics(part)}</span>;
                    }
                })}
            </span>
        );
    } catch (e) {
        console.error('Math rendering error:', e);
        return <span className="text-red-500 text-xs">[Render Error]</span>;
    }
};

const AdminPyqView = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [questions, setQuestions] = useState<Question[]>([]);
    const [paper, setPaper] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    // Edit State
    const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    // Delete Paper State
    const [confirmDeletePaper, setConfirmDeletePaper] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    // Hierarchy State
    const [subjects, setSubjects] = useState<Subject[]>([]);
    const [chapters, setChapters] = useState<Chapter[]>([]);
    const [topics, setTopics] = useState<Topic[]>([]);
    const [openChapterSelect, setOpenChapterSelect] = useState(false);
    const [openTopicSelect, setOpenTopicSelect] = useState(false);

    useEffect(() => {
        if (id) {
            fetchData();
            fetchHierarchy();
        }
    }, [id]);

    const fetchHierarchy = async () => {
        const { data: sData } = await supabase.from("subjects").select("*").order("name");
        if (sData) setSubjects(sData);

        const { data: cData } = await supabase.from("chapters").select("*").order("name");
        if (cData) setChapters(cData);

        const { data: tData } = await supabase.from("topics").select("*").order("name");
        if (tData) setTopics(tData);
    };

    const fetchData = async () => {
        if (!id) return;
        setLoading(true);

        try {
            // Fetch Paper
            const { data: paperData, error: paperError } = await supabase
                .from('pyq_papers')
                .select('*')
                .eq('id', id)
                .single();

            if (paperData) setPaper(paperData);
            if (paperError) console.error("Error fetching paper:", paperError);

            // Fetch Questions
            const { data: qData, error: qError } = await supabase
                .from('pyq_questions')
                .select('*')
                .eq('paper_id', id)
                .order('question_number', { ascending: true });

            if (qData) setQuestions(qData as any);
            if (qError) console.error("Error fetching questions:", qError);
        } catch (err) {
            console.error("Fetch Data failed:", err);
            toast.error("Failed to load paper data");
        } finally {
            setLoading(false);
        }
    };

    const handleDeletePaper = async () => {
        setIsDeleting(true);
        try {
            const token = (await supabase.auth.getSession()).data.session?.access_token;
            const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

            const res = await fetch(`${API_BASE_URL}/api/pyq/papers/${id}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!res.ok) throw new Error('Failed to delete paper');

            toast.success("Paper deleted successfully");
            navigate('/admin/pyq');
        } catch (e) {
            toast.error("Failed to delete paper");
            setIsDeleting(false);
            setConfirmDeletePaper(false);
        }
    };

    const handleDeleteQuestion = async (qId: string) => {
        if (!confirm("Are you sure you want to delete this question?")) return;

        try {
            const token = (await supabase.auth.getSession()).data.session?.access_token;
            const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

            const res = await fetch(`${API_BASE_URL}/api/pyq/questions/${qId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!res.ok) throw new Error('Failed to delete question');

            toast.success("Question deleted");
            setQuestions(questions.filter(q => q.id !== qId));
        } catch (e) {
            toast.error("Failed to delete question");
        }
    };

    const handleSaveQuestion = async () => {
        if (!editingQuestion) return;
        setIsSaving(true);

        try {
            const token = (await supabase.auth.getSession()).data.session?.access_token;
            const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

            // Ensure options is stringified properly if needed or backend handles it
            const payload = {
                ...editingQuestion,
                // If options is a string (JSON), parse it back to object for DB or keep as is depending on DB expectation
                // The DB expects JSON type.
                chapter_ids: editingQuestion.chapter_ids || (editingQuestion.chapter_id ? [editingQuestion.chapter_id] : []),
                topic_ids: editingQuestion.topic_ids || (editingQuestion.topic_id ? [editingQuestion.topic_id] : [])
            };

            const res = await fetch(`${API_BASE_URL}/api/pyq/questions/${editingQuestion.id}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error('Failed to update question');

            const updated = await res.json();
            setQuestions(questions.map(q => q.id === updated.id ? updated : q));
            toast.success("Question updated");
            setEditingQuestion(null);
        } catch (e) {
            toast.error("Failed to update question");
        } finally {
            setIsSaving(false);
        }
    };

    const updateOptionText = (idx: number, text: string) => {
        if (!editingQuestion) return;

        let newOptions: any[] = [];
        if (typeof editingQuestion.options === 'string') {
            try {
                newOptions = JSON.parse(editingQuestion.options);
            } catch (e) {
                newOptions = [];
            }
        } else {
            newOptions = [...(editingQuestion.options || [])];
        }

        if (newOptions[idx]) {
            newOptions[idx].text = text;
        }

        setEditingQuestion({ ...editingQuestion, options: newOptions });
    };

    const getOptionsArray = (options: any): { id: string; text: string }[] => {
        if (!options) return [];
        if (Array.isArray(options)) return options;
        if (typeof options === 'string') {
            try {
                return JSON.parse(options);
            } catch (e) {
                return [];
            }
        }
        return [];
    };

    if (loading) return <MainLayout><div className="p-8 flex items-center justify-center"><Loader2 className="animate-spin mr-2" /> Loading...</div></MainLayout>;

    return (
        <MainLayout>
            <div className="container py-8 max-w-5xl">
                <Button variant="ghost" className="mb-4 gap-2" onClick={() => navigate('/admin/pyq')}>
                    <ArrowLeft className="w-4 h-4" /> Back to Papers
                </Button>

                <div className="flex justify-between items-start mb-8">
                    <div>
                        <h1 className="text-3xl font-bold">{paper?.exam_type}</h1>
                        <p className="text-muted-foreground">{paper?.exam_date} • {paper?.exam_session}</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <Badge variant={paper?.processing_status === 'completed' ? 'default' : 'secondary'}>
                            {paper?.processing_status}
                        </Badge>
                        <Button variant="destructive" size="sm" onClick={() => setConfirmDeletePaper(true)}>
                            <Trash2 className="w-4 h-4 mr-2" /> Delete Paper
                        </Button>
                    </div>
                </div>

                <div className="space-y-6">
                    {questions.map((q, idx) => {
                        const options = getOptionsArray(q.options);
                        return (
                            <Card key={q.id}>
                                <CardContent className="pt-6">
                                    <div className="flex gap-4">
                                        <div className="flex-shrink-0 w-8 h-8 bg-muted rounded-full flex items-center justify-center font-bold text-sm">
                                            {q.question_number || idx + 1}
                                        </div>
                                        <div className="flex-grow space-y-4">
                                            {/* Question Text */}
                                            <div className="prose max-w-none dark:prose-invert">
                                                {/* Tags Display */}
                                                <div className="flex flex-wrap gap-2 mb-2">
                                                    {q.subject_id && (
                                                        <Badge variant="outline" className="text-xs">
                                                            {subjects.find(s => s.id === q.subject_id)?.name || "Subject"}
                                                        </Badge>
                                                    )}
                                                    {(q.chapter_ids || (q.chapter_id ? [q.chapter_id] : [])).map(cid => (
                                                        <Badge key={cid} variant="secondary" className="text-xs">
                                                            {chapters.find(c => c.id === cid)?.name || "Chapter"}
                                                        </Badge>
                                                    ))}
                                                    {(q.topic_ids || (q.topic_id ? [q.topic_id] : [])).map(tid => (
                                                        <Badge key={tid} variant="outline" className="text-[10px] opacity-80">
                                                            {topics.find(t => t.id === tid)?.name || "Topic"}
                                                        </Badge>
                                                    ))}
                                                </div>
                                                <div className="whitespace-normal leading-relaxed">{renderMathText(q.question_text)}</div>
                                            </div>

                                            {/* Extracted Diagram */}
                                            {q.has_image && q.image_url && (
                                                <div className="border rounded-lg p-2 bg-muted/20 inline-block">
                                                    <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground">
                                                        <ImageIcon className="w-3 h-3" /> Extracted Diagram
                                                    </div>
                                                    <img
                                                        src={q.image_url}
                                                        alt="Question Diagram"
                                                        className="max-h-64 object-contain rounded border bg-white"
                                                    />
                                                </div>
                                            )}

                                            {/* Options */}
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                {options.map((opt: any) => (
                                                    <div
                                                        key={opt.id}
                                                        className={`p-3 rounded border ${q.correct_answer === opt.id
                                                            ? 'bg-green-50 border-green-200 dark:bg-green-900/20'
                                                            : 'bg-card'
                                                            }`}
                                                    >
                                                        <span className="font-bold mr-2">{opt.id}.</span>
                                                        {renderMathText(opt.text)}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="flex flex-col gap-2">
                                            <Button variant="outline" size="icon" onClick={() => setEditingQuestion(q)}>
                                                <Pencil className="w-4 h-4" />
                                            </Button>
                                            <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive" onClick={() => handleDeleteQuestion(q.id)}>
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        )
                    })}

                    {questions.length === 0 && (
                        <div className="text-center py-12 text-muted-foreground border-2 border-dashed rounded-lg">
                            No questions extracted yet.
                        </div>
                    )}
                </div>

                {/* Edit Dialog */}
                <Dialog open={!!editingQuestion} onOpenChange={(open) => !open && setEditingQuestion(null)}>
                    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                        <DialogHeader>
                            <DialogTitle>Edit Question {editingQuestion?.question_number}</DialogTitle>
                        </DialogHeader>
                        {editingQuestion && (
                            <div className="space-y-4 py-4">
                                {/* Tagging Section */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 border rounded-lg bg-muted/20">
                                    <div className="space-y-2">
                                        <Label>Subject</Label>
                                        <Select
                                            value={editingQuestion.subject_id || ""}
                                            onValueChange={(val) => setEditingQuestion({ ...editingQuestion, subject_id: val })}
                                        >
                                            <SelectTrigger><SelectValue placeholder="Subject" /></SelectTrigger>
                                            <SelectContent>
                                                {subjects.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Chapters</Label>
                                        <Popover open={openChapterSelect} onOpenChange={setOpenChapterSelect}>
                                            <PopoverTrigger asChild>
                                                <Button variant="outline" role="combobox" aria-expanded={openChapterSelect} className="w-full justify-between h-10 px-3 overflow-hidden text-left">
                                                    <span className="truncate">
                                                        {(editingQuestion.chapter_ids || []).length > 0
                                                            ? `${(editingQuestion.chapter_ids || []).length} selected`
                                                            : "Select Chapters"}
                                                    </span>
                                                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                                                </Button>
                                            </PopoverTrigger>
                                            <PopoverContent className="w-[300px] p-0">
                                                <Command>
                                                    <CommandInput placeholder="Search chapter..." />
                                                    <CommandList>
                                                        <CommandEmpty>No chapter found.</CommandEmpty>
                                                        <CommandGroup>
                                                            {chapters
                                                                .filter(c => !editingQuestion.subject_id || c.subject_id === editingQuestion.subject_id)
                                                                .map((chapter) => (
                                                                    <CommandItem
                                                                        key={chapter.id}
                                                                        value={chapter.name}
                                                                        onSelect={() => {
                                                                            const current = editingQuestion.chapter_ids || (editingQuestion.chapter_id ? [editingQuestion.chapter_id] : []);
                                                                            const newIds = current.includes(chapter.id)
                                                                                ? current.filter((id) => id !== chapter.id)
                                                                                : [...current, chapter.id];
                                                                            setEditingQuestion({ ...editingQuestion, chapter_ids: newIds });
                                                                        }}
                                                                    >
                                                                        <Check
                                                                            className={cn(
                                                                                "mr-2 h-4 w-4",
                                                                                (editingQuestion.chapter_ids || []).includes(chapter.id) ? "opacity-100" : "opacity-0"
                                                                            )}
                                                                        />
                                                                        {chapter.name}
                                                                    </CommandItem>
                                                                ))}
                                                        </CommandGroup>
                                                    </CommandList>
                                                </Command>
                                            </PopoverContent>
                                        </Popover>
                                    </div>

                                    <div className="space-y-2">
                                        <Label>Topics</Label>
                                        <Popover open={openTopicSelect} onOpenChange={setOpenTopicSelect}>
                                            <PopoverTrigger asChild>
                                                <Button variant="outline" role="combobox" aria-expanded={openTopicSelect} className="w-full justify-between h-10 px-3 overflow-hidden text-left">
                                                    <span className="truncate">
                                                        {(editingQuestion.topic_ids || []).length > 0
                                                            ? `${(editingQuestion.topic_ids || []).length} selected`
                                                            : "Select Topics"}
                                                    </span>
                                                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                                                </Button>
                                            </PopoverTrigger>
                                            <PopoverContent className="w-[300px] p-0">
                                                <Command>
                                                    <CommandInput placeholder="Search topic..." />
                                                    <CommandList>
                                                        <CommandEmpty>No topic found.</CommandEmpty>
                                                        <CommandGroup>
                                                            {topics
                                                                .filter(t => {
                                                                    const currentChapters = editingQuestion.chapter_ids || [];
                                                                    return currentChapters.length === 0 || currentChapters.includes(t.chapter_id);
                                                                })
                                                                .map((topic) => (
                                                                    <CommandItem
                                                                        key={topic.id}
                                                                        value={topic.name}
                                                                        onSelect={() => {
                                                                            const current = editingQuestion.topic_ids || (editingQuestion.topic_id ? [editingQuestion.topic_id] : []);
                                                                            const newIds = current.includes(topic.id)
                                                                                ? current.filter((id) => id !== topic.id)
                                                                                : [...current, topic.id];
                                                                            setEditingQuestion({ ...editingQuestion, topic_ids: newIds });
                                                                        }}
                                                                    >
                                                                        <Check
                                                                            className={cn(
                                                                                "mr-2 h-4 w-4",
                                                                                (editingQuestion.topic_ids || []).includes(topic.id) ? "opacity-100" : "opacity-0"
                                                                            )}
                                                                        />
                                                                        {topic.name}
                                                                    </CommandItem>
                                                                ))}
                                                        </CommandGroup>
                                                    </CommandList>
                                                </Command>
                                            </PopoverContent>
                                        </Popover>
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label>Question Text (LaTeX supported with $...$)</Label>
                                    <Textarea
                                        value={editingQuestion.question_text}
                                        onChange={(e) => setEditingQuestion({ ...editingQuestion, question_text: e.target.value })}
                                        rows={5}
                                    />
                                    <div className="text-xs text-muted-foreground p-2 bg-muted rounded">
                                        <strong>Preview:</strong> {renderMathText(editingQuestion.question_text)}
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label>Correct Answer</Label>
                                    <Select
                                        value={editingQuestion.correct_answer}
                                        onValueChange={(val) => setEditingQuestion({ ...editingQuestion, correct_answer: val })}
                                    >
                                        <SelectTrigger>
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {getOptionsArray(editingQuestion.options).map(opt => (
                                                <SelectItem key={opt.id} value={opt.id}>Option {opt.id}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2">
                                    <Label>Options</Label>
                                    <div className="space-y-2">
                                        {getOptionsArray(editingQuestion.options).map((opt, idx) => (
                                            <div key={opt.id} className="grid gap-2">
                                                <div className="flex items-start gap-2">
                                                    <div className="pt-2 font-bold w-6 border-r pr-2">{opt.id}</div>
                                                    <Textarea
                                                        value={opt.text}
                                                        onChange={(e) => updateOptionText(idx, e.target.value)}
                                                        rows={2}
                                                    />
                                                </div>
                                                <div className="text-xs text-muted-foreground ml-10">
                                                    Preview: {renderMathText(opt.text)}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setEditingQuestion(null)}>Cancel</Button>
                            <Button onClick={handleSaveQuestion} disabled={isSaving}>
                                {isSaving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                                Save Changes
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                {/* Confirm Delete Paper Dialog */}
                <Dialog open={confirmDeletePaper} onOpenChange={setConfirmDeletePaper}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Delete Paper?</DialogTitle>
                            <DialogDescription>
                                Accion irreversible. All questions associated with this paper will also be deleted.
                            </DialogDescription>
                        </DialogHeader>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setConfirmDeletePaper(false)} disabled={isDeleting}>Cancel</Button>
                            <Button variant="destructive" onClick={handleDeletePaper} disabled={isDeleting}>
                                {isDeleting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                                Delete
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
        </MainLayout>
    );
};

export default AdminPyqView;
