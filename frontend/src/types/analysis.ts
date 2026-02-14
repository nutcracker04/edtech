/**
 * Analysis Page Data Models and Interfaces
 * Defines the structure of data displayed on the Analysis page
 */

export interface PerformanceOverview {
  accuracy_percentage: number;
  questions_solved: number;
  study_hours: number;
  avg_time_per_question: number;
  percentile_rank?: number;
}

export interface TrendDataPoint {
  date: string; // ISO8601
  accuracy?: number;
  count?: number;
}

export interface TopicData {
  topic_id: string;
  topic_name: string;
  accuracy_percentage: number;
  questions_solved: number;
  trend: 'up' | 'down' | 'flat';
}

export interface SubjectBreakdown {
  subject_id: string;
  subject_name: string;
  accuracy_percentage: number;
  questions_solved: number;
  trend: 'up' | 'down' | 'flat';
  topics: TopicData[];
}

export interface WeakArea {
  topic_id: string;
  topic_name: string;
  accuracy_percentage: number;
  impact_score: number;
  recommended_action: string;
}

export interface AnalysisRecommendation {
  topic_id: string;
  topic_name: string;
  reason: string;
  action: string;
  difficulty: string;
  estimated_time_minutes: number;
  priority: 'high' | 'medium' | 'low';
}

export interface AnalysisData {
  user_id: string;
  time_period: '7d' | '30d' | '90d' | 'all';
  performance_overview: PerformanceOverview;
  subject_performance: SubjectBreakdown[];
  trend_data: {
    accuracy_by_date: TrendDataPoint[];
    questions_by_date: TrendDataPoint[];
  };
  weak_areas: WeakArea[];
  recommendations: AnalysisRecommendation[];
  data_timestamp: string; // ISO8601 - for freshness validation
}
