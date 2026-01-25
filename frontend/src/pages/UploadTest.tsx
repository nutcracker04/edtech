import { useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { FileUploader } from '@/components/upload/FileUploader';
import { QuestionMapper } from '@/components/upload/QuestionMapper';
import { AnswerMapper } from '@/components/upload/AnswerMapper';
import { UploadAnalysis } from '@/components/upload/UploadAnalysis';
import { uploadService } from '@/services/uploadService';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';

type Step = 'upload' | 'review' | 'answer' | 'analysis';

interface ExtractedQuestion {
  question_number: number;
  question_text: string;
  options: Array<{ id: string; text: string }>;
  confidence: number;
  subject?: string;
  topic?: string;
}

export default function UploadTest() {
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [questions, setQuestions] = useState<ExtractedQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'error'>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string>('');

  const handleFileSelect = async (file: File) => {
    setUploadStatus('uploading');
    setUploadProgress(20);
    setError('');

    try {
      // Upload file
      const uploadResponse = await uploadService.uploadTestPaper(file);
      setUploadId(uploadResponse.id);
      setUploadProgress(50);
      setUploadStatus('processing');

      // Poll for status
      const pollStatus = async () => {
        try {
          const statusResponse = await uploadService.getUploadStatus(uploadResponse.id);

          if (statusResponse.status === 'completed') {
            setUploadProgress(100);
            setUploadStatus('completed');

            if (statusResponse.extracted_questions) {
              setQuestions(statusResponse.extracted_questions);
              setTimeout(() => setCurrentStep('review'), 500);
              toast.success('Questions extracted successfully!');
            }
          } else if (statusResponse.status === 'failed') {
            throw new Error(statusResponse.error_message || 'Processing failed');
          } else {
            // Still processing
            setUploadProgress(70);
            setTimeout(pollStatus, 2000);
          }
        } catch (err: any) {
          setError(err.message);
          setUploadStatus('error');
          toast.error(err.message);
        }
      };

      setTimeout(pollStatus, 1000);
    } catch (err: any) {
      setError(err.message);
      setUploadStatus('error');
      toast.error('Upload failed: ' + err.message);
    }
  };

  const handleQuestionsConfirm = () => {
    if (questions.length === 0) {
      toast.error('No questions to confirm');
      return;
    }
    setCurrentStep('answer');
    toast.success('Moving to answer mapping');
  };

  const handleAnswersSubmit = async () => {
    if (!uploadId) {
      toast.error('No upload ID found');
      return;
    }

    if (Object.keys(answers).length < questions.length) {
      toast.error('Please answer all questions');
      return;
    }

    try {
      toast.loading('Submitting answers...');

      // Prepare questions with correct format
      const formattedQuestions = questions.map((q) => ({
        id: `q-${q.question_number}`,
        question: q.question_text,
        options: q.options,
        correct_answer: '', // Will be determined by comparison
        explanation: '',
        difficulty: 'medium',
        topic: q.topic || '',
        subject: q.subject || 'mathematics',
        grade_level: ['11', '12'],
        answer_type: 'single_choice',
      }));

      const result = await uploadService.confirmQuestions(
        uploadId,
        formattedQuestions,
        answers
      );

      // Simulate analysis result (in real app, this would come from backend)
      const correct = Object.keys(answers).filter((qNum) => {
        // This is a placeholder - real implementation would check against correct answers
        return Math.random() > 0.3; // 70% correct for demo
      }).length;

      setAnalysisResult({
        test_id: result.test_id,
        total_questions: questions.length,
        correct_answers: correct,
        incorrect_answers: questions.length - correct,
        unanswered: 0,
        score: Math.round((correct / questions.length) * 100),
      });

      setCurrentStep('analysis');
      toast.dismiss();
      toast.success('Test submitted successfully!');
    } catch (err: any) {
      toast.dismiss();
      toast.error('Submission failed: ' + err.message);
    }
  };

  const handleReset = () => {
    setCurrentStep('upload');
    setUploadId(null);
    setQuestions([]);
    setAnswers({});
    setAnalysisResult(null);
    setUploadStatus('idle');
    setUploadProgress(0);
    setError('');
  };

  const steps = [
    { id: 'upload', label: 'Upload', completed: currentStep !== 'upload' },
    { id: 'review', label: 'Review', completed: currentStep === 'answer' || currentStep === 'analysis' },
    { id: 'answer', label: 'Answer', completed: currentStep === 'analysis' },
    { id: 'analysis', label: 'Analysis', completed: false },
  ];

  return (
    <MainLayout>
      <div className="container max-w-6xl py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Upload Test</h1>
          <p className="text-muted-foreground">
            Upload your test paper and get instant analysis with AI-powered OCR
          </p>
        </div>

        {/* Progress Stepper */}
        <Card className="mb-8">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center flex-1">
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center border-2 ${step.completed
                          ? 'bg-primary border-primary text-primary-foreground'
                          : currentStep === step.id
                            ? 'border-primary text-primary'
                            : 'border-muted text-muted-foreground'
                        }`}
                    >
                      {index + 1}
                    </div>
                    <span className="text-sm mt-2">{step.label}</span>
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`flex-1 h-0.5 mx-4 ${step.completed ? 'bg-primary' : 'bg-muted'}`} />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Step Content */}
        <div>
          {currentStep === 'upload' && (
            <FileUploader
              onFileSelect={handleFileSelect}
              loading={uploadStatus === 'uploading' || uploadStatus === 'processing'}
              progress={uploadProgress}
              status={uploadStatus}
              error={error}
              label="Upload Test Paper"
              accept="image/*,.pdf"
            />
          )}

          {currentStep === 'review' && (
            <QuestionMapper
              questions={questions}
              onQuestionsChange={setQuestions}
              onConfirm={handleQuestionsConfirm}
              onCancel={handleReset}
            />
          )}

          {currentStep === 'answer' && (
            <AnswerMapper
              questions={questions}
              answers={answers}
              onAnswersChange={setAnswers}
              onSubmit={handleAnswersSubmit}
              onBack={() => setCurrentStep('review')}
            />
          )}

          {currentStep === 'analysis' && analysisResult && (
            <UploadAnalysis
              result={analysisResult}
              onNewUpload={handleReset}
            />
          )}
        </div>
      </div>
    </MainLayout>
  );
}
