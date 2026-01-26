import { useState, useEffect } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tag, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

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

const QuestionTagging = () => {
    const [questions, setQuestions] = useState<Question[]>([]);
    const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);

    const [subjects, setSubjects] = useState<Subject[]>([]);
    const [chapters, setChapters] = useState<Chapter[]>([]);
    const [topics, setTopics] = useState<Topic[]>([]);

    const [selectedSubject, setSelectedSubject] = useState<string>("");
    const [selectedChapter, setSelectedChapter] = useState<string>("");
    const [selectedTopic, setSelectedTopic] = useState<string>("");
    const [difficulty, setDifficulty] = useState<string>("medium");

    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchUntaggedQuestions();
        fetchSubjects();
    }, []);

    useEffect(() => {
        if (selectedSubject) {
            fetchChapters(selectedSubject);
            setSelectedChapter("");
            setTopics([]);
        }
    }, [selectedSubject]);

    useEffect(() => {
        if (selectedChapter) {
            fetchTopics(selectedChapter);
            setSelectedTopic("");
        }
    }, [selectedChapter]);

    const fetchUntaggedQuestions = async () => {
        const { data, error } = await supabase
            .from("repository_questions")
            .select("*")
            .eq("is_tagged", false)
            .limit(50);

        if (error) toast.error("Error fetching questions");
        else {
            setQuestions(data || []);
            if (data && data.length > 0) setCurrentQuestion(data[0]);
        }
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

    const handleTagQuestion = async () => {
        if (!currentQuestion || !selectedSubject || !selectedChapter || !selectedTopic) {
            toast.error("Please select Subject, Chapter and Topic");
            return;
        }

        setLoading(true);
        const { error } = await supabase
            .from("repository_questions")
            .update({
                subject_id: selectedSubject,
                chapter_id: selectedChapter,
                topic_id: selectedTopic,
                difficulty_level: difficulty,
                is_tagged: true,
                updated_at: new Date().toISOString()
            } as never)
            .eq("id", currentQuestion.id);

        if (error) {
            toast.error("Error tagging question");
        } else {
            toast.success("Question tagged successfully");
            const updatedQuestions = questions.filter(q => q.id !== currentQuestion.id);
            setQuestions(updatedQuestions);
            setCurrentQuestion(updatedQuestions[0] || null);
            // Reset selections
            // setSelectedSubject(""); // Keep subject if tagging multiple similar questions
        }
        setLoading(false);
    };

    return (
        <MainLayout>
            <div className="container py-8 h-[calc(100vh-64px)] overflow-hidden">
                <div className="mb-6">
                    <h1 className="text-3xl font-bold mb-2">Question Tagging</h1>
                    <p className="text-muted-foreground">Map extracted questions to the SCT hierarchy.</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full pb-8">
                    {/* Questions List Sidebar */}
                    <Card className="lg:col-span-3 border-2 border-border/50 h-full flex flex-col">
                        <CardHeader className="pb-3 border-b">
                            <CardTitle className="text-lg flex items-center justify-between">
                                Untagged
                                <Badge variant="secondary">{questions.length}</Badge>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0 flex-grow overflow-hidden">
                            <ScrollArea className="h-full">
                                <div className="divide-y">
                                    {questions.map((q) => (
                                        <button
                                            key={q.id}
                                            className={`w-full text-left p-4 hover:bg-accent transition-colors ${currentQuestion?.id === q.id ? "bg-accent border-r-4 border-primary" : ""
                                                }`}
                                            onClick={() => setCurrentQuestion(q)}
                                        >
                                            <p className="text-sm font-medium line-clamp-2">{q.question_text}</p>
                                        </button>
                                    ))}
                                    {questions.length === 0 && (
                                        <div className="p-8 text-center text-muted-foreground italic">
                                            No untagged questions
                                        </div>
                                    )}
                                </div>
                            </ScrollArea>
                        </CardContent>
                    </Card>

                    {/* Tagging Workspace */}
                    <div className="lg:col-span-9 grid grid-cols-1 lg:grid-cols-2 gap-6 h-full overflow-hidden">
                        {/* Question Preview */}
                        <Card className="border-2 border-border/50 h-full flex flex-col overflow-hidden">
                            <CardHeader className="pb-3 border-b">
                                <CardTitle>Question Preview</CardTitle>
                            </CardHeader>
                            <CardContent className="flex-grow overflow-hidden pt-6">
                                {currentQuestion ? (
                                    <ScrollArea className="h-full pr-4">
                                        <div className="space-y-6">
                                            {currentQuestion.image_url && (
                                                <div className="border rounded-md overflow-hidden bg-muted/20 flex justify-center p-2">
                                                    <img
                                                        src={currentQuestion.image_url}
                                                        alt="Question"
                                                        className="max-h-[300px] w-auto object-contain rounded-md"
                                                    />
                                                </div>
                                            )}
                                            <div className="p-4 bg-accent/30 rounded-lg border">
                                                <p className="text-lg leading-relaxed">{currentQuestion.question_text}</p>
                                            </div>
                                            <div className="grid grid-cols-1 gap-3">
                                                {currentQuestion.options.map((opt: any, idx) => (
                                                    <div key={idx} className="flex gap-4 p-3 rounded-md border bg-card">
                                                        <span className="font-bold text-primary">{opt.id}</span>
                                                        <span>{opt.text}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </ScrollArea>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                                        <AlertCircle className="h-12 w-12 mb-4 opacity-20" />
                                        <p>Select a question to tag</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Tag Selection */}
                        <Card className="border-2 border-border/50 h-full flex flex-col overflow-hidden">
                            <CardHeader className="pb-3 border-b">
                                <CardTitle>Assign Tags</CardTitle>
                                <CardDescription>Select Subject, Chapter, and Topic</CardDescription>
                            </CardHeader>
                            <CardContent className="pt-6 space-y-6">
                                <div className="space-y-2">
                                    <Label>Subject</Label>
                                    <Select value={selectedSubject} onValueChange={setSelectedSubject}>
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
                                        onValueChange={setSelectedChapter}
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
                                    <Label>Difficulty Level</Label>
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

                                <div className="pt-4 mt-auto">
                                    <Button
                                        className="w-full h-12 text-lg"
                                        onClick={handleTagQuestion}
                                        disabled={loading || !currentQuestion}
                                    >
                                        {loading ? (
                                            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                        ) : (
                                            <Tag className="mr-2 h-5 w-5" />
                                        )}
                                        Tag & Move to Next
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </MainLayout>
    );
};

export default QuestionTagging;
