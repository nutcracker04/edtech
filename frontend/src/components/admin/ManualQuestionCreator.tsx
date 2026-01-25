import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Plus, Trash2, Check, X, Info } from "lucide-react";
import { toast } from "sonner";
import { supabase } from "@/integrations/supabase/client";
import { Alert, AlertDescription } from "@/components/ui/alert";

type QuestionType = "single_choice" | "multi_choice" | "integer" | "assertion_reasoning";

interface Option {
    id: string;
    text: string;
}

interface QuestionData {
    question_text: string;
    question_type: QuestionType;
    options?: Option[];
    correct_answer: string | string[]; // string for single/integer, array for multi
    assertion?: string;
    reasoning?: string;
}

const ASSERTION_REASONING_OPTIONS = [
    { id: "A", text: "Both A and R are true, and R is the correct explanation of A" },
    { id: "B", text: "Both A and R are true, but R is NOT the correct explanation of A" },
    { id: "C", text: "A is true, but R is false" },
    { id: "D", text: "A is false, but R is true" },
    { id: "E", text: "Both A and R are false" },
];

export const ManualQuestionCreator = ({ onQuestionCreated }: { onQuestionCreated?: () => void }) => {
    const [questionType, setQuestionType] = useState<QuestionType>("single_choice");
    const [questionText, setQuestionText] = useState("");

    // For assertion-reasoning
    const [assertion, setAssertion] = useState("");
    const [reasoning, setReasoning] = useState("");

    // For choice-based questions
    const [options, setOptions] = useState<Option[]>([
        { id: "A", text: "" },
        { id: "B", text: "" },
        { id: "C", text: "" },
        { id: "D", text: "" },
    ]);

    // For answers
    const [correctAnswer, setCorrectAnswer] = useState("");
    const [correctAnswers, setCorrectAnswers] = useState<string[]>([]); // For multi-choice
    const [integerAnswer, setIntegerAnswer] = useState("");

    const [saving, setSaving] = useState(false);

    const handleQuestionTypeChange = (type: QuestionType) => {
        setQuestionType(type);
        resetForm();
    };

    const updateOption = (index: number, text: string) => {
        const newOptions = [...options];
        newOptions[index].text = text;
        setOptions(newOptions);
    };

    const addOption = () => {
        const nextLetter = String.fromCharCode(65 + options.length);
        setOptions([...options, { id: nextLetter, text: "" }]);
    };

    const removeOption = (index: number) => {
        if (options.length <= 2) {
            toast.error("A question must have at least 2 options");
            return;
        }
        const newOptions = options.filter((_, i) => i !== index);
        setOptions(newOptions);
    };

    const toggleMultiAnswer = (optionId: string) => {
        setCorrectAnswers(prev =>
            prev.includes(optionId)
                ? prev.filter(id => id !== optionId)
                : [...prev, optionId]
        );
    };

    const validateQuestion = (): boolean => {
        if (questionType === "assertion_reasoning") {
            if (!assertion.trim() || !reasoning.trim()) {
                toast.error("Both Assertion and Reasoning are required");
                return false;
            }
            if (!correctAnswer) {
                toast.error("Please select the correct answer");
                return false;
            }
        } else if (questionType === "integer") {
            if (!questionText.trim()) {
                toast.error("Question text is required");
                return false;
            }
            if (!integerAnswer.trim() || !/^\d+$/.test(integerAnswer)) {
                toast.error("Please enter a valid integer answer (0-9)");
                return false;
            }
        } else {
            if (!questionText.trim()) {
                toast.error("Question text is required");
                return false;
            }

            const filledOptions = options.filter(opt => opt.text.trim());
            if (filledOptions.length < 2) {
                toast.error("At least 2 options must be filled");
                return false;
            }

            if (questionType === "single_choice" && !correctAnswer) {
                toast.error("Please select the correct answer");
                return false;
            }

            if (questionType === "multi_choice" && correctAnswers.length === 0) {
                toast.error("Please select at least one correct answer");
                return false;
            }
        }

        return true;
    };

    const handleSaveQuestion = async () => {
        if (!validateQuestion()) return;

        setSaving(true);
        try {
            let questionData: any = {
                question_type: questionType,
                is_tagged: false,
                source_paper_id: null,
            };

            if (questionType === "assertion_reasoning") {
                questionData.question_text = `Assertion (A): ${assertion}\nReason (R): ${reasoning}`;
                questionData.options = ASSERTION_REASONING_OPTIONS;
                questionData.correct_answer = correctAnswer;
                questionData.assertion = assertion;
                questionData.reasoning = reasoning;
            } else if (questionType === "integer") {
                questionData.question_text = questionText.trim();
                questionData.options = [];
                questionData.correct_answer = integerAnswer;
            } else if (questionType === "multi_choice") {
                questionData.question_text = questionText.trim();
                questionData.options = options.filter(opt => opt.text.trim());
                questionData.correct_answer = correctAnswers.join(",");
            } else {
                questionData.question_text = questionText.trim();
                questionData.options = options.filter(opt => opt.text.trim());
                questionData.correct_answer = correctAnswer;
            }

            const { error } = await supabase
                .from("repository_questions")
                .insert(questionData);

            if (error) throw error;

            toast.success("Question added to untagged repository!");
            resetForm();
            onQuestionCreated?.();
        } catch (error: any) {
            toast.error("Failed to save question: " + error.message);
        } finally {
            setSaving(false);
        }
    };

    const resetForm = () => {
        setQuestionText("");
        setAssertion("");
        setReasoning("");
        setOptions([
            { id: "A", text: "" },
            { id: "B", text: "" },
            { id: "C", text: "" },
            { id: "D", text: "" },
        ]);
        setCorrectAnswer("");
        setCorrectAnswers([]);
        setIntegerAnswer("");
    };

    return (
        <Card className="border-2">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Plus className="h-5 w-5" />
                    Create Question Manually
                </CardTitle>
                <CardDescription>
                    Select question type and enter details
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* Question Type Selection */}
                <div className="space-y-2">
                    <Label>Question Type *</Label>
                    <Select value={questionType} onValueChange={(val) => handleQuestionTypeChange(val as QuestionType)}>
                        <SelectTrigger>
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="single_choice">Single Choice (One Correct)</SelectItem>
                            <SelectItem value="multi_choice">Multi Choice (Multiple Correct)</SelectItem>
                            <SelectItem value="integer">Integer Based (0-9)</SelectItem>
                            <SelectItem value="assertion_reasoning">Assertion & Reasoning</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {/* Type-specific info */}
                {questionType === "integer" && (
                    <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription>
                            Integer questions expect a numeric answer between 0-9.
                        </AlertDescription>
                    </Alert>
                )}

                {questionType === "multi_choice" && (
                    <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription>
                            You can select multiple correct answers for this question type.
                        </AlertDescription>
                    </Alert>
                )}

                {/* Assertion & Reasoning Fields */}
                {questionType === "assertion_reasoning" ? (
                    <>
                        <div className="space-y-2">
                            <Label htmlFor="assertion">Assertion (A) *</Label>
                            <Textarea
                                id="assertion"
                                placeholder="Enter the assertion statement..."
                                value={assertion}
                                onChange={(e) => setAssertion(e.target.value)}
                                rows={3}
                                className="font-mono resize-none"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="reasoning">Reason (R) *</Label>
                            <Textarea
                                id="reasoning"
                                placeholder="Enter the reasoning statement..."
                                value={reasoning}
                                onChange={(e) => setReasoning(e.target.value)}
                                rows={3}
                                className="font-mono resize-none"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Correct Answer *</Label>
                            <Select value={correctAnswer} onValueChange={setCorrectAnswer}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select correct answer" />
                                </SelectTrigger>
                                <SelectContent>
                                    {ASSERTION_REASONING_OPTIONS.map(opt => (
                                        <SelectItem key={opt.id} value={opt.id}>
                                            {opt.id} - {opt.text}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </>
                ) : questionType === "integer" ? (
                    <>
                        <div className="space-y-2">
                            <Label htmlFor="question-text">Question Text *</Label>
                            <Textarea
                                id="question-text"
                                placeholder="Enter your question here..."
                                value={questionText}
                                onChange={(e) => setQuestionText(e.target.value)}
                                rows={4}
                                className="font-mono resize-none"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="integer-answer">Integer Answer (0-9) *</Label>
                            <Input
                                id="integer-answer"
                                type="number"
                                min="0"
                                max="9"
                                placeholder="Enter answer (0-9)"
                                value={integerAnswer}
                                onChange={(e) => setIntegerAnswer(e.target.value)}
                                className="font-mono"
                            />
                        </div>
                    </>
                ) : (
                    <>
                        {/* Question Text for choice-based */}
                        <div className="space-y-2">
                            <Label htmlFor="question-text">Question Text *</Label>
                            <Textarea
                                id="question-text"
                                placeholder="Enter your question here. You can use special characters like: α, β, π, ∫, √, ², ³, etc."
                                value={questionText}
                                onChange={(e) => setQuestionText(e.target.value)}
                                rows={4}
                                className="font-mono resize-none"
                            />
                        </div>

                        {/* Options */}
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <Label>Options *</Label>
                                <Button variant="outline" size="sm" onClick={addOption}>
                                    <Plus className="h-3 w-3 mr-1" />
                                    Add Option
                                </Button>
                            </div>
                            {options.map((option, idx) => (
                                <div key={idx} className="flex gap-2 items-center">
                                    <Badge variant="secondary" className="shrink-0 w-8 h-8 flex items-center justify-center">
                                        {option.id}
                                    </Badge>
                                    <Input
                                        placeholder={`Option ${option.id}`}
                                        value={option.text}
                                        onChange={(e) => updateOption(idx, e.target.value)}
                                        className="flex-grow font-mono"
                                    />
                                    {options.length > 2 && (
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => removeOption(idx)}
                                            className="shrink-0"
                                        >
                                            <Trash2 className="h-4 w-4 text-destructive" />
                                        </Button>
                                    )}
                                </div>
                            ))}
                        </div>

                        {/* Correct Answer(s) */}
                        {questionType === "single_choice" ? (
                            <div className="space-y-2">
                                <Label>Correct Answer *</Label>
                                <Select value={correctAnswer} onValueChange={setCorrectAnswer}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select correct answer" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {options
                                            .filter(opt => opt.text.trim())
                                            .map(opt => (
                                                <SelectItem key={opt.id} value={opt.id}>
                                                    {opt.id} - {opt.text.substring(0, 50)}
                                                    {opt.text.length > 50 ? "..." : ""}
                                                </SelectItem>
                                            ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                <Label>Correct Answers * (Select all that apply)</Label>
                                <div className="space-y-2 border rounded-md p-4">
                                    {options
                                        .filter(opt => opt.text.trim())
                                        .map(opt => (
                                            <div key={opt.id} className="flex items-center space-x-2">
                                                <Checkbox
                                                    id={`answer-${opt.id}`}
                                                    checked={correctAnswers.includes(opt.id)}
                                                    onCheckedChange={() => toggleMultiAnswer(opt.id)}
                                                />
                                                <label
                                                    htmlFor={`answer-${opt.id}`}
                                                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                                                >
                                                    {opt.id} - {opt.text}
                                                </label>
                                            </div>
                                        ))}
                                </div>
                                {correctAnswers.length > 0 && (
                                    <p className="text-xs text-muted-foreground">
                                        Selected: {correctAnswers.join(", ")}
                                    </p>
                                )}
                            </div>
                        )}
                    </>
                )}

                {/* Actions */}
                <div className="flex gap-3 pt-4">
                    <Button
                        onClick={handleSaveQuestion}
                        disabled={saving}
                        className="flex-1"
                    >
                        {saving ? (
                            <>Saving...</>
                        ) : (
                            <>
                                <Check className="h-4 w-4 mr-2" />
                                Save Question
                            </>
                        )}
                    </Button>
                    <Button
                        variant="outline"
                        onClick={resetForm}
                        disabled={saving}
                    >
                        <X className="h-4 w-4 mr-2" />
                        Clear
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
};
