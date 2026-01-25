import { useState, useEffect } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Search, Plus, Trash2, ChevronRight, BookOpen, GraduationCap, Layers } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

interface Subject {
    id: string;
    name: string;
}

interface Chapter {
    id: string;
    name: string;
    subject_id: string;
}

interface Topic {
    id: string;
    name: string;
    chapter_id: string;
}

const HierarchyManager = () => {
    const [subjects, setSubjects] = useState<Subject[]>([]);
    const [chapters, setChapters] = useState<Chapter[]>([]);
    const [topics, setTopics] = useState<Topic[]>([]);

    const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
    const [selectedChapter, setSelectedChapter] = useState<string | null>(null);

    const [newItemName, setNewItemName] = useState("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchSubjects();
    }, []);

    useEffect(() => {
        if (selectedSubject) {
            fetchChapters(selectedSubject);
            setSelectedChapter(null);
            setTopics([]);
        }
    }, [selectedSubject]);

    useEffect(() => {
        if (selectedChapter) {
            fetchTopics(selectedChapter);
        }
    }, [selectedChapter]);

    const fetchSubjects = async () => {
        const { data, error } = await supabase.from("subjects").select("*").order("name");
        if (error) toast.error("Error fetching subjects");
        else setSubjects(data || []);
    };

    const fetchChapters = async (subjectId: string) => {
        const { data, error } = await supabase
            .from("chapters")
            .select("*")
            .eq("subject_id", subjectId)
            .order("name");
        if (error) toast.error("Error fetching chapters");
        else setChapters(data || []);
    };

    const fetchTopics = async (chapterId: string) => {
        const { data, error } = await supabase
            .from("topics")
            .select("*")
            .eq("chapter_id", chapterId)
            .order("name");
        if (error) toast.error("Error fetching topics");
        else setTopics(data || []);
    };

    const handleAddSubject = async () => {
        if (!newItemName) return;
        setLoading(true);
        const { data, error } = await supabase.from("subjects").insert([{ name: newItemName }] as any).select();
        if (error) toast.error("Error adding subject");
        else {
            setSubjects([...subjects, data[0]]);
            setNewItemName("");
            toast.success("Subject added");
        }
        setLoading(false);
    };

    const handleAddChapter = async () => {
        if (!newItemName || !selectedSubject) return;
        setLoading(true);
        const { data, error } = await supabase
            .from("chapters")
            .insert([{ name: newItemName, subject_id: selectedSubject }] as any)
            .select();
        if (error) toast.error("Error adding chapter");
        else {
            setChapters([...chapters, data[0]]);
            setNewItemName("");
            toast.success("Chapter added");
        }
        setLoading(false);
    };

    const handleAddTopic = async () => {
        if (!newItemName || !selectedChapter) return;
        setLoading(true);
        const { data, error } = await supabase
            .from("topics")
            .insert([{ name: newItemName, chapter_id: selectedChapter }] as any)
            .select();
        if (error) toast.error("Error adding topic");
        else {
            setTopics([...topics, data[0]]);
            setNewItemName("");
            toast.success("Topic added");
        }
        setLoading(false);
    };

    const handleDelete = async (table: string, id: string) => {
        const { error } = await supabase.from(table).delete().eq("id", id);
        if (error) toast.error(`Error deleting from ${table}`);
        else {
            if (table === "subjects") {
                setSubjects(subjects.filter((s) => s.id !== id));
                if (selectedSubject === id) setSelectedSubject(null);
            } else if (table === "chapters") {
                setChapters(chapters.filter((c) => c.id !== id));
                if (selectedChapter === id) setSelectedChapter(null);
            } else if (table === "topics") {
                setTopics(topics.filter((t) => t.id !== id));
            }
            toast.success("Item deleted");
        }
    };

    return (
        <MainLayout>
            <div className="container py-8">
                <div className="mb-8 flex justify-between items-end">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Hierarchy Manager</h1>
                        <p className="text-muted-foreground">Define Subjects, Chapters, and Topics.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Subjects Column */}
                    <Card className="border-2 border-border/50">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b">
                            <div className="flex items-center gap-2">
                                <GraduationCap className="h-5 w-5 text-blue-500" />
                                <CardTitle className="text-lg">Subjects</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="pt-6">
                            <div className="flex gap-2 mb-4">
                                <Input
                                    placeholder="New Subject..."
                                    value={newItemName}
                                    onChange={(e) => setNewItemName(e.target.value)}
                                    onKeyDown={(e) => e.key === "Enter" && handleAddSubject()}
                                />
                                <Button size="icon" onClick={handleAddSubject} disabled={loading}>
                                    <Plus className="h-4 w-4" />
                                </Button>
                            </div>
                            <div className="space-y-1">
                                {subjects.map((subject) => (
                                    <div
                                        key={subject.id}
                                        className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${selectedSubject === subject.id ? "bg-blue-500/20 text-blue-400" : "hover:bg-accent"
                                            }`}
                                        onClick={() => setSelectedSubject(subject.id)}
                                    >
                                        <span className="font-medium">{subject.name}</span>
                                        <div className="flex items-center gap-1">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-7 w-7 text-muted-foreground hover:text-destructive"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDelete("subjects", subject.id);
                                                }}
                                            >
                                                <Trash2 className="h-3.5 w-3.5" />
                                            </Button>
                                            <ChevronRight className="h-4 w-4" />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    {/* Chapters Column */}
                    <Card className="border-2 border-border/50">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b">
                            <div className="flex items-center gap-2">
                                <BookOpen className="h-5 w-5 text-purple-500" />
                                <CardTitle className="text-lg">Chapters</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="pt-6">
                            {!selectedSubject ? (
                                <div className="text-center py-8 text-muted-foreground">Select a subject first</div>
                            ) : (
                                <>
                                    <div className="flex gap-2 mb-4">
                                        <Input
                                            placeholder="New Chapter..."
                                            value={newItemName}
                                            onChange={(e) => setNewItemName(e.target.value)}
                                            onKeyDown={(e) => e.key === "Enter" && handleAddChapter()}
                                        />
                                        <Button size="icon" onClick={handleAddChapter} disabled={loading}>
                                            <Plus className="h-4 w-4" />
                                        </Button>
                                    </div>
                                    <div className="space-y-1">
                                        {chapters.map((chapter) => (
                                            <div
                                                key={chapter.id}
                                                className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${selectedChapter === chapter.id ? "bg-purple-500/20 text-purple-400" : "hover:bg-accent"
                                                    }`}
                                                onClick={() => setSelectedChapter(chapter.id)}
                                            >
                                                <span className="font-medium">{chapter.name}</span>
                                                <div className="flex items-center gap-1">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-7 w-7 text-muted-foreground hover:text-destructive"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDelete("chapters", chapter.id);
                                                        }}
                                                    >
                                                        <Trash2 className="h-3.5 w-3.5" />
                                                    </Button>
                                                    <ChevronRight className="h-4 w-4" />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </>
                            )}
                        </CardContent>
                    </Card>

                    {/* Topics Column */}
                    <Card className="border-2 border-border/50">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b">
                            <div className="flex items-center gap-2">
                                <Layers className="h-5 w-5 text-emerald-500" />
                                <CardTitle className="text-lg">Topics</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="pt-6">
                            {!selectedChapter ? (
                                <div className="text-center py-8 text-muted-foreground">Select a chapter first</div>
                            ) : (
                                <>
                                    <div className="flex gap-2 mb-4">
                                        <Input
                                            placeholder="New Topic..."
                                            value={newItemName}
                                            onChange={(e) => setNewItemName(e.target.value)}
                                            onKeyDown={(e) => e.key === "Enter" && handleAddTopic()}
                                        />
                                        <Button size="icon" onClick={handleAddTopic} disabled={loading}>
                                            <Plus className="h-4 w-4" />
                                        </Button>
                                    </div>
                                    <div className="space-y-1">
                                        {topics.map((topic) => (
                                            <div
                                                key={topic.id}
                                                className="flex items-center justify-between p-2 rounded-lg hover:bg-accent group transition-colors"
                                            >
                                                <span className="font-medium">{topic.name}</span>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-7 w-7 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100"
                                                    onClick={() => handleDelete("topics", topic.id)}
                                                >
                                                    <Trash2 className="h-3.5 w-3.5" />
                                                </Button>
                                            </div>
                                        ))}
                                    </div>
                                </>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </MainLayout>
    );
};

export default HierarchyManager;
