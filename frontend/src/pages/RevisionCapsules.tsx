import { useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { RevisionCapsuleWidget } from '@/components/chat/RevisionCapsuleWidget';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import { Subject } from '@/types';
import { BookOpen, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

const RevisionCapsules = () => {
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState<Subject>('physics');
  const [focusOnWeak, setFocusOnWeak] = useState(true);
  const [includeFormulas, setIncludeFormulas] = useState(true);
  const [includeCommonMistakes, setIncludeCommonMistakes] = useState(true);
  const [expandedCapsule, setExpandedCapsule] = useState<string | null>(null);

  const subjects: Subject[] = ['physics', 'chemistry', 'mathematics'];

  // Mock capsules list
  const capsules = [
    {
      id: '1',
      subject: 'physics',
      title: 'Electromagnetic Induction & Thermodynamics',
      generatedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
      topicCount: 2,
    },
    {
      id: '2',
      subject: 'chemistry',
      title: 'Coordination Chemistry Quick Review',
      generatedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), // 5 days ago
      topicCount: 1,
    },
    {
      id: '3',
      subject: 'mathematics',
      title: 'Integration Techniques & Applications',
      generatedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
      topicCount: 2,
    },
  ];

  const handleGenerateCapsule = () => {
    console.log('Generating capsule:', {
      subject: selectedSubject,
      focusOnWeak,
      includeFormulas,
      includeCommonMistakes,
    });
    setShowGenerateDialog(false);
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <MainLayout>
      <div className="p-4 sm:p-6 lg:p-8 space-y-4 sm:space-y-6 lg:space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Revision Capsules</h1>
          </div>
          <Button
            onClick={() => setShowGenerateDialog(true)}
            size="lg"
            className="w-full sm:w-auto"
          >
            <Sparkles className="h-4 w-4 mr-2" />
            <span className="hidden sm:inline">Generate New Capsule</span>
            <span className="sm:hidden">Generate</span>
          </Button>
        </div>

        {/* Info Section */}
        <div className="bg-primary/10 border border-primary/20 rounded-xl p-4 sm:p-6">
          <div className="flex items-start gap-3 sm:gap-4">
            <BookOpen className="h-4 w-4 sm:h-5 sm:w-5 text-primary mt-1 shrink-0" />
            <div className="space-y-2">
              <p className="font-semibold text-foreground text-sm sm:text-base">What are Revision Capsules?</p>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Revision capsules are condensed summaries of key concepts, formulas, and common mistakes for specific topics. They're designed to help you quickly review and reinforce your understanding before exams.
              </p>
            </div>
          </div>
        </div>

        {/* Existing Capsules */}
        <div className="space-y-4">
          <h2 className="text-base sm:text-lg font-semibold text-foreground">Your Capsules</h2>

          {capsules.length === 0 ? (
            <div className="bg-card border border-border rounded-xl p-8 sm:p-12 text-center space-y-4">
              <BookOpen className="h-10 w-10 sm:h-12 sm:w-12 text-muted-foreground mx-auto opacity-50" />
              <div>
                <p className="font-medium text-foreground text-sm sm:text-base">No capsules yet</p>
                <p className="text-xs sm:text-sm text-muted-foreground mt-1">
                  Generate your first revision capsule to get started
                </p>
              </div>
              <Button onClick={() => setShowGenerateDialog(true)}>
                Create First Capsule
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {capsules.map((capsule) => (
                <div
                  key={capsule.id}
                  className="bg-card border border-border rounded-lg overflow-hidden"
                >
                  <button
                    onClick={() => setExpandedCapsule(expandedCapsule === capsule.id ? null : capsule.id)}
                    className="w-full p-3 sm:p-4 hover:bg-secondary/30 transition-colors flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
                  >
                    <div className="text-left flex-1 min-w-0">
                      <div className="flex items-center gap-2 sm:gap-3">
                        <div className="w-2 h-2 rounded-full bg-primary shrink-0" />
                        <div className="min-w-0 flex-1">
                          <h3 className="font-medium text-foreground text-sm sm:text-base truncate">{capsule.title}</h3>
                          <p className="text-xs text-muted-foreground mt-1">
                            {capsule.topicCount} topic{capsule.topicCount !== 1 ? 's' : ''} • Generated {formatDate(capsule.generatedAt)}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0 self-start sm:self-center">
                      <span className={cn(
                        'px-2 py-0.5 rounded text-xs font-medium capitalize whitespace-nowrap',
                        capsule.subject === 'physics' && 'bg-blue-500/20 text-blue-400',
                        capsule.subject === 'chemistry' && 'bg-purple-500/20 text-purple-400',
                        capsule.subject === 'mathematics' && 'bg-orange-500/20 text-orange-400',
                      )}>
                        {capsule.subject}
                      </span>
                      {expandedCapsule === capsule.id ? (
                        <ChevronUp className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                      )}
                    </div>
                  </button>

                  {/* Expanded Content */}
                  {expandedCapsule === capsule.id && (
                    <div className="border-t border-border p-3 sm:p-4 space-y-3 sm:space-y-4 bg-secondary/20">
                      <div className="space-y-3">
                        <RevisionCapsuleWidget subject={capsule.subject} />
                      </div>

                      <div className="flex justify-end">
                        <Button size="sm">
                          Practice Topics
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Generate Capsule Dialog */}
      <Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
        <DialogContent className="max-w-md w-[95vw] sm:w-full">
          <DialogHeader>
            <DialogTitle className="text-lg sm:text-xl">Generate Revision Capsule</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 sm:space-y-6">
            {/* Subject Selection */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-3">
                Subject
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {subjects.map(subject => (
                  <button
                    key={subject}
                    onClick={() => setSelectedSubject(subject)}
                    className={cn(
                      'p-3 rounded-lg border-2 transition-all capitalize text-sm font-medium',
                      selectedSubject === subject
                        ? 'border-primary bg-primary/10'
                        : 'border-border hover:border-primary/50'
                    )}
                  >
                    {subject}
                  </button>
                ))}
              </div>
            </div>

            {/* Options */}
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
                <div>
                  <p className="font-medium text-foreground text-sm">Focus on Weak Areas</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Prioritize struggling topics</p>
                </div>
                <Switch checked={focusOnWeak} onCheckedChange={setFocusOnWeak} />
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
                <div>
                  <p className="font-medium text-foreground text-sm">Include Formulas</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Add key formulas and equations</p>
                </div>
                <Switch checked={includeFormulas} onCheckedChange={setIncludeFormulas} />
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/30">
                <div>
                  <p className="font-medium text-foreground text-sm">Common Mistakes</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Highlight frequent errors</p>
                </div>
                <Switch checked={includeCommonMistakes} onCheckedChange={setIncludeCommonMistakes} />
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-3">
              <Button
                onClick={() => setShowGenerateDialog(false)}
                variant="outline"
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={handleGenerateCapsule}
                className="flex-1"
              >
                Generate
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </MainLayout>
  );
};

export default RevisionCapsules;
