/**
 * Dashboard Data Models and Interfaces
 * Defines the structure of data displayed on the Dashboard page
 */

export interface DashboardMetrics {
  accuracy_percentage: number;
  questions_solved: number;
  study_hours: number;
  tests_completed: number;
}

export interface StreakData {
  current_streak: number;
  streak_milestone_reached: boolean;
  milestone_value?: number; // 7, 14, 30, etc.
}

export interface SubjectPerformance {
  subject_id: string;
  subject_name: string;
  accuracy_percentage: number;
  questions_solved: number;
  trend: 'up' | 'down' | 'flat';
}

export interface ActivityItem {
  id: string;
  type: 'test_completed' | 'questions_solved' | 'topic_reviewed';
  title: string;
  score?: number;
  timestamp: string; // ISO8601
  link?: string;
}

export interface UpcomingTest {
  test_id: string;
  test_name: string;
  test_type: 'mock' | 'pyq' | 'topic';
  date: string; // ISO8601
  difficulty: 'easy' | 'medium' | 'hard';
}

export interface Recommendation {
  topic_id: string;
  topic_name: string;
  reason: string;
  action: string;
  difficulty: string;
  estimated_time_minutes: number;
}

export interface DashboardData {
  user_id: string;
  current_streak: number;
  streak_milestone_reached: boolean;
  key_metrics: DashboardMetrics;
  recent_activity: ActivityItem[];
  subject_performance: SubjectPerformance[];
  upcoming_tests: UpcomingTest[];
  recommendation: Recommendation;
  data_timestamp: string; // ISO8601 - for freshness validation
}
