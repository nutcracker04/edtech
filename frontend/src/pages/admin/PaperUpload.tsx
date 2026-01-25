import { useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { FileUploader } from '@/components/upload/FileUploader';
import { uploadService } from '@/services/uploadService';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useNavigate } from 'react-router-dom';
import { FileUp, CheckCircle2, ArrowRight, Loader2, PenTool } from 'lucide-react';
import { ManualQuestionCreator } from '@/components/admin/ManualQuestionCreator';

const AdminPaperUpload = () => {
    const navigate = useNavigate();
    const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'error'>('idle');
    const [uploadProgress, setUploadProgress] = useState(0);
    const [error, setError] = useState<string>('');
    const [lastUploadId, setLastUploadId] = useState<string | null>(null);

    const handleFileSelect = async (file: File) => {
        setUploadStatus('uploading');
        setUploadProgress(20);
        setError('');

        try {
            const uploadResponse = await uploadService.uploadTestPaper(file);
            setLastUploadId(uploadResponse.id);
            setUploadProgress(50);
            setUploadStatus('processing');

            // Poll for completion
            const poll = async () => {
                try {
                    const status = await uploadService.getUploadStatus(uploadResponse.id);
                    if (status.status === 'completed') {
                        setUploadProgress(100);
                        setUploadStatus('completed');

                        // Auto-import into repository as untagged
                        const token = await (async () => {
                            const { data: { session } } = await (await import('@/integrations/supabase/client')).supabase.auth.getSession();
                            return session?.access_token;
                        })();

                        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
                        await fetch(`${API_BASE_URL}/api/repository/questions/bulk-import-from-upload/${uploadResponse.id}`, {
                            method: 'POST',
                            headers: { 'Authorization': `Bearer ${token}` }
                        });

                        toast.success('Paper processed and imported to repository!');
                    } else if (status.status === 'failed') {
                        throw new Error(status.error_message || 'Processing failed');
                    } else {
                        setUploadProgress(prev => Math.min(prev + 5, 95));
                        setTimeout(poll, 2000);
                    }
                } catch (err: any) {
                    setError(err.message);
                    setUploadStatus('error');
                }
            };

            setTimeout(poll, 1000);
        } catch (err: any) {
            setError(err.message);
            setUploadStatus('error');
            toast.error('Upload failed');
        }
    };

    return (
        <MainLayout>
            <div className="container max-w-4xl py-8">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">Add Questions to Repository</h1>
                    <p className="text-muted-foreground">
                        Upload papers to extract questions or create questions manually.
                    </p>
                </div>

                <Tabs defaultValue="upload" className="space-y-6">
                    <TabsList className="grid w-full max-w-md grid-cols-2">
                        <TabsTrigger value="upload" className="flex items-center gap-2">
                            <FileUp className="h-4 w-4" />
                            Upload Paper
                        </TabsTrigger>
                        <TabsTrigger value="manual" className="flex items-center gap-2">
                            <PenTool className="h-4 w-4" />
                            Create Manually
                        </TabsTrigger>
                    </TabsList>

                    {/* Upload Tab */}
                    <TabsContent value="upload" className="space-y-8">
                        {uploadStatus !== 'completed' ? (
                            <Card className="border-2 border-dashed border-border/50">
                                <CardContent className="pt-6">
                                    <FileUploader
                                        onFileSelect={handleFileSelect}
                                        loading={uploadStatus === 'uploading' || uploadStatus === 'processing'}
                                        progress={uploadProgress}
                                        status={uploadStatus}
                                        error={error}
                                        label="Drop test paper (PDF/JPG) here"
                                    />
                                </CardContent>
                            </Card>
                        ) : (
                            <Card className="border-2 border-primary/20 bg-primary/5">
                                <CardHeader>
                                    <div className="h-12 w-12 rounded-full bg-primary/20 flex items-center justify-center mb-4">
                                        <CheckCircle2 className="h-6 w-6 text-primary" />
                                    </div>
                                    <CardTitle className="text-2xl">Upload Complete!</CardTitle>
                                    <CardDescription>
                                        Questions have been extracted and added to the untagged repository.
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="flex gap-4">
                                    <Button onClick={() => setUploadStatus('idle')} variant="outline">
                                        <FileUp className="mr-2 h-4 w-4" />
                                        Upload Another
                                    </Button>
                                    <Button onClick={() => navigate('/admin/tagging')}>
                                        Go to Tagging
                                        <ArrowRight className="ml-2 h-4 w-4" />
                                    </Button>
                                </CardContent>
                            </Card>
                        )}

                        <Card>
                            <CardHeader>
                                <CardTitle className="text-lg">What happens next?</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4 text-sm text-muted-foreground">
                                <div className="flex gap-3">
                                    <div className="h-6 w-6 rounded-full bg-accent flex items-center justify-center shrink-0">1</div>
                                    <p>System uses AI OCR to extract image/text from the uploaded paper.</p>
                                </div>
                                <div className="flex gap-3">
                                    <div className="h-6 w-6 rounded-full bg-accent flex items-center justify-center shrink-0">2</div>
                                    <p>Questions are stored in the <strong>Untagged Repository</strong>.</p>
                                </div>
                                <div className="flex gap-3">
                                    <div className="h-6 w-6 rounded-full bg-accent flex items-center justify-center shrink-0">3</div>
                                    <p>You can then go to the <strong>Tagging</strong> section to assign Subject, Chapter, and Topic.</p>
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    {/* Manual Creation Tab */}
                    <TabsContent value="manual">
                        <ManualQuestionCreator
                            onQuestionCreated={() => {
                                toast.success("Question saved! Go to tagging to assign Subject, Chapter, and Topic.");
                            }}
                        />
                    </TabsContent>
                </Tabs>
            </div>
        </MainLayout>
    );
};

export default AdminPaperUpload;
