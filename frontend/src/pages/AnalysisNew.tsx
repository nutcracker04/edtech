import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { MainLayout } from "@/components/layout/MainLayout";
import { PerformanceVisualization } from "@/components/analysis/PerformanceVisualization";
import { PerformanceOverview } from "@/components/analysis/PerformanceOverview";
import { TrendGraphs } from "@/components/analysis/TrendGraphs";
import { WeakAreasSection } from "@/components/analysis/WeakAreasSection";
import { SubjectBreakdown } from "@/components/analysis/SubjectBreakdown";
import { Breadcrumbs } from "@/components/shared/Breadcrumbs";
import { ErrorBoundary, VisualizationErrorBoundary } from "@/components/ui/error-boundary";
import { OfflineIndicator } from "@/components/ui/offline-indicator";
import { Loader2, AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { analysisApi } from "@/api/analysis";
import { toast } from "sonner";
import { getAnalysisRefreshTimestamp } from "@/lib/dataRefresh";
import type { AnalysisData, WeakArea, SubjectBreakdown as SubjectBreakdownType, TopicData } from "@/types/analysis";

const AnalysisNew = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timePeriod, setTimePeriod] = useState<'7d' | '30d' | '90d' | 'all'>('30d');
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);
  const [lastFetchTime, setLastFetchTime] = useState<number>(0);

  // Handle subject filter from URL params
  useEffect(() => {
    const subjectParam = searchParams.get('subject');
    if (subjectParam) {
      setSelectedSubjectId(subjectParam);
    }
  }, [searchParams]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await analysisApi.getFullAnalysisData(timePeriod);
      setAnalysisData(data);
      setLastFetchTime(Date.now());
    } catch (error) {
      console.error('Failed to load analysis data:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to load analysis data';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [timePeriod]);

  // Check for data refresh requests (e.g., after test completion)
  useEffect(() => {
    const refreshTimestamp = getAnalysisRefreshTimestamp();
    if (refreshTimestamp > lastFetchTime && lastFetchTime > 0) {
      console.log('Analysis data invalidated, refreshing...');
      loadData();
    }
  }, [lastFetchTime]);

  const handleWeakAreaAction = (area: WeakArea) => {
    navigate(`/tests?search=${encodeURIComponent(area.topic_name)}`);
  };

  const handleTopicClick = (subject: SubjectBreakdownType, topic: TopicData) => {
    navigate(`/tests?search=${encodeURIComponent(topic.topic_name)}`);
  };

  if (loading) {
    return (
      <MainLayout>
        <OfflineIndicator />
        <div className="flex justify-center items-center py-20">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <OfflineIndicator />
        <div className="p-4 sm:p-6 lg:p-8">
          <Card className="border-destructive">
            <CardContent className="py-12 text-center">
              <div className="flex justify-center mb-4">
                <div className="h-16 w-16 rounded-full bg-destructive/10 flex items-center justify-center">
                  <AlertTriangle className="h-8 w-8 text-destructive" />
                </div>
              </div>
              <h3 className="text-lg font-semibold mb-2">Failed to Load Analysis</h3>
              <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
                {error}. Please check your connection and try again.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button onClick={loadData}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Retry
                </Button>
                <Button variant="outline" onClick={() => navigate('/dashboard')}>
                  Go to Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </MainLayout>
    );
  }

  if (!analysisData) {
    return (
      <MainLayout>
        <OfflineIndicator />
        <div className="p-4 sm:p-6 lg:p-8">
          <div className="text-center py-20">
            <AlertTriangle className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">No Analysis Data Available</h2>
            <p className="text-muted-foreground mb-6">
              Take some tests to see your performance analysis
            </p>
            <Button onClick={() => navigate('/tests')}>
              Create Your First Test
            </Button>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <OfflineIndicator />
      <ErrorBoundary onReset={loadData}>
        <div className="p-4 sm:p-6 lg:p-8 space-y-6">
          {/* Breadcrumb Navigation */}
          <Breadcrumbs items={[{ label: 'Home', href: '/' }, { label: 'Analysis' }]} />

          {/* Header */}
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Performance Analysis</h1>
            <p className="text-sm sm:text-base text-muted-foreground mt-1">
              Detailed breakdown of your strengths and weaknesses across all topics
            </p>
          </div>

          {/* Performance Overview */}
          <PerformanceOverview
            data={analysisData.performance_overview}
            timePeriod={timePeriod}
            onTimePeriodChange={setTimePeriod}
          />

          {/* Performance Visualization - Progress Rings */}
          <VisualizationErrorBoundary>
            <PerformanceVisualization
              subjects={analysisData.subject_performance}
            />
          </VisualizationErrorBoundary>

          {/* Trend Graphs */}
          <VisualizationErrorBoundary>
            <TrendGraphs
              accuracyData={analysisData.trend_data.accuracy_by_date}
              questionCountData={analysisData.trend_data.questions_by_date}
            />
          </VisualizationErrorBoundary>

          {/* Weak Areas Section */}
          <WeakAreasSection
            weakAreas={analysisData.weak_areas}
            onActionClick={handleWeakAreaAction}
          />

          {/* Subject-wise Breakdown */}
          <SubjectBreakdown
            subjects={analysisData.subject_performance}
            onTopicClick={handleTopicClick}
            selectedSubjectId={selectedSubjectId}
          />
        </div>
      </ErrorBoundary>
    </MainLayout>
  );
};

export default AnalysisNew;
