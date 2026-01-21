import { useState, useEffect, useCallback } from 'react';
import {
  TopicMastery,
  TestAttempt,
  PerformanceMetrics,
  SubjectPerformance,
  UserPerformance,
  Subject,
  Recommendation,
} from '@/types';
import {
  getStoredPerformanceData,
  recordAttempts,
  getTopicMasteries,
  getWeakTopics,
  getStrongTopics,
  getAverageTopics,
  getSubjectPerformance,
  getUserPerformance,
  getAllPerformanceMetrics,
  generateRecommendations,
  generateAllRecommendations,
  getOverallStats,
  getTopicTrend,
  getRecentAttempts,
  calculateAccuracy,
} from '@/services/performanceService';

const DEFAULT_USER_ID = 'current-user'; // In a real app, this would come from auth context

interface UsePerformanceReturn {
  // Data
  topicMasteries: TopicMastery[];
  weakTopics: TopicMastery[];
  strongTopics: TopicMastery[];
  averageTopics: TopicMastery[];
  subjectPerformance: SubjectPerformance | null;
  userPerformance: UserPerformance | null;
  performanceMetrics: PerformanceMetrics[];
  recommendations: Recommendation[];
  overallStats: ReturnType<typeof getOverallStats>;

  // Functions
  recordAttempts: (attempts: TestAttempt[]) => void;
  getTopicTrend: (subject: Subject, topic: string) => 'improving' | 'declining' | 'stable';
  getSubjectPerformance: (subject: Subject) => SubjectPerformance;
  refresh: () => void;

  // Loading state
  isLoading: boolean;
}

/**
 * Hook for managing user performance data
 * Handles fetching, calculating, and updating performance metrics
 */
export function usePerformance(userId: string = DEFAULT_USER_ID, subject?: Subject): UsePerformanceReturn {
  const [topicMasteries, setTopicMasteries] = useState<TopicMastery[]>([]);
  const [weakTopics, setWeakTopics] = useState<TopicMastery[]>([]);
  const [strongTopics, setStrongTopics] = useState<TopicMastery[]>([]);
  const [averageTopics, setAverageTopics] = useState<TopicMastery[]>([]);
  const [subjectPerformance, setSubjectPerformance] = useState<SubjectPerformance | null>(null);
  const [userPerformance, setUserPerformance] = useState<UserPerformance | null>(null);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [overallStats, setOverallStats] = useState(getOverallStats(userId));
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Refresh all performance data
   */
  const refresh = useCallback(() => {
    setIsLoading(true);
    try {
      // Fetch all data
      const masteries = getTopicMasteries(userId);
      const weak = getWeakTopics(userId, subject);
      const strong = getStrongTopics(userId, subject);
      const average = getAverageTopics(userId, subject);
      const userPerf = getUserPerformance(userId);
      const metrics = getAllPerformanceMetrics(userId);
      const recs = generateAllRecommendations(userId);
      const stats = getOverallStats(userId);

      const subjectPerf = subject ? getSubjectPerformance(userId, subject) : null;

      // Update state
      setTopicMasteries(masteries);
      setWeakTopics(weak);
      setStrongTopics(strong);
      setAverageTopics(average);
      setUserPerformance(userPerf);
      setPerformanceMetrics(metrics);
      setRecommendations(recs);
      setOverallStats(stats);
      if (subjectPerf) {
        setSubjectPerformance(subjectPerf);
      }
    } finally {
      setIsLoading(false);
    }
  }, [userId, subject]);

  /**
   * Record new attempts and update data
   */
  const handleRecordAttempts = useCallback(
    (attempts: TestAttempt[]) => {
      recordAttempts(userId, attempts);
      refresh();
    },
    [userId, refresh]
  );

  /**
   * Get trend for a topic
   */
  const handleGetTopicTrend = useCallback(
    (subj: Subject, topic: string) => getTopicTrend(userId, subj, topic),
    [userId]
  );

  /**
   * Get subject performance
   */
  const handleGetSubjectPerformance = useCallback(
    (subj: Subject) => getSubjectPerformance(userId, subj),
    [userId]
  );

  // Load data on mount and when userId/subject changes
  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    // Data
    topicMasteries,
    weakTopics,
    strongTopics,
    averageTopics,
    subjectPerformance,
    userPerformance,
    performanceMetrics,
    recommendations,
    overallStats,

    // Functions
    recordAttempts: handleRecordAttempts,
    getTopicTrend: handleGetTopicTrend,
    getSubjectPerformance: handleGetSubjectPerformance,
    refresh,

    // Loading
    isLoading,
  };
}

/**
 * Hook for a specific subject's performance
 */
export function useSubjectPerformance(subject: Subject): UsePerformanceReturn {
  return usePerformance(DEFAULT_USER_ID, subject);
}

/**
 * Hook for weak topics only
 */
export function useWeakTopics(subject?: Subject) {
  const { weakTopics } = usePerformance(DEFAULT_USER_ID, subject);
  return weakTopics;
}

/**
 * Hook for strong topics only
 */
export function useStrongTopics(subject?: Subject) {
  const { strongTopics } = usePerformance(DEFAULT_USER_ID, subject);
  return strongTopics;
}

/**
 * Hook for recommendations only
 */
export function useRecommendations() {
  const { recommendations } = usePerformance();
  return recommendations;
}

/**
 * Hook for overall stats
 */
export function useOverallStats() {
  const { overallStats } = usePerformance();
  return overallStats;
}
