import { useState, useEffect } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Database, Tag, AlertCircle, CheckCircle2, Filter, Check } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import { QuestionEditDialog } from "@/components/admin/QuestionEditDialog";
import { Pencil, Trash2 } from "lucide-react";

interface Question {
    id: string;
    question_text: string;
    options: any[];
    is_tagged: boolean;
    subject_id: string | null;
    chapter_id: string | null;
    topic_id: string | null;
    difficulty_level: string | null;
    correct_answer?: string;
    created_at: string;
    image_url?: string | null;
    status?: string | null;
}

interface Subject { id: string; name: string; }
interface Chapter { id: string; name: string; }
interface Topic { id: string; name: string; }

const AdminRepository = () => {
    const [activeTab, setActiveTab] = useState<"tagged" | "untagged">("tagged");
    const [questions, setQuestions] = useState<Question[]>([]);
    const [loading, setLoading] = useState(false);

    // Filter states
    const [subjects, setSubjects] = useState<Subject[]>([]);
    const [chapters, setChapters] = useState<Chapter[]>([]);
    const [topics, setTopics] = useState<Topic[]>([]);

    const [selectedSubject, setSelectedSubject] = useState<string | undefined>(undefined);
    const [selectedChapter, setSelectedChapter] = useState<string | undefined>(undefined);
    const [selectedTopic, setSelectedTopic] = useState<string | undefined>(undefined);
    const [selectedStatus, setSelectedStatus] = useState<string | undefined>(undefined);

    // Metadata lookup
    const [subjectMap, setSubjectMap] = useState<Record<string, string>>({});
    const [chapterMap, setChapterMap] = useState<Record<string, string>>({});
    const [topicMap, setTopicMap] = useState<Record<string, string>>({});

    const [questionToEdit, setQuestionToEdit] = useState<Question | null>(null);

    useEffect(() => {
        fetchMetadata();
    }, []);

    useEffect(() => {
        fetchQuestions();
    }, [activeTab, selectedSubject, selectedChapter, selectedTopic, selectedStatus]);

    useEffect(() => {
        if (selectedSubject) {
            fetchChapters(selectedSubject);
            setSelectedChapter(undefined);
            setTopics([]);
        }
    }, [selectedSubject]);

    useEffect(() => {
        if (selectedChapter) {
            fetchTopics(selectedChapter);
            setSelectedTopic(undefined);
        }
    }, [selectedChapter]);

    const fetchMetadata = async () => {
        try {
            const [subjectsRes, chaptersRes, topicsRes] = await Promise.all([
                supabase.from("subjects").select("*").order("name"),
                supabase.from("chapters").select("*").order("name"),
                supabase.from("topics").select("*").order("name"),
            ]);

            const subs = (subjectsRes.data || []) as Subject[];
            const chaps = (chaptersRes.data || []) as Chapter[];
            const tops = (topicsRes.data || []) as Topic[];

            setSubjects(subs);
            setSubjectMap(Object.fromEntries(subs.map(s => [s.id, s.name])));
            setChapterMap(Object.fromEntries(chaps.map(c => [c.id, c.name])));
            setTopicMap(Object.fromEntries(tops.map(t => [t.id, t.name])));
        } catch (error) {
            console.error("Error fetching metadata:", error);
        }
    };

    const fetchChapters = async (sid: string) => {
        try {
            const { data } = await supabase.from("chapters").select("*").eq("subject_id", sid).order("name");
            setChapters((data || []) as Chapter[]);
        } catch (error) {
            console.error("Error fetching chapters:", error);
        }
    };

    const fetchTopics = async (cid: string) => {
        try {
            const { data } = await supabase.from("topics").select("*").eq("chapter_id", cid).order("name");
            setTopics((data || []) as Topic[]);
        } catch (error) {
            console.error("Error fetching topics:", error);
        }
    };

    const fetchQuestions = async () => {
        setLoading(true);
        try {
            let query = supabase
                .from("repository_questions")
                .select("*")
                .eq("is_tagged", activeTab === "tagged")
                .order("created_at", { ascending: false });

            if (activeTab === "tagged") {
                if (selectedSubject) query = query.eq("subject_id", selectedSubject);
                if (selectedChapter) query = query.eq("chapter_id", selectedChapter);
                if (selectedTopic) query = query.eq("topic_id", selectedTopic);
            }
            
            // Filter by status for both tagged and untagged
            if (selectedStatus) {
                if (selectedStatus === 'no_status') {
                    query = query.is('status', null);
                } else {
                    query = query.eq("status", selectedStatus);
                }
            }

            const { data, error } = await query;
            if (error) {
                console.error("Error fetching questions:", error);
                toast.error("Error fetching questions. Please ensure migrations are run.");
                setQuestions([]);
            } else {
                setQuestions(data || []);
            }
        } catch (error) {
            console.error("Error in fetchQuestions:", error);
            toast.error("Failed to load questions. Please check database setup.");
            setQuestions([]);
        } finally {
            setLoading(false);
        }
    };

    const clearFilters = () => {
        setSelectedSubject(undefined);
        setSelectedChapter(undefined);
        setSelectedTopic(undefined);
        setSelectedStatus(undefined);
    };

    const handleDeleteQuestion = async (id: string) => {
        if (!confirm("Are you sure you want to delete this question?")) return;

        const { error } = await supabase.from("repository_questions").delete().eq("id", id);
        if (error) {
            toast.error("Failed to delete question");
        } else {
            toast.success("Question deleted");
            setQuestions(questions.filter(q => q.id !== id));
        }
    };

    const handleApproveQuestion = async (question: Question) => {
        if (!question.subject_id || !question.chapter_id || !question.topic_id) {
            toast.error("Question must be fully tagged before approval");
            return;
        }

        if (!confirm("Approve this question and move it to the tagged repository?")) return;

        const { error } = await supabase
            .from("repository_questions")
            // @ts-ignore - Supabase types may not be up to date
            .update({
                is_tagged: true,
                status: null // Clear status when moving to tagged
            })
            .eq("id", question.id);

        if (error) {
            toast.error("Failed to approve question");
        } else {
            toast.success("Question approved and moved to tagged repository!");
            setQuestions(questions.filter(q => q.id !== question.id));
        }
    };

    return (
        <MainLayout>
            <div className="container py-8">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Question Repository</h1>
                    <p className="text-muted-foreground">
                        View and manage all tagged and untagged questions in the global repository.
                    </p>
                </div>

                <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "tagged" | "untagged")} className="space-y-6">
                    <TabsList className="grid w-full max-w-md grid-cols-2">
                        <TabsTrigger value="tagged" className="flex items-center gap-2">
                            <CheckCircle2 className="h-4 w-4" />
                            Tagged Questions
                        </TabsTrigger>
                        <TabsTrigger value="untagged" className="flex items-center gap-2">
                            <AlertCircle className="h-4 w-4" />
                            Untagged Questions
                        </TabsTrigger>
                    </TabsList>

                    {/* Filters for Tagged Questions */}
                    {activeTab === "tagged" && (
                        <Card className="border-2">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2 text-lg">
                                    <Filter className="h-5 w-5" />
                                    Filter Questions
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                <div className="space-y-2">
                                    <Label>Subject</Label>
                                    <Select value={selectedSubject} onValueChange={(val) => setSelectedSubject(val === "all" ? undefined : val)}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="All Subjects" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Subjects</SelectItem>
                                            {subjects.map(s => <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Chapter</Label>
                                    <Select value={selectedChapter} onValueChange={(val) => setSelectedChapter(val === "all" ? undefined : val)} disabled={!selectedSubject}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="All Chapters" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Chapters</SelectItem>
                                            {chapters.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Topic</Label>
                                    <Select value={selectedTopic} onValueChange={(val) => setSelectedTopic(val === "all" ? undefined : val)} disabled={!selectedChapter}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="All Topics" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Topics</SelectItem>
                                            {topics.map(t => <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Status</Label>
                                    <Select value={selectedStatus} onValueChange={(val) => setSelectedStatus(val === "all" ? undefined : val)}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="All Status" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Status</SelectItem>
                                            <SelectItem value="in_review">In Review</SelectItem>
                                            <SelectItem value="approved">Approved</SelectItem>
                                            <SelectItem value="rejected">Rejected</SelectItem>
                                            <SelectItem value="no_status">No Status</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="md:col-span-4 flex justify-end">
                                    <Button variant="outline" onClick={clearFilters}>
                                        Clear Filters
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Filters for Untagged Questions */}
                    {activeTab === "untagged" && (
                        <Card className="border-2">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2 text-lg">
                                    <Filter className="h-5 w-5" />
                                    Filter Questions
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Status</Label>
                                    <Select value={selectedStatus} onValueChange={(val) => setSelectedStatus(val === "all" ? undefined : val)}>
                                        <SelectTrigger className="max-w-xs">
                                            <SelectValue placeholder="All Status" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="all">All Status</SelectItem>
                                            <SelectItem value="in_review">In Review (Fully Tagged)</SelectItem>
                                            <SelectItem value="no_status">Needs Tagging</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="flex justify-end">
                                    <Button variant="outline" onClick={clearFilters}>
                                        Clear Filters
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    <TabsContent value={activeTab} className="mt-0">
                        <Card className="border-2">
                            <CardHeader className="border-b">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="flex items-center gap-2">
                                        <Database className="h-5 w-5" />
                                        {activeTab === "tagged" ? "Tagged Questions" : "Untagged Questions"}
                                    </CardTitle>
                                    <Badge variant="secondary" className="text-lg px-4 py-1">
                                        {questions.length}
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent className="p-0">
                                <ScrollArea className="h-[600px]">
                                    {loading ? (
                                        <div className="p-12 text-center text-muted-foreground">
                                            Loading questions...
                                        </div>
                                    ) : questions.length === 0 ? (
                                        <div className="p-12 text-center text-muted-foreground">
                                            <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-20" />
                                            <p>No {activeTab} questions found.</p>
                                        </div>
                                    ) : (
                                        <div className="divide-y">
                                            {questions.map((q, idx) => (
                                                <div key={q.id} className="p-6 hover:bg-accent/50 transition-colors group">
                                                    <div className="flex gap-4">
                                                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary">
                                                            {idx + 1}
                                                        </div>
                                                        <div className="flex-grow space-y-3">
                                                            <div className="flex justify-between items-start">
                                                                <div className="space-y-3 flex-grow pr-4">
                                                                    {q.image_url && (
                                                                        <div className="border rounded-md overflow-hidden bg-muted/20 w-fit">
                                                                            <img
                                                                                src={q.image_url}
                                                                                alt="Question"
                                                                                className="max-h-[200px] w-auto object-contain rounded-md"
                                                                            />
                                                                        </div>
                                                                    )}
                                                                    <p className="text-lg leading-relaxed">{q.question_text}</p>
                                                                </div>
                                                                <div className="flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                    {q.status === 'in_review' && (
                                                                        <Button
                                                                            variant="ghost"
                                                                            size="icon"
                                                                            onClick={() => handleApproveQuestion(q)}
                                                                            className="h-8 w-8 text-muted-foreground hover:text-green-600"
                                                                            title="Approve & Move to Tagged"
                                                                        >
                                                                            <Check className="h-4 w-4" />
                                                                        </Button>
                                                                    )}
                                                                    <Button
                                                                        variant="ghost"
                                                                        size="icon"
                                                                        onClick={() => setQuestionToEdit(q)}
                                                                        className="h-8 w-8 text-muted-foreground hover:text-primary"
                                                                        title="Edit"
                                                                    >
                                                                        <Pencil className="h-4 w-4" />
                                                                    </Button>
                                                                    <Button
                                                                        variant="ghost"
                                                                        size="icon"
                                                                        onClick={() => handleDeleteQuestion(q.id)}
                                                                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                                                                        title="Delete"
                                                                    >
                                                                        <Trash2 className="h-4 w-4" />
                                                                    </Button>
                                                                </div>
                                                            </div>

                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                                {q.options.map((opt: any, optIdx) => (
                                                                    <div
                                                                        key={optIdx}
                                                                        className={`flex gap-2 p-2 rounded border text-sm ${opt.id === q.correct_answer ? "bg-green-500/10 border-green-500/30" : "bg-card"
                                                                            }`}
                                                                    >
                                                                        <span className="font-bold text-primary">{opt.id}.</span>
                                                                        <span>{opt.text}</span>
                                                                    </div>
                                                                ))}
                                                            </div>

                                                            <div className="flex flex-wrap gap-2 pt-2">
                                                                {q.status && (
                                                                    <Badge 
                                                                        variant="outline" 
                                                                        className="bg-yellow-500/10 border-yellow-500/30 text-yellow-700 dark:text-yellow-400"
                                                                    >
                                                                        🔍 In Review (Ready to Approve)
                                                                    </Badge>
                                                                )}
                                                                {!q.status && activeTab === "untagged" && (
                                                                    <Badge 
                                                                        variant="outline" 
                                                                        className="bg-gray-500/10 border-gray-500/30"
                                                                    >
                                                                        ⚠️ Needs Tagging
                                                                    </Badge>
                                                                )}
                                                                {activeTab === "tagged" && (
                                                                    <>
                                                                        {q.subject_id && (
                                                                            <Badge variant="outline" className="bg-blue-500/10">
                                                                                <Tag className="h-3 w-3 mr-1" />
                                                                                {subjectMap[q.subject_id] || "Unknown Subject"}
                                                                            </Badge>
                                                                        )}
                                                                        {q.chapter_id && (
                                                                            <Badge variant="outline" className="bg-purple-500/10">
                                                                                {chapterMap[q.chapter_id] || "Unknown Chapter"}
                                                                            </Badge>
                                                                        )}
                                                                        {q.topic_id && (
                                                                            <Badge variant="outline" className="bg-green-500/10">
                                                                                {topicMap[q.topic_id] || "Unknown Topic"}
                                                                            </Badge>
                                                                        )}
                                                                    </>
                                                                )}
                                                                {q.difficulty_level && (
                                                                    <Badge variant="secondary">
                                                                        {q.difficulty_level.toUpperCase()}
                                                                    </Badge>
                                                                )}
                                                                {q.correct_answer && (
                                                                    <Badge variant="outline" className="bg-green-500/10">
                                                                        Ans: {q.correct_answer}
                                                                    </Badge>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </ScrollArea>
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>

                <QuestionEditDialog
                    open={!!questionToEdit}
                    onOpenChange={(open) => !open && setQuestionToEdit(null)}
                    question={questionToEdit}
                    onQuestionUpdated={() => {
                        fetchQuestions();
                        setQuestionToEdit(null);
                    }}
                />
            </div>
        </MainLayout>
    );
};

export default AdminRepository;
