import { useState } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { FileUp, BookOpen, Network, Loader2, CheckCircle2, AlertCircle, Upload } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { supabase } from "@/integrations/supabase/client";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

interface ExtractedConcept {
  name: string;
  class_level: number;
  keywords: string[];
  description: string;
  proposed_dna: any;
  potential_prerequisites: string[];
  chapter_context?: string;
}

const ConceptGraphManager = () => {
  const [loading, setLoading] = useState(false);
  const [extractedConcepts, setExtractedConcepts] = useState<ExtractedConcept[]>([]);
  const [publishingAll, setPublishingAll] = useState(false);
  const [selectedConcepts, setSelectedConcepts] = useState<Set<number>>(new Set());
  
  // Image/Text Extraction Form
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [subject, setSubject] = useState("mathematics");
  const [classLevel, setClassLevel] = useState("8");
  const [chapterName, setChapterName] = useState("");
  
  // Text Extraction Form
  const [textContent, setTextContent] = useState("");

  const handleImageExtraction = async () => {
    if (!imageFile) {
      toast.error("Please select an image file");
      return;
    }

    setLoading(true);
    setExtractedConcepts([]);

    const progressToast = toast.loading("Analyzing image with AI vision model...");

    try {
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      
      const formData = new FormData();
      formData.append("image_file", imageFile);
      formData.append("subject", subject);
      formData.append("class_level", classLevel);
      formData.append("textbook_content", "Extract all mathematical concepts from this image");
      if (chapterName) formData.append("chapter_name", chapterName);

      const response = await fetch(`${API_BASE_URL}/api/extract/ncert`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail?.message || "Extraction failed");
      }

      const data = await response.json();
      setExtractedConcepts(data.concepts);
      setSelectedConcepts(new Set(data.concepts.map((_: any, i: number) => i)));
      
      toast.success(`Extracted ${data.concepts.length} concepts from image!`, { id: progressToast });
    } catch (error: any) {
      console.error("Extraction error:", error);
      toast.error(error.message || "Failed to extract concepts", { id: progressToast });
    } finally {
      setLoading(false);
    }
  };

  const handleTextExtraction = async () => {
    if (!textContent || textContent.length < 100) {
      toast.error("Please provide at least 100 characters of text content");
      return;
    }

    setLoading(true);
    setExtractedConcepts([]);

    // Show progress toast
    const progressToast = toast.loading("Analyzing content with AI...");

    try {
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      
      const formData = new FormData();
      formData.append("textbook_content", textContent);
      formData.append("subject", subject);
      formData.append("class_level", classLevel);
      if (chapterName) formData.append("chapter_name", chapterName);

      // Show warning for large content
      if (textContent.length > 8000) {
        toast.loading("Large content detected. Processing in chunks (1-2 minutes)...", { id: progressToast });
      }

      const response = await fetch(`${API_BASE_URL}/api/extract/ncert`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail?.message || "Extraction failed");
      }

      const data = await response.json();
      setExtractedConcepts(data.concepts);
      setSelectedConcepts(new Set(data.concepts.map((_: any, i: number) => i))); // Select all by default
      
      toast.success(`Extracted ${data.concepts.length} concepts successfully!`, { id: progressToast });
      
      // Show chunking info if applicable
      if (data.metadata?.chunks_processed > 1) {
        toast.info(`Processed ${data.metadata.chunks_processed} sections of content`);
      }
    } catch (error: any) {
      console.error("Extraction error:", error);
      const errorMsg = error.message || "Failed to extract concepts";
      
      if (errorMsg.includes("timeout") || errorMsg.includes("timed out")) {
        toast.error(
          "Extraction timed out. Try extracting a smaller section.",
          { id: progressToast, duration: 5000 }
        );
      } else {
        toast.error(errorMsg, { id: progressToast });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConcept = async (concept: ExtractedConcept, index: number) => {
    try {
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      
      const conceptData = {
        name: concept.name,
        subject: subject,
        class_level: concept.class_level,
        keywords: concept.keywords,
        description: concept.description,
        difficulty_dna: concept.proposed_dna,
      };

      const response = await fetch(`${API_BASE_URL}/api/concepts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(conceptData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail?.message || "Failed to create concept");
      }

      toast.success(`Concept "${concept.name}" created successfully!`);
      
      // Remove from extracted list and selection
      setExtractedConcepts(prev => prev.filter((_, i) => i !== index));
      setSelectedConcepts(prev => {
        const newSet = new Set(prev);
        newSet.delete(index);
        return newSet;
      });
      
      return true;
    } catch (error: any) {
      console.error("Create concept error:", error);
      toast.error(error.message || "Failed to create concept");
      return false;
    }
  };

  const handlePublishSelected = async () => {
    if (selectedConcepts.size === 0) {
      toast.error("Please select at least one concept to publish");
      return;
    }

    setPublishingAll(true);
    let successCount = 0;
    let failCount = 0;

    const conceptsToPublish = extractedConcepts.filter((_, i) => selectedConcepts.has(i));

    for (let i = 0; i < conceptsToPublish.length; i++) {
      const concept = conceptsToPublish[i];
      const originalIndex = extractedConcepts.indexOf(concept);
      
      try {
        const token = (await supabase.auth.getSession()).data.session?.access_token;
        
        const conceptData = {
          name: concept.name,
          subject: subject,
          class_level: concept.class_level,
          keywords: concept.keywords,
          description: concept.description,
          difficulty_dna: concept.proposed_dna,
        };

        const response = await fetch(`${API_BASE_URL}/api/concepts`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(conceptData),
        });

        if (response.ok) {
          successCount++;
        } else {
          failCount++;
          console.error(`Failed to create concept: ${concept.name}`);
        }
      } catch (error) {
        failCount++;
        console.error(`Error creating concept ${concept.name}:`, error);
      }
    }

    setPublishingAll(false);

    // Remove successfully published concepts
    setExtractedConcepts(prev => prev.filter((_, i) => !selectedConcepts.has(i)));
    setSelectedConcepts(new Set());

    if (successCount > 0) {
      toast.success(`Published ${successCount} concept${successCount > 1 ? 's' : ''} successfully!`);
    }
    if (failCount > 0) {
      toast.error(`Failed to publish ${failCount} concept${failCount > 1 ? 's' : ''}`);
    }
  };

  const toggleConceptSelection = (index: number) => {
    setSelectedConcepts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const toggleSelectAll = () => {
    if (selectedConcepts.size === extractedConcepts.length) {
      setSelectedConcepts(new Set());
    } else {
      setSelectedConcepts(new Set(extractedConcepts.map((_, i) => i)));
    }
  };

  return (
    <MainLayout>
      <div className="container py-8 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Concept Graph Manager</h1>
          <p className="text-muted-foreground">
            Extract concepts from NCERT textbooks and build the knowledge graph
          </p>
        </div>

        <Tabs defaultValue="image" className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="image" className="flex items-center gap-2">
              <FileUp className="h-4 w-4" />
              Image Upload
            </TabsTrigger>
            <TabsTrigger value="text" className="flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              Text Input
            </TabsTrigger>
          </TabsList>

          {/* Image Upload Tab */}
          <TabsContent value="image">
            <Card>
              <CardHeader>
                <CardTitle>Extract from Image</CardTitle>
                <CardDescription>
                  Upload a textbook page image (PNG/JPG) to automatically extract concepts using vision AI
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="subject">Subject</Label>
                    <Select value={subject} onValueChange={setSubject}>
                      <SelectTrigger id="subject">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="mathematics">Mathematics</SelectItem>
                        <SelectItem value="physics">Physics</SelectItem>
                        <SelectItem value="chemistry">Chemistry</SelectItem>
                        <SelectItem value="biology">Biology</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="class-level">Class Level</Label>
                    <Select value={classLevel} onValueChange={setClassLevel}>
                      <SelectTrigger id="class-level">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[8, 9, 10, 11, 12].map((level) => (
                          <SelectItem key={level} value={level.toString()}>
                            Class {level}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="chapter-name">Chapter Name (Optional)</Label>
                    <Input
                      id="chapter-name"
                      placeholder="e.g., Rational Numbers"
                      value={chapterName}
                      onChange={(e) => setChapterName(e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="image-file">Image File</Label>
                  <Input
                    id="image-file"
                    type="file"
                    accept="image/png,image/jpeg,image/jpg"
                    onChange={(e) => setImageFile(e.target.files?.[0] || null)}
                  />
                  <p className="text-xs text-muted-foreground">
                    📸 Upload a clear image of a textbook page. Vision AI will extract concepts from text, diagrams, and formulas.
                  </p>
                </div>

                <Button
                  onClick={handleImageExtraction}
                  disabled={loading || !imageFile}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Extracting Concepts...
                    </>
                  ) : (
                    <>
                      <Network className="mr-2 h-4 w-4" />
                      Extract Concepts from Image
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Text Input Tab */}
          <TabsContent value="text">
            <Card>
              <CardHeader>
                <CardTitle>Extract from Text</CardTitle>
                <CardDescription>
                  Paste NCERT textbook content to extract concepts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="subject-text">Subject</Label>
                    <Select value={subject} onValueChange={setSubject}>
                      <SelectTrigger id="subject-text">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="mathematics">Mathematics</SelectItem>
                        <SelectItem value="physics">Physics</SelectItem>
                        <SelectItem value="chemistry">Chemistry</SelectItem>
                        <SelectItem value="biology">Biology</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="class-level-text">Class Level</Label>
                    <Select value={classLevel} onValueChange={setClassLevel}>
                      <SelectTrigger id="class-level-text">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[8, 9, 10, 11, 12].map((level) => (
                          <SelectItem key={level} value={level.toString()}>
                            Class {level}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="chapter-name-text">Chapter Name (Optional)</Label>
                    <Input
                      id="chapter-name-text"
                      placeholder="e.g., Rational Numbers"
                      value={chapterName}
                      onChange={(e) => setChapterName(e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="text-content">Textbook Content</Label>
                  <Textarea
                    id="text-content"
                    placeholder="Paste NCERT textbook content here (minimum 100 characters)..."
                    value={textContent}
                    onChange={(e) => setTextContent(e.target.value)}
                    rows={12}
                    className="font-mono text-sm"
                  />
                  <p className="text-xs text-muted-foreground">
                    {textContent.length} characters
                  </p>
                </div>

                <Button
                  onClick={handleTextExtraction}
                  disabled={loading || textContent.length < 100}
                  className="w-full"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Extracting Concepts...
                    </>
                  ) : (
                    <>
                      <Network className="mr-2 h-4 w-4" />
                      Extract Concepts from Text
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Extracted Concepts Preview */}
        {extractedConcepts.length > 0 && (
          <Card className="mt-6 border-2 border-primary/20">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    Preview: Extracted Concepts ({extractedConcepts.length})
                  </CardTitle>
                  <CardDescription>
                    Review concepts before publishing to the knowledge graph
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={toggleSelectAll}
                  >
                    {selectedConcepts.size === extractedConcepts.length ? "Deselect All" : "Select All"}
                  </Button>
                  <Button
                    size="sm"
                    onClick={handlePublishSelected}
                    disabled={publishingAll || selectedConcepts.size === 0}
                    className="gap-2"
                  >
                    {publishingAll ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Publishing...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4" />
                        Publish Selected ({selectedConcepts.size})
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {extractedConcepts.map((concept, index) => (
                <Card 
                  key={index} 
                  className={`border-2 transition-all ${
                    selectedConcepts.has(index) 
                      ? "border-primary/50 bg-primary/5" 
                      : "border-border/50"
                  }`}
                >
                  <CardHeader>
                    <div className="flex items-start gap-3">
                      <Checkbox
                        checked={selectedConcepts.has(index)}
                        onCheckedChange={() => toggleConceptSelection(index)}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div className="space-y-1 flex-1">
                            <CardTitle className="text-lg">{concept.name}</CardTitle>
                            <CardDescription>
                              Class {concept.class_level} • {concept.keywords.slice(0, 3).join(", ")}
                              {concept.keywords.length > 3 && ` +${concept.keywords.length - 3} more`}
                            </CardDescription>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleCreateConcept(concept, index)}
                          >
                            Add to Graph
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3 ml-9">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground mb-1">Description:</p>
                      <p className="text-sm">{concept.description}</p>
                    </div>
                    
                    <div>
                      <p className="text-sm font-medium text-muted-foreground mb-1">All Keywords:</p>
                      <div className="flex flex-wrap gap-2">
                        {concept.keywords.map((keyword, i) => (
                          <span
                            key={i}
                            className="text-xs px-2 py-1 bg-accent rounded"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    {concept.potential_prerequisites.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-1">
                          Potential Prerequisites:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {concept.potential_prerequisites.map((prereq, i) => (
                            <span
                              key={i}
                              className="text-xs px-2 py-1 bg-blue-500/10 text-blue-400 rounded"
                            >
                              {prereq}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div>
                      <p className="text-sm font-medium text-muted-foreground mb-1">
                        Difficulty DNA (AI Proposed):
                      </p>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                        <div className="px-3 py-2 bg-accent rounded">
                          <span className="text-muted-foreground">Bloom's Level:</span>{" "}
                          <span className="font-medium">{concept.proposed_dna.bloom_level}/6</span>
                        </div>
                        <div className="px-3 py-2 bg-accent rounded">
                          <span className="text-muted-foreground">Abstraction:</span>{" "}
                          <span className="font-medium">{concept.proposed_dna.abstraction_level}/5</span>
                        </div>
                        <div className="px-3 py-2 bg-accent rounded">
                          <span className="text-muted-foreground">Complexity:</span>{" "}
                          <span className="font-medium">{concept.proposed_dna.computational_complexity}</span>
                        </div>
                        <div className="px-3 py-2 bg-accent rounded">
                          <span className="text-muted-foreground">Integration:</span>{" "}
                          <span className="font-medium">{concept.proposed_dna.concept_integration}</span>
                        </div>
                        <div className="px-3 py-2 bg-accent rounded">
                          <span className="text-muted-foreground">Real-world:</span>{" "}
                          <span className="font-medium">{concept.proposed_dna.real_world_context}/5</span>
                        </div>
                        <div className="px-3 py-2 bg-accent rounded">
                          <span className="text-muted-foreground">Approach:</span>{" "}
                          <span className="font-medium">{concept.proposed_dna.problem_solving_approach}</span>
                        </div>
                      </div>
                    </div>

                    {concept.chapter_context && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-1">Chapter Context:</p>
                        <p className="text-xs text-muted-foreground italic">{concept.chapter_context}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </MainLayout>
  );
};

export default ConceptGraphManager;
