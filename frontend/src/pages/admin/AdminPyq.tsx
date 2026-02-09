
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { FileUploader } from '@/components/upload/FileUploader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { supabase } from '@/integrations/supabase/client';
import { Loader2, CheckCircle2, AlertTriangle, Calendar as CalendarIcon } from 'lucide-react';
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { Calendar } from "@/components/ui/calendar";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";

interface PyqPaper {
    id: string;
    exam_type: string;
    exam_date: string;
    exam_session: string;
    processing_status: 'pending' | 'processing' | 'completed' | 'failed';
    total_questions: number;
    created_at: string;
}

const AdminPyq = () => {
    const navigate = useNavigate();
    const [papers, setPapers] = useState<PyqPaper[]>([]);
    const [uploading, setUploading] = useState(false);

    // Form State
    const [examType, setExamType] = useState('');
    const [date, setDate] = useState<Date>();
    const [examSession, setExamSession] = useState('');

    useEffect(() => {
        fetchPapers();

        // Poll for updates if any are processing
        const interval = setInterval(() => {
            fetchPapers();
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchPapers = async () => {
        const { data } = await supabase.from('pyq_papers').select('*').order('created_at', { ascending: false });
        if (data) setPapers(data as any);
    };

    const handleFileSelect = async (file: File) => {
        if (!examType || !date || !examSession) {
            toast.error("Please fill in all exam details first.");
            return;
        }

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('exam_type', examType);
        formData.append('exam_date', format(date, "yyyy-MM-dd"));
        formData.append('exam_session', examSession);

        try {
            const token = (await supabase.auth.getSession()).data.session?.access_token;
            const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

            const res = await fetch(`${API_BASE_URL}/api/pyq/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!res.ok) throw new Error('Upload failed');

            toast.success("Paper uploaded! Processing in background.");
            fetchPapers();
            // Reset form
            setExamType('');
            setDate(undefined);
            setExamSession('');

        } catch (e) {
            toast.error("Failed to upload paper.");
        } finally {
            setUploading(false);
        }
    };

    return (
        <MainLayout>
            <div className="container py-8 max-w-6xl">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold">PYQ Management</h1>
                    <p className="text-muted-foreground">Upload and manage Previous Year Question papers.</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Upload Section */}
                    <div className="lg:col-span-1 space-y-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Upload New Paper</CardTitle>
                                <CardDescription>System will extract questions and images.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Exam Type</Label>
                                    <Select value={examType} onValueChange={setExamType}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select type" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="JEE Main">JEE Main</SelectItem>
                                            <SelectItem value="JEE Advanced">JEE Advanced</SelectItem>
                                            <SelectItem value="NEET">NEET</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div className="space-y-2 flex flex-col">
                                    <Label>Date</Label>
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <Button
                                                variant={"outline"}
                                                className={cn(
                                                    "w-full pl-3 text-left font-normal",
                                                    !date && "text-muted-foreground"
                                                )}
                                            >
                                                {date ? (
                                                    format(date, "PPP")
                                                ) : (
                                                    <span>Pick a date</span>
                                                )}
                                                <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                                            </Button>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-auto p-0" align="start">
                                            <Calendar
                                                mode="single"
                                                selected={date}
                                                onSelect={setDate}
                                                disabled={(date) =>
                                                    date > new Date() || date < new Date("1900-01-01")
                                                }
                                                initialFocus
                                                captionLayout="dropdown-buttons"
                                                fromYear={2000}
                                                toYear={new Date().getFullYear()}
                                            />
                                        </PopoverContent>
                                    </Popover>
                                </div>

                                <div className="space-y-2">
                                    <Label>Session</Label>
                                    <Select value={examSession} onValueChange={setExamSession}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select session" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="Morning">Morning</SelectItem>
                                            <SelectItem value="Evening">Evening</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <FileUploader
                                    onFileSelect={handleFileSelect}
                                    loading={uploading}
                                    label="Drop PDF Here"
                                    accept="application/pdf"
                                />
                            </CardContent>
                        </Card>
                    </div>

                    {/* Repository List */}
                    <div className="lg:col-span-2">
                        <Card>
                            <CardHeader>
                                <CardTitle>Repository</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {papers.map(paper => (
                                        <div key={paper.id} className="flex items-center justify-between p-4 border rounded-lg bg-card">
                                            <div>
                                                <h3 className="font-semibold">{paper.exam_type}</h3>
                                                <p className="text-sm text-muted-foreground">
                                                    {paper.exam_date} • {paper.exam_session}
                                                </p>
                                            </div>
                                            <div className="flex items-center gap-4">
                                                <div className="text-right">
                                                    <div className="text-sm font-medium">
                                                        {paper.processing_status === 'completed' ? (
                                                            <span className="text-green-600 flex items-center gap-1">
                                                                <CheckCircle2 className="w-3 h-3" /> Completed
                                                            </span>
                                                        ) : paper.processing_status === 'failed' ? (
                                                            <span className="text-red-600 flex items-center gap-1">
                                                                <AlertTriangle className="w-3 h-3" /> Failed
                                                            </span>
                                                        ) : (
                                                            <span className="text-blue-600 flex items-center gap-1">
                                                                <Loader2 className="w-3 h-3 animate-spin" /> Processing
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-xs text-muted-foreground">{paper.total_questions} questions</p>
                                                </div>
                                                <Button variant="outline" size="sm" onClick={() => navigate(`/admin/pyq/${paper.id}`)}>
                                                    View
                                                </Button>
                                            </div>
                                        </div>
                                    ))}
                                    {papers.length === 0 && (
                                        <div className="text-center py-8 text-muted-foreground">
                                            No papers uploaded yet.
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </MainLayout>
    );
};

export default AdminPyq;
