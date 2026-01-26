import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, Trash2, CheckCircle2, Edit2 } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';

interface ParsedQuestion {
  id: string;
  question_text: string;
  options: { id: string; text: string }[];
  correct_answer: string;
  difficulty_level?: string;
  subject?: string;
  chapter?: string;
  topic?: string;
}

export function BulkTextDumper({ onComplete }: { onComplete?: () => void }) {
  const [bulkText, setBulkText] = useState('');
  const [parsing, setParsing] = useState(false);
  const [parsedQuestions, setParsedQuestions] = useState<ParsedQuestion[]>([]);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [tagHierarchy, setTagHierarchy] = useState<any>(null);

  // Fetch tag hierarchy on mount
  useEffect(() => {
    fetchTagHierarchy();
  }, []);

  const fetchTagHierarchy = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      if (!token) return;

      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      
      const response = await fetch(`${API_BASE_URL}/api/ai/tag-hierarchy`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('[DEBUG] Tag hierarchy fetched:', data);
        console.log('[DEBUG] Hierarchy keys:', Object.keys(data.hierarchy || {}));
        console.log('[DEBUG] Full hierarchy structure:', JSON.stringify(data.hierarchy, null, 2));
        setTagHierarchy(data.hierarchy);
      } else {
        console.error('[DEBUG] Failed to fetch tag hierarchy:', response.status);
      }
    } catch (error) {
      console.error('Error fetching tag hierarchy:', error);
    }
  };

  const mapTagNamesToIds = (question: ParsedQuestion) => {
    if (!tagHierarchy) {
      console.log('[DEBUG] No tag hierarchy loaded, cannot map IDs');
      return { subject_id: null, chapter_id: null, topic_id: null };
    }

    let subject_id = null;
    let chapter_id = null;
    let topic_id = null;

    // Find subject ID
    if (question.subject && tagHierarchy[question.subject]) {
      subject_id = tagHierarchy[question.subject].id;
      console.log(`[DEBUG] Mapped subject "${question.subject}" to ID: ${subject_id}`);

      // Find chapter ID
      if (question.chapter && tagHierarchy[question.subject].chapters[question.chapter]) {
        chapter_id = tagHierarchy[question.subject].chapters[question.chapter].id;
        console.log(`[DEBUG] Mapped chapter "${question.chapter}" to ID: ${chapter_id}`);

        // Find topic ID
        if (question.topic && tagHierarchy[question.subject].chapters[question.chapter].topics[question.topic]) {
          topic_id = tagHierarchy[question.subject].chapters[question.chapter].topics[question.topic].id;
          console.log(`[DEBUG] Mapped topic "${question.topic}" to ID: ${topic_id}`);
        } else if (question.topic) {
          console.log(`[DEBUG] Topic "${question.topic}" not found in database`);
        }
      } else if (question.chapter) {
        console.log(`[DEBUG] Chapter "${question.chapter}" not found in database`);
      }
    } else if (question.subject) {
      console.log(`[DEBUG] Subject "${question.subject}" not found in database`);
    }

    return { subject_id, chapter_id, topic_id };
  };

  const parseQuestions = async () => {
    setParsing(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      if (!token) {
        toast.error('Please log in to continue');
        setParsing(false);
        return;
      }

      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      
      const response = await fetch(`${API_BASE_URL}/api/ai/parse-questions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ text: bulkText })
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to parse questions' }));
        
        // Handle specific error cases
        if (response.status === 503) {
          throw new Error('AI service is not configured. Please contact administrator.');
        } else if (response.status === 401) {
          throw new Error('Session expired. Please log in again.');
        } else {
          throw new Error(error.detail || 'Failed to parse questions');
        }
      }

      const { questions, count } = await response.json();

      console.log('[DEBUG] Received questions from API:', questions);
      console.log('[DEBUG] First question tags:', questions[0]?.subject, questions[0]?.chapter, questions[0]?.topic);
      console.log('[DEBUG] First question full object:', JSON.stringify(questions[0], null, 2));

      if (!questions || questions.length === 0) {
        toast.error('No valid questions found. Please check the format and try again.');
        setParsedQuestions([]);
      } else {
        const parsed = questions.map((q: any, idx: number) => ({
          id: `temp-${idx}`,
          question_text: q.question_text,
          options: q.options,
          correct_answer: q.correct_answer,
          difficulty_level: q.difficulty_level || 'medium',
          subject: q.subject || null,
          chapter: q.chapter || null,
          topic: q.topic || null
        }));
        
        console.log('[DEBUG] Parsed questions with tags:', parsed);
        console.log('[DEBUG] First parsed question:', parsed[0]);
        
        setParsedQuestions(parsed);
        toast.success(`🎉 AI parsed ${count} question(s) successfully!`);
      }
    } catch (error: any) {
      console.error('Parse error:', error);
      toast.error(error.message || 'Failed to parse questions. Please try again.');
      setParsedQuestions([]);
    } finally {
      setParsing(false);
    }
  };

  const updateQuestion = (index: number, field: keyof ParsedQuestion, value: any) => {
    const updated = [...parsedQuestions];
    updated[index] = { ...updated[index], [field]: value };
    setParsedQuestions(updated);
  };

  const updateQuestionTags = (index: number, subject?: string | null, chapter?: string | null, topic?: string | null) => {
    const updated = [...parsedQuestions];
    const updates: Partial<ParsedQuestion> = {};
    
    if (subject !== undefined) updates.subject = subject || undefined;
    if (chapter !== undefined) updates.chapter = chapter || undefined;
    if (topic !== undefined) updates.topic = topic || undefined;
    
    updated[index] = { ...updated[index], ...updates };
    setParsedQuestions(updated);
  };

  const updateOption = (qIndex: number, optIndex: number, text: string) => {
    const updated = [...parsedQuestions];
    updated[qIndex].options[optIndex].text = text;
    setParsedQuestions(updated);
  };

  const deleteQuestion = (index: number) => {
    setParsedQuestions(parsedQuestions.filter((_, i) => i !== index));
  };

  const saveToRepository = async () => {
    setSaving(true);
    try {
      const questionsToInsert = parsedQuestions.map(q => {
        // Map tag names to IDs
        const { subject_id, chapter_id, topic_id } = mapTagNamesToIds(q);
        
        // Determine status based on whether question is fully tagged with valid IDs
        const isFullyTagged = subject_id && chapter_id && topic_id;
        
        // Store AI-generated tag names in metadata for reference
        const metadata: any = {};
        if (q.subject || q.chapter || q.topic) {
          metadata.ai_suggested_tags = {
            subject: q.subject,
            chapter: q.chapter,
            topic: q.topic
          };
        }
        
        return {
          question_text: q.question_text,
          options: q.options,
          correct_answer: q.correct_answer,
          difficulty_level: q.difficulty_level,
          subject_id,
          chapter_id,
          topic_id,
          is_tagged: false, // All go to untagged repository initially
          status: isFullyTagged ? 'in_review' : null, // in_review if fully tagged with IDs, null otherwise
          metadata: Object.keys(metadata).length > 0 ? metadata : null
        };
      });

      const { error } = await supabase
        .from('repository_questions')
        // @ts-ignore - Supabase types may not be up to date with new status column
        .insert(questionsToInsert);

      if (error) throw error;

      const fullyTaggedCount = questionsToInsert.filter(q => q.status === 'in_review').length;
      const needsTaggingCount = questionsToInsert.filter(q => q.status === null).length;
      const hasAISuggestions = questionsToInsert.filter(q => q.metadata?.ai_suggested_tags).length;

      let message = `${parsedQuestions.length} question(s) saved to repository!`;
      if (fullyTaggedCount > 0) {
        message += ` ${fullyTaggedCount} marked as "In Review" (fully tagged).`;
      }
      if (needsTaggingCount > 0) {
        message += ` ${needsTaggingCount} need tagging.`;
      }
      if (hasAISuggestions > 0 && needsTaggingCount > 0) {
        message += ` AI suggestions saved for manual review.`;
      }

      toast.success(message);
      setBulkText('');
      setParsedQuestions([]);
      onComplete?.();
    } catch (error: any) {
      console.error('Save error:', error);
      toast.error('Failed to save questions: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      {parsedQuestions.length === 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Paste Question Text
              <Badge variant="secondary" className="text-xs">AI-Powered</Badge>
            </CardTitle>
            <CardDescription>
              Paste your questions in any format. Our AI (powered by Groq) will intelligently parse and structure them in seconds.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Format Example:</Label>
              <div className="bg-muted p-4 rounded-md text-sm font-mono space-y-1">
                <div className="text-muted-foreground mb-2">// Flexible format - AI will understand various styles:</div>
                <div>Q: What is 2 + 2?</div>
                <div>A) 3</div>
                <div>B) 4</div>
                <div>C) 5</div>
                <div>D) 6</div>
                <div>Answer: B</div>
                <div>Difficulty: easy</div>
                <div className="text-muted-foreground">(blank line)</div>
                <div className="mt-2">1. What is the capital of France?</div>
                <div>a. London</div>
                <div>b. Berlin</div>
                <div>c. Paris (correct)</div>
                <div>d. Madrid</div>
                <div className="text-muted-foreground mt-2">// AI handles different formats automatically</div>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                💡 The AI can understand various question formats, numbering styles, and answer indicators. 
                Just paste your questions naturally!
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="bulk-text">Paste Questions Here</Label>
              <Textarea
                id="bulk-text"
                value={bulkText}
                onChange={(e) => setBulkText(e.target.value)}
                placeholder="Paste your questions here..."
                className="min-h-[300px] font-mono text-sm"
              />
            </div>

            <Button 
              onClick={parseQuestions} 
              disabled={!bulkText.trim() || parsing}
              className="w-full"
            >
              {parsing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  AI Parsing Questions...
                </>
              ) : (
                <>
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  Parse with AI
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Review Section */}
      {parsedQuestions.length > 0 && (
        <Card>
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Review Questions</CardTitle>
                <CardDescription>
                  Review and edit parsed questions before saving to repository
                </CardDescription>
              </div>
              <Badge variant="secondary" className="text-lg px-4 py-1">
                {parsedQuestions.length} Questions
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[500px]">
              <div className="divide-y">
                {parsedQuestions.map((q, qIdx) => {
                  // Debug: Log question tags
                  if (qIdx === 0) {
                    console.log('[DEBUG] Rendering question:', q);
                    console.log('[DEBUG] Has tags?', q.subject, q.chapter, q.topic);
                  }
                  
                  return (
                  <div key={q.id} className="p-6 space-y-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary">
                        {qIdx + 1}
                      </div>
                      
                      <div className="flex-grow space-y-4">
                        {/* Question Text */}
                        <div className="space-y-2">
                          <Label>Question</Label>
                          {editingIndex === qIdx ? (
                            <Textarea
                              value={q.question_text}
                              onChange={(e) => updateQuestion(qIdx, 'question_text', e.target.value)}
                              className="min-h-[80px]"
                            />
                          ) : (
                            <p className="text-lg p-3 bg-muted/30 rounded-md">{q.question_text}</p>
                          )}
                        </div>

                        {/* Options */}
                        <div className="space-y-2">
                          <Label>Options</Label>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                            {q.options.map((opt, optIdx) => (
                              <div key={opt.id} className="flex gap-2 items-center">
                                <span className="font-bold text-primary w-6">{opt.id}.</span>
                                {editingIndex === qIdx ? (
                                  <Input
                                    value={opt.text}
                                    onChange={(e) => updateOption(qIdx, optIdx, e.target.value)}
                                    className="flex-grow"
                                  />
                                ) : (
                                  <span className={`flex-grow p-2 rounded border ${
                                    opt.id === q.correct_answer ? 'bg-green-500/10 border-green-500/30' : 'bg-card'
                                  }`}>
                                    {opt.text}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Metadata */}
                        <div className="space-y-4">
                          <div className="flex gap-4 items-end">
                            <div className="space-y-2 flex-grow">
                              <Label>Correct Answer</Label>
                              {editingIndex === qIdx ? (
                                <Select
                                  value={q.correct_answer}
                                  onValueChange={(val) => updateQuestion(qIdx, 'correct_answer', val)}
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {q.options.map(opt => (
                                      <SelectItem key={opt.id} value={opt.id}>{opt.id}</SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              ) : (
                                <Badge variant="outline" className="bg-green-500/10">
                                  Answer: {q.correct_answer}
                                </Badge>
                              )}
                            </div>

                            <div className="space-y-2 flex-grow">
                              <Label>Difficulty</Label>
                              {editingIndex === qIdx ? (
                                <Select
                                  value={q.difficulty_level}
                                  onValueChange={(val) => updateQuestion(qIdx, 'difficulty_level', val)}
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="easy">Easy</SelectItem>
                                    <SelectItem value="medium">Medium</SelectItem>
                                    <SelectItem value="hard">Hard</SelectItem>
                                  </SelectContent>
                                </Select>
                              ) : (
                                <Badge variant="secondary">
                                  {q.difficulty_level?.toUpperCase()}
                                </Badge>
                              )}
                            </div>
                          </div>

                          {/* Tags */}
                          {(q.subject || q.chapter || q.topic || editingIndex === qIdx) && (
                            <div className="space-y-2">
                              <Label className="text-xs">Tags</Label>
                              {editingIndex === qIdx ? (
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                  {/* Subject Selector */}
                                  <div className="space-y-1">
                                    <Label className="text-xs text-muted-foreground">Subject</Label>
                                    <Select
                                      value={q.subject || 'none'}
                                      onValueChange={(val) => {
                                        if (val === 'none') {
                                          updateQuestionTags(qIdx, null, null, null);
                                        } else {
                                          updateQuestionTags(qIdx, val, null, null);
                                        }
                                      }}
                                    >
                                      <SelectTrigger>
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem value="none">-- Select Subject --</SelectItem>
                                        {tagHierarchy && Object.keys(tagHierarchy).map(subject => (
                                          <SelectItem key={subject} value={subject}>
                                            {subject}
                                          </SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  </div>

                                  {/* Chapter Selector */}
                                  <div className="space-y-1">
                                    <Label className="text-xs text-muted-foreground">Chapter</Label>
                                    <Select
                                      value={q.chapter || 'none'}
                                      onValueChange={(val) => {
                                        if (val === 'none') {
                                          updateQuestionTags(qIdx, undefined, null, null);
                                        } else {
                                          updateQuestionTags(qIdx, undefined, val, null);
                                        }
                                      }}
                                      disabled={!q.subject || !tagHierarchy?.[q.subject]}
                                    >
                                      <SelectTrigger>
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem value="none">-- Select Chapter --</SelectItem>
                                        {q.subject && tagHierarchy?.[q.subject]?.chapters && 
                                          Object.keys(tagHierarchy[q.subject].chapters).map(chapter => (
                                            <SelectItem key={chapter} value={chapter}>
                                              {chapter}
                                            </SelectItem>
                                          ))
                                        }
                                      </SelectContent>
                                    </Select>
                                  </div>

                                  {/* Topic Selector */}
                                  <div className="space-y-1">
                                    <Label className="text-xs text-muted-foreground">Topic</Label>
                                    <Select
                                      value={q.topic || 'none'}
                                      onValueChange={(val) => {
                                        if (val === 'none') {
                                          updateQuestionTags(qIdx, undefined, undefined, null);
                                        } else {
                                          updateQuestionTags(qIdx, undefined, undefined, val);
                                        }
                                      }}
                                      disabled={!q.chapter || !q.subject || !tagHierarchy?.[q.subject]?.chapters?.[q.chapter]}
                                    >
                                      <SelectTrigger>
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem value="none">-- Select Topic --</SelectItem>
                                        {q.subject && q.chapter && tagHierarchy?.[q.subject]?.chapters?.[q.chapter]?.topics && 
                                          Object.keys(tagHierarchy[q.subject].chapters[q.chapter].topics).map(topic => (
                                            <SelectItem key={topic} value={topic}>
                                              {topic}
                                            </SelectItem>
                                          ))
                                        }
                                      </SelectContent>
                                    </Select>
                                  </div>
                                </div>
                              ) : (
                                <div className="flex flex-wrap gap-2">
                                  {q.subject && (
                                    <Badge variant="outline" className="bg-blue-500/10 border-blue-500/30">
                                      {q.subject}
                                    </Badge>
                                  )}
                                  {q.chapter && (
                                    <Badge variant="outline" className="bg-purple-500/10 border-purple-500/30">
                                      {q.chapter}
                                    </Badge>
                                  )}
                                  {q.topic && (
                                    <Badge variant="outline" className="bg-green-500/10 border-green-500/30">
                                      {q.topic}
                                    </Badge>
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex flex-col gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setEditingIndex(editingIndex === qIdx ? null : qIdx)}
                          className="h-8 w-8"
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => deleteQuestion(qIdx)}
                          className="h-8 w-8 text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                  );
                })}
              </div>
            </ScrollArea>
          </CardContent>
          <div className="p-6 border-t bg-muted/20 flex gap-4">
            <Button
              variant="outline"
              onClick={() => {
                setParsedQuestions([]);
                setBulkText('');
              }}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={saveToRepository}
              disabled={saving || parsedQuestions.length === 0}
              className="flex-1"
            >
              {saving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  Save to Repository ({parsedQuestions.length})
                </>
              )}
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
