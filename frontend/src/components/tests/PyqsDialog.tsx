import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { ChevronRight, BookOpen, GraduationCap, ArrowLeft } from "lucide-react";

interface PyqsDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

type Step = 'exam-selection' | 'type-selection' | 'details-selection';
type ExamType = 'mains' | 'advanced';
type TestType = 'full' | 'subject' | 'chapter';

export function PyqsDialog({ open, onOpenChange }: PyqsDialogProps) {
    const [step, setStep] = useState<Step>('exam-selection');
    const [exam, setExam] = useState<ExamType | null>(null);
    const [testType, setTestType] = useState<TestType | null>(null);

    // Form states
    const [year, setYear] = useState<string>("");
    const [session, setSession] = useState<string>("");
    const [subject, setSubject] = useState<string>("");
    const [chapter, setChapter] = useState<string>("");

    const resetState = () => {
        setStep('exam-selection');
        setExam(null);
        setTestType(null);
        setYear("");
        setSession("");
        setSubject("");
        setChapter("");
    };

    const handleOpenChange = (newOpen: boolean) => {
        if (!newOpen) {
            resetState();
        }
        onOpenChange(newOpen);
    };

    const handleExamSelect = (selectedExam: ExamType) => {
        setExam(selectedExam);
        setStep('type-selection');
    };

    const handleBack = () => {
        if (step === 'type-selection') {
            setStep('exam-selection');
            setExam(null);
        } else if (step === 'details-selection') {
            setStep('type-selection');
            // Keep testType for now, or reset it? 
            // User might want to change type, so going back to type selection is correct.
        }
    };

    const handleNextToDetails = () => {
        if (testType) {
            setStep('details-selection');
        }
    };

    const handleStartTest = () => {
        console.log("Starting test with:", { exam, testType, year, session, subject, chapter });
        // TODO: Implement navigation to test or API call
        handleOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <div className="flex items-center gap-2">
                        {step !== 'exam-selection' && (
                            <Button variant="ghost" size="icon" className="h-8 w-8 -ml-2" onClick={handleBack}>
                                <ArrowLeft className="h-4 w-4" />
                            </Button>
                        )}
                        <DialogTitle>
                            {step === 'exam-selection' && "Select Exam"}
                            {step === 'type-selection' && `Select ${exam === 'mains' ? 'JEE Mains' : 'JEE Advanced'} Test Type`}
                            {step === 'details-selection' && "Configure Test"}
                        </DialogTitle>
                    </div>
                </DialogHeader>

                <div className="py-4">
                    {step === 'exam-selection' && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <Card
                                className="cursor-pointer hover:border-primary transition-colors hover:bg-muted/50"
                                onClick={() => handleExamSelect('mains')}
                            >
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <GraduationCap className="h-5 w-5 text-blue-500" />
                                        JEE Mains
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">
                                        Paper 1 & 2 previous year questions with detailed solutions.
                                    </p>
                                </CardContent>
                            </Card>

                            <Card
                                className="cursor-pointer hover:border-primary transition-colors hover:bg-muted/50"
                                onClick={() => handleExamSelect('advanced')}
                            >
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <BookOpen className="h-5 w-5 text-purple-500" />
                                        JEE Advanced
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <p className="text-sm text-muted-foreground">
                                        Advanced level problems from previous years papers.
                                    </p>
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {step === 'type-selection' && (
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <Label>Select Test Type</Label>
                                <Select value={testType || ""} onValueChange={(val) => setTestType(val as TestType)}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Choose a test type" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="full">Full Syllabus Mock Test</SelectItem>
                                        <SelectItem value="subject">Subject Wise Test</SelectItem>
                                        <SelectItem value="chapter">Chapter Wise Test</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="flex justify-end pt-4">
                                <Button onClick={handleNextToDetails} disabled={!testType}>
                                    Next
                                    <ChevronRight className="ml-2 h-4 w-4" />
                                </Button>
                            </div>
                        </div>
                    )}

                    {step === 'details-selection' && (
                        <div className="space-y-4">
                            {testType === 'full' && (
                                <>
                                    <div className="space-y-2">
                                        <Label>Select Year</Label>
                                        <Select value={year} onValueChange={setYear}>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Year" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                {['2024', '2023', '2022', '2021', '2020'].map(y => (
                                                    <SelectItem key={y} value={y}>{y}</SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Select Session</Label>
                                        <Select value={session} onValueChange={setSession}>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Session" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="jan">January Session</SelectItem>
                                                <SelectItem value="apr">April Session</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </>
                            )}

                            {testType === 'subject' && (
                                <div className="space-y-2">
                                    <Label>Select Subject</Label>
                                    <Select value={subject} onValueChange={setSubject}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Choose a subject" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="physics">Physics</SelectItem>
                                            <SelectItem value="chemistry">Chemistry</SelectItem>
                                            <SelectItem value="maths">Mathematics</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            )}

                            {testType === 'chapter' && (
                                <>
                                    <div className="space-y-2">
                                        <Label>Select Subject</Label>
                                        <Select value={subject} onValueChange={setSubject}>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Choose a subject" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="physics">Physics</SelectItem>
                                                <SelectItem value="chemistry">Chemistry</SelectItem>
                                                <SelectItem value="maths">Mathematics</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Select Chapter</Label>
                                        <Select value={chapter} onValueChange={setChapter} disabled={!subject}>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Choose a chapter" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="kinematics">Kinematics</SelectItem>
                                                <SelectItem value="thermodynamics">Thermodynamics</SelectItem>
                                                {/* Add more chapters dynamically potentially */}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </>
                            )}

                            <div className="flex justify-end pt-4">
                                <Button onClick={handleStartTest} className="w-full sm:w-auto">
                                    Start Practice
                                </Button>
                            </div>
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}
