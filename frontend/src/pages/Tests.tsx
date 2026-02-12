import { useState, useEffect } from "react";
import { testApi } from "@/api/test";
import { pyqApi } from "@/api/pyq";
import { MainLayout } from "@/components/layout/MainLayout";
import { ChevronRight, Plus, BookOpen, FileText, Search, GraduationCap, Bookmark } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { TestCreationDialog } from "@/components/tests/TestCreationDialog";
import { TestCard } from "@/components/tests/TestCard";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";

interface UnifiedTest {
  id: string;
  title: string;
  subject: string;
  type: "full" | "topic" | "adaptive" | "pyq_paper" | "practice";
  questions: number;
  duration: number;
  score?: number;
  date: string;
  status: "completed" | "in_progress" | "upcoming" | "available";
  source?: "repository" | "pyq";
  year?: string; // For year-based filtering
}

type SectionType = 'all' | 'pyq_mock_2026' | 'pyq_mock_2025' | 'pyq_mock_2024' | 'pyq_mock_2023' |
  'pyq_physics' | 'pyq_chemistry' | 'pyq_maths' |
  'topic_physics' | 'topic_chemistry' | 'topic_maths';
type FilterStatus = 'all' | 'available' | 'attempted' | 'upcoming';

const Tests = () => {
  const navigate = useNavigate();
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // Data State
  const [allTests, setAllTests] = useState<UnifiedTest[]>([]);

  // Navigation & Filter States
  const [selectedSection, setSelectedSection] = useState<SectionType>('all');
  const [sectionFilters, setSectionFilters] = useState<Record<string, FilterStatus>>({});
  const [searchQuery, setSearchQuery] = useState("");

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [userTests, papers] = await Promise.all([
        testApi.getTests(),
        pyqApi.getPapers()
      ]);

      const mappedUserTests: UnifiedTest[] = userTests.map((t: any) => ({
        id: t.id,
        title: t.title,
        subject: t.subject || "All Subjects",
        type: t.type,
        questions: t.questions?.length || 0,
        duration: t.duration,
        score: t.max_score > 0 ? Math.round((t.score / t.max_score) * 100) : undefined,
        date: new Date(t.created_at).toLocaleDateString(),
        status: t.status,
        source: t.source || 'repository'
      }));

      const mappedPapers: UnifiedTest[] = papers.map((p: any) => {
        // Extract year from exam_date or title
        const yearMatch = p.exam_date?.match(/\d{4}/) || p.exam_type?.match(/\d{4}/);
        const year = yearMatch ? yearMatch[0] : new Date(p.created_at).getFullYear().toString();

        return {
          id: p.id,
          title: `${p.exam_type} ${p.exam_session || ''} ${p.exam_date || ''}`.trim(),
          subject: "All Subjects",
          type: "pyq_paper" as const,
          questions: p.total_questions || 0,
          duration: 180,
          status: "available" as const,
          date: new Date(p.created_at).toLocaleDateString(),
          source: "pyq" as const,
          year: year
        };
      });

      setAllTests([...mappedPapers, ...mappedUserTests]);

    } catch (error) {
      console.error(error);
      toast.error("Failed to load tests");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateSuccess = (testId?: string) => {
    if (testId) navigate(`/test/${testId}`);
    else loadData();
  };

  // Get current filter for selected section
  const getCurrentFilter = (): FilterStatus => {
    return sectionFilters[selectedSection] || 'all';
  };

  const setCurrentFilter = (filter: FilterStatus) => {
    setSectionFilters(prev => ({ ...prev, [selectedSection]: filter }));
  };

  // Get tests for display based on section and filters
  const getDisplayTests = () => {
    let filtered = allTests;

    // Section-based filtering
    if (selectedSection.startsWith('pyq_mock_')) {
      const year = selectedSection.replace('pyq_mock_', '');
      filtered = filtered.filter(t =>
        t.source === 'pyq' &&
        (t.type === 'full' || t.type === 'practice' || t.type === 'pyq_paper') &&
        t.year === year
      );
    } else if (selectedSection === 'pyq_physics') {
      filtered = filtered.filter(t =>
        t.source === 'pyq' &&
        t.type === 'topic' &&
        t.subject?.toLowerCase() === 'physics'
      );
    } else if (selectedSection === 'pyq_chemistry') {
      filtered = filtered.filter(t =>
        t.source === 'pyq' &&
        t.type === 'topic' &&
        t.subject?.toLowerCase() === 'chemistry'
      );
    } else if (selectedSection === 'pyq_maths') {
      filtered = filtered.filter(t =>
        t.source === 'pyq' &&
        t.type === 'topic' &&
        (t.subject?.toLowerCase() === 'mathematics' || t.subject?.toLowerCase() === 'maths')
      );
    } else if (selectedSection === 'topic_physics') {
      filtered = filtered.filter(t =>
        t.source !== 'pyq' &&
        (t.type === 'topic' || t.type === 'adaptive') &&
        t.subject?.toLowerCase() === 'physics'
      );
    } else if (selectedSection === 'topic_chemistry') {
      filtered = filtered.filter(t =>
        t.source !== 'pyq' &&
        (t.type === 'topic' || t.type === 'adaptive') &&
        t.subject?.toLowerCase() === 'chemistry'
      );
    } else if (selectedSection === 'topic_maths') {
      filtered = filtered.filter(t =>
        t.source !== 'pyq' &&
        (t.type === 'topic' || t.type === 'adaptive') &&
        (t.subject?.toLowerCase() === 'mathematics' || t.subject?.toLowerCase() === 'maths')
      );
    }

    // Apply status filter
    const statusFilter = getCurrentFilter();
    if (statusFilter !== 'all') {
      if (statusFilter === 'attempted') {
        filtered = filtered.filter(t => t.status === 'completed' || t.status === 'in_progress');
      } else if (statusFilter === 'available') {
        filtered = filtered.filter(t => t.status === 'available');
      } else if (statusFilter === 'upcoming') {
        filtered = filtered.filter(t => t.status === 'upcoming');
      }
    }

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(t =>
        t.title.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    return filtered;
  };

  // Count tests for badges
  const getTestCount = (section: SectionType) => {
    let count = 0;
    if (section.startsWith('pyq_mock_')) {
      const year = section.replace('pyq_mock_', '');
      count = allTests.filter(t =>
        t.source === 'pyq' &&
        (t.type === 'full' || t.type === 'practice' || t.type === 'pyq_paper') &&
        t.year === year
      ).length;
    } else if (section === 'pyq_physics') {
      count = allTests.filter(t =>
        t.source === 'pyq' && t.type === 'topic' && t.subject?.toLowerCase() === 'physics'
      ).length;
    } else if (section === 'pyq_chemistry') {
      count = allTests.filter(t =>
        t.source === 'pyq' && t.type === 'topic' && t.subject?.toLowerCase() === 'chemistry'
      ).length;
    } else if (section === 'pyq_maths') {
      count = allTests.filter(t =>
        t.source === 'pyq' && t.type === 'topic' &&
        (t.subject?.toLowerCase() === 'mathematics' || t.subject?.toLowerCase() === 'maths')
      ).length;
    } else if (section === 'topic_physics') {
      count = allTests.filter(t =>
        t.source !== 'pyq' && (t.type === 'topic' || t.type === 'adaptive') &&
        t.subject?.toLowerCase() === 'physics'
      ).length;
    } else if (section === 'topic_chemistry') {
      count = allTests.filter(t =>
        t.source !== 'pyq' && (t.type === 'topic' || t.type === 'adaptive') &&
        t.subject?.toLowerCase() === 'chemistry'
      ).length;
    } else if (section === 'topic_maths') {
      count = allTests.filter(t =>
        t.source !== 'pyq' && (t.type === 'topic' || t.type === 'adaptive') &&
        (t.subject?.toLowerCase() === 'mathematics' || t.subject?.toLowerCase() === 'maths')
      ).length;
    }
    return count;
  };

  const SidebarItem = ({
    active,
    label,
    onClick,
    icon,
    badge
  }: {
    active: boolean,
    label: string,
    onClick: () => void,
    icon?: React.ReactNode,
    badge?: string
  }) => (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center w-full px-4 py-2 text-sm font-medium transition-colors rounded-md",
        active
          ? "bg-primary text-primary-foreground"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
    >
      {icon && <span className="mr-2">{icon}</span>}
      <span className="flex-1 text-left">{label}</span>
      {badge && (
        <Badge variant={active ? "secondary" : "outline"} className="ml-2 text-[10px] h-5">
          {badge}
        </Badge>
      )}
      {!active && <ChevronRight className="w-3 h-3 opacity-50" />}
    </button>
  );

  const FilterBar = ({ selected, onChange }: { selected: FilterStatus, onChange: (s: FilterStatus) => void }) => (
    <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0">
      <Button
        variant={selected === 'all' ? 'default' : 'outline'}
        size="sm"
        className="rounded-full"
        onClick={() => onChange('all')}
      >
        All
      </Button>
      <Button
        variant={selected === 'available' ? 'default' : 'outline'}
        size="sm"
        className="rounded-full"
        onClick={() => onChange('available')}
      >
        Available
      </Button>
      <Button
        variant={selected === 'attempted' ? 'default' : 'outline'}
        size="sm"
        className="rounded-full"
        onClick={() => onChange('attempted')}
      >
        Attempted
      </Button>
      <Button
        variant={selected === 'upcoming' ? 'default' : 'outline'}
        size="sm"
        className="rounded-full"
        onClick={() => onChange('upcoming')}
      >
        Upcoming
      </Button>
    </div>
  );

  const filteredTests = getDisplayTests();

  return (
    <MainLayout>
      <div className="flex h-[calc(100vh-theme(spacing.4))] overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 flex flex-col border-r bg-card/50 hidden md:flex shrink-0">
          <div className="p-4 border-b space-y-2">
            <Button onClick={() => setShowCreateDialog(true)} className="w-full justify-start">
              <Plus className="mr-2 h-4 w-4" /> Create Test
            </Button>
            <Button
              variant={selectedSection === 'all' ? 'default' : 'outline'}
              onClick={() => setSelectedSection('all')}
              className={cn("w-full justify-start", selectedSection === 'all' && "bg-primary text-primary-foreground hover:bg-primary/90")}
            >
              <FileText className="mr-2 h-4 w-4" /> All Tests
            </Button>
          </div>

          <ScrollArea className="flex-1 py-4">
            <div className="space-y-6 px-2">
              {/* PYQs as Mock Tests - Year-wise */}
              <div>
                <h3 className="px-2 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  PYQs as Mock Tests
                </h3>
                <div className="space-y-1">
                  <SidebarItem
                    label="2026 PYQs"
                    active={selectedSection === 'pyq_mock_2026'}
                    onClick={() => setSelectedSection('pyq_mock_2026')}
                    badge={getTestCount('pyq_mock_2026').toString()}
                  />
                  <SidebarItem
                    label="2025 PYQs"
                    active={selectedSection === 'pyq_mock_2025'}
                    onClick={() => setSelectedSection('pyq_mock_2025')}
                    badge={getTestCount('pyq_mock_2025').toString()}
                  />
                  <SidebarItem
                    label="2024 PYQs"
                    active={selectedSection === 'pyq_mock_2024'}
                    onClick={() => setSelectedSection('pyq_mock_2024')}
                    badge={getTestCount('pyq_mock_2024').toString()}
                  />
                  <SidebarItem
                    label="2023 PYQs"
                    active={selectedSection === 'pyq_mock_2023'}
                    onClick={() => setSelectedSection('pyq_mock_2023')}
                    badge={getTestCount('pyq_mock_2023').toString()}
                  />
                </div>
              </div>

              {/* PYQ Chapter-wise - Subject-wise */}
              <div>
                <h3 className="px-2 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  PYQ Chapter-wise
                </h3>
                <div className="space-y-1">
                  <SidebarItem
                    label="Physics PYQ"
                    active={selectedSection === 'pyq_physics'}
                    onClick={() => setSelectedSection('pyq_physics')}
                    badge={getTestCount('pyq_physics').toString()}
                  />
                  <SidebarItem
                    label="Chemistry PYQ"
                    active={selectedSection === 'pyq_chemistry'}
                    onClick={() => setSelectedSection('pyq_chemistry')}
                    badge={getTestCount('pyq_chemistry').toString()}
                  />
                  <SidebarItem
                    label="Mathematics PYQ"
                    active={selectedSection === 'pyq_maths'}
                    onClick={() => setSelectedSection('pyq_maths')}
                    badge={getTestCount('pyq_maths').toString()}
                  />
                </div>
              </div>

              {/* Topic & Chapter Tests - Subject-wise */}
              <div>
                <h3 className="px-2 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Topic & Chapter Tests
                </h3>
                <div className="space-y-1">
                  <SidebarItem
                    label="Physics"
                    active={selectedSection === 'topic_physics'}
                    onClick={() => setSelectedSection('topic_physics')}
                    badge={getTestCount('topic_physics').toString()}
                  />
                  <SidebarItem
                    label="Chemistry"
                    active={selectedSection === 'topic_chemistry'}
                    onClick={() => setSelectedSection('topic_chemistry')}
                    badge={getTestCount('topic_chemistry').toString()}
                  />
                  <SidebarItem
                    label="Mathematics"
                    active={selectedSection === 'topic_maths'}
                    onClick={() => setSelectedSection('topic_maths')}
                    badge={getTestCount('topic_maths').toString()}
                  />
                </div>
              </div>
            </div>
          </ScrollArea>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0 bg-background">
          <div className="flex-1 overflow-hidden p-6 relative">
            <ScrollArea className="h-full pr-4">
              {/* Filter Chips / Tabs */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                {selectedSection !== 'all' && (
                  <FilterBar
                    selected={getCurrentFilter()}
                    onChange={setCurrentFilter}
                  />
                )}

                {/* Search Bar */}
                <div className="relative w-full sm:w-auto">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <input
                    placeholder="Search Tests"
                    className="pl-8 h-9 w-full sm:w-64 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>

              {/* Test Grid */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 pb-10">
                {filteredTests.length > 0 ? (
                  filteredTests.map((test) => (
                    <TestCard key={test.id} test={test} />
                  ))
                ) : (
                  <div className="col-span-full flex flex-col items-center justify-center py-20 text-muted-foreground">
                    <div className="h-16 w-16 bg-muted/50 rounded-full flex items-center justify-center mb-4">
                      <FileText className="h-8 w-8 opacity-50" />
                    </div>
                    <h3 className="text-lg font-medium mb-1">No tests found</h3>
                    <p>Try adjusting your search or filters</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </div>

      <TestCreationDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSuccess={handleCreateSuccess}
      />
    </MainLayout>
  );
};

export default Tests;
