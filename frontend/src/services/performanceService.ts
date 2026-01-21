import {
  TopicMastery,
  TestAttempt,
  PerformanceMetrics,
  SubjectPerformance,
  UserPerformance,
  Subject,
  Recommendation,
} from '@/types';

const STORAGE_KEY = 'jee-performance-data';
const MINIMUM_QUESTIONS = 3;

// ============================================================================
// Performance Data Storage
// ============================================================================

interface StoredPerformanceData {
  userId: string;
  topicMasteries: TopicMastery[];
  attempts: TestAttempt[];
  updatedAt: Date;
}

/**
 * Get all stored performance data from localStorage
 */
export function getStoredPerformanceData(userId: string): StoredPerformanceData {
  const stored = localStorage.getItem(`${STORAGE_KEY}-${userId}`);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch (e) {
      console.error('Failed to parse stored performance data:', e);
    }
  }

  return {
    userId,
    topicMasteries: [],
    attempts: [],
    updatedAt: new Date(),
  };
}

/**
 * Save performance data to localStorage
 */
export function savePerformanceData(userId: string, data: StoredPerformanceData): void {
  localStorage.setItem(`${STORAGE_KEY}-${userId}`, JSON.stringify(data));
}

/**
 * Record test attempts
 */
export function recordAttempts(userId: string, attempts: TestAttempt[]): void {
  const data = getStoredPerformanceData(userId);
  data.attempts.push(...attempts);
  data.updatedAt = new Date();
  savePerformanceData(userId, data);
  updateMasteryScores(userId);
}

/**
 * Update topic mastery scores based on attempts
 */
function updateMasteryScores(userId: string): void {
  const data = getStoredPerformanceData(userId);

  // Group attempts by topic
  const attemptsByTopic: Record<string, TestAttempt[]> = {};

  data.attempts.forEach(attempt => {
    // Note: In a real app, we'd have topic info in the attempt
    // For now, we'll use a simple key
    const key = `${attempt.questionId}`;
    if (!attemptsByTopic[key]) {
      attemptsByTopic[key] = [];
    }
    attemptsByTopic[key].push(attempt);
  });

  // Calculate mastery for each topic
  const masteryMap: Record<string, { correct: number; total: number }> = {};

  data.attempts.forEach(attempt => {
    const topicKey = `topic-${attempt.questionId}`;
    if (!masteryMap[topicKey]) {
      masteryMap[topicKey] = { correct: 0, total: 0 };
    }
    masteryMap[topicKey].total += 1;
    if (attempt.isCorrect) {
      masteryMap[topicKey].correct += 1;
    }
  });

  // Update or create TopicMastery entries
  Object.entries(masteryMap).forEach(([topicKey, stats]) => {
    const existingIndex = data.topicMasteries.findIndex(
      m => m.id === topicKey
    );

    const masteryScore = stats.total > 0 ? (stats.correct / stats.total) * 100 : 0;
    const strength = masteryScore >= 85 ? 'strong' : masteryScore >= 70 ? 'average' : 'weak';

    const mastery: TopicMastery = {
      id: topicKey,
      userId,
      subject: 'physics', // This would be determined from the question in a real app
      topic: topicKey.replace('topic-', ''),
      masteryScore: Math.round(masteryScore),
      questionsAttempted: stats.total,
      questionsCorrect: stats.correct,
      lastAttemptDate: new Date(),
      strength,
    };

    if (existingIndex >= 0) {
      data.topicMasteries[existingIndex] = mastery;
    } else {
      data.topicMasteries.push(mastery);
    }
  });

  data.updatedAt = new Date();
  savePerformanceData(userId, data);
}

// ============================================================================
// Performance Calculation Functions
// ============================================================================

/**
 * Get all topic masteries for a user
 */
export function getTopicMasteries(userId: string): TopicMastery[] {
  const data = getStoredPerformanceData(userId);
  return data.topicMasteries;
}

/**
 * Get mastery for a specific topic
 */
export function getTopicMastery(userId: string, subject: Subject, topic: string): TopicMastery | null {
  const data = getStoredPerformanceData(userId);
  const mastery = data.topicMasteries.find(
    m => m.subject === subject && m.topic === topic
  );
  return mastery || null;
}

/**
 * Get weak topics (mastery < 70%)
 */
export function getWeakTopics(userId: string, subject?: Subject): TopicMastery[] {
  const masteries = getTopicMasteries(userId);
  let filtered = masteries.filter(m => m.masteryScore < 70);

  if (subject) {
    filtered = filtered.filter(m => m.subject === subject);
  }

  return filtered.sort((a, b) => a.masteryScore - b.masteryScore);
}

/**
 * Get strong topics (mastery >= 85%)
 */
export function getStrongTopics(userId: string, subject?: Subject): TopicMastery[] {
  const masteries = getTopicMasteries(userId);
  let filtered = masteries.filter(m => m.masteryScore >= 85);

  if (subject) {
    filtered = filtered.filter(m => m.subject === subject);
  }

  return filtered.sort((a, b) => b.masteryScore - a.masteryScore);
}

/**
 * Get average topics (70% <= mastery < 85%)
 */
export function getAverageTopics(userId: string, subject?: Subject): TopicMastery[] {
  const masteries = getTopicMasteries(userId);
  let filtered = masteries.filter(m => m.masteryScore >= 70 && m.masteryScore < 85);

  if (subject) {
    filtered = filtered.filter(m => m.subject === subject);
  }

  return filtered;
}

/**
 * Calculate overall performance metrics for a subject
 */
export function getSubjectPerformance(userId: string, subject: Subject): SubjectPerformance {
  const masteries = getTopicMasteries(userId).filter(m => m.subject === subject);

  const averageScore =
    masteries.length > 0
      ? Math.round(masteries.reduce((sum, m) => sum + m.masteryScore, 0) / masteries.length)
      : 0;

  const strengths = getStrongTopics(userId, subject).map(m => m.topic);
  const weaknesses = getWeakTopics(userId, subject).map(m => m.topic);

  const recommendations = generateRecommendations(userId, subject);

  return {
    subject,
    averageScore,
    topicMastery: masteries,
    strengths,
    weaknesses,
    recommendations: recommendations.map(r => r.description),
  };
}

/**
 * Get overall user performance across all subjects
 */
export function getUserPerformance(userId: string): UserPerformance {
  const subjects: Subject[] = ['physics', 'chemistry', 'mathematics'];
  const subjectPerformances = subjects.map(subject => getSubjectPerformance(userId, subject));

  const overallScore =
    subjectPerformances.length > 0
      ? Math.round(
        subjectPerformances.reduce((sum, sp) => sum + sp.averageScore, 0) / subjectPerformances.length
      )
      : 0;

  return {
    userId,
    overallScore,
    subjectPerformance: subjectPerformances,
    updatedAt: new Date(),
  };
}

/**
 * Get performance metrics for all topics
 */
export function getAllPerformanceMetrics(userId: string): PerformanceMetrics[] {
  const masteries = getTopicMasteries(userId);
  const recommendations = generateAllRecommendations(userId);

  return masteries.map(mastery => ({
    subject: mastery.subject,
    topic: mastery.topic,
    masteryScore: mastery.masteryScore,
    questionsAttempted: mastery.questionsAttempted,
    accuracy: mastery.questionsCorrect > 0
      ? Math.round((mastery.questionsCorrect / mastery.questionsAttempted) * 100)
      : 0,
    trend: mastery.trend || 'stable',
    strength: mastery.strength,
    recommendations: recommendations
      .filter(r => r.topic === mastery.topic)
      .map(r => r.description),
  }));
}

// ============================================================================
// Recommendation Engine
// ============================================================================

/**
 * Generate recommendations for a specific subject
 */
export function generateRecommendations(userId: string, subject: Subject): Recommendation[] {
  const weakTopics = getWeakTopics(userId, subject);
  const strongTopics = getStrongTopics(userId, subject);
  const masteries = getTopicMasteries(userId).filter(m => m.subject === subject);

  const recommendations: Recommendation[] = [];

  // Recommendations for weak topics
  weakTopics.slice(0, 3).forEach((topic, index) => {
    recommendations.push({
      id: `weak-${topic.id}`,
      type: 'practice',
      title: `Master ${topic.topic}`,
      description: `Your mastery in ${topic.topic} is ${topic.masteryScore}%. Focus on practicing more questions in this topic.`,
      subject,
      topic: topic.topic,
      priority: index === 0 ? 'high' : 'medium',
      actionUrl: `/practice?topic=${encodeURIComponent(topic.topic)}`,
    });
  });

  // Recommendations to maintain strong topics
  if (strongTopics.length > 0) {
    recommendations.push({
      id: 'maintain-strengths',
      type: 'revision',
      title: 'Maintain Your Strengths',
      description: `You are strong in ${strongTopics.slice(0, 2).map(t => t.topic).join(', ')}. Keep practicing to maintain your skills.`,
      subject,
      priority: 'low',
    });
  }

  // Overall subject recommendation
  const avgScore = masteries.length > 0
    ? Math.round(masteries.reduce((sum, m) => sum + m.masteryScore, 0) / masteries.length)
    : 0;

  if (avgScore < 60) {
    recommendations.push({
      id: `weak-subject-${subject}`,
      type: 'focus',
      title: `Improve ${subject.charAt(0).toUpperCase() + subject.slice(1)}`,
      description: `Your ${subject} performance (${avgScore}%) needs improvement. Consider taking a full test in this subject.`,
      subject,
      priority: 'high',
    });
  }

  return recommendations;
}

/**
 * Generate recommendations for all subjects
 */
export function generateAllRecommendations(userId: string): Recommendation[] {
  const subjects: Subject[] = ['physics', 'chemistry', 'mathematics'];
  const allRecommendations: Recommendation[] = [];

  subjects.forEach(subject => {
    allRecommendations.push(...generateRecommendations(userId, subject));
  });

  return allRecommendations.sort((a, b) => {
    const priorityMap = { high: 0, medium: 1, low: 2 };
    return priorityMap[a.priority] - priorityMap[b.priority];
  });
}

/**
 * Calculate accuracy for a set of attempts
 */
export function calculateAccuracy(attempts: TestAttempt[]): number {
  if (attempts.length === 0) return 0;
  const correct = attempts.filter(a => a.isCorrect).length;
  return Math.round((correct / attempts.length) * 100);
}

/**
 * Calculate average time spent per question
 */
export function calculateAverageTimePerQuestion(attempts: TestAttempt[]): number {
  if (attempts.length === 0) return 0;
  const totalTime = attempts.reduce((sum, a) => sum + a.timeSpent, 0);
  return Math.round(totalTime / attempts.length);
}

/**
 * Get recent attempts (last N attempts)
 */
export function getRecentAttempts(userId: string, limit: number = 10): TestAttempt[] {
  const data = getStoredPerformanceData(userId);
  return data.attempts.slice(-limit).reverse();
}

/**
 * Get attempts for a specific topic
 */
export function getAttemptsForTopic(userId: string, topic: string): TestAttempt[] {
  const data = getStoredPerformanceData(userId);
  return data.attempts.filter(a => a.questionId.includes(topic));
}

/**
 * Get performance trend for a topic
 */
export function getTopicTrend(userId: string, subject: Subject, topic: string): 'improving' | 'declining' | 'stable' {
  const attempts = getAttemptsForTopic(userId, topic);
  if (attempts.length < 4) return 'stable';

  const recent = attempts.slice(-5);
  const older = attempts.slice(-10, -5);

  const recentAccuracy = calculateAccuracy(recent);
  const olderAccuracy = calculateAccuracy(older);

  if (recentAccuracy > olderAccuracy + 5) return 'improving';
  if (recentAccuracy < olderAccuracy - 5) return 'declining';
  return 'stable';
}

/**
 * Get overall statistics
 */
export function getOverallStats(userId: string) {
  const data = getStoredPerformanceData(userId);
  const masteries = data.topicMasteries;

  const totalQuestionsAttempted = masteries.reduce((sum, m) => sum + m.questionsAttempted, 0);
  const totalQuestionsCorrect = masteries.reduce((sum, m) => sum + m.questionsCorrect, 0);
  const overallAccuracy = totalQuestionsAttempted > 0
    ? Math.round((totalQuestionsCorrect / totalQuestionsAttempted) * 100)
    : 0;

  const averageMastery = masteries.length > 0
    ? Math.round(masteries.reduce((sum, m) => sum + m.masteryScore, 0) / masteries.length)
    : 0;

  const weakTopicsCount = masteries.filter(m => m.strength === 'weak').length;
  const strongTopicsCount = masteries.filter(m => m.strength === 'strong').length;

  return {
    totalQuestionsAttempted,
    totalQuestionsCorrect,
    overallAccuracy,
    averageMastery,
    weakTopicsCount,
    strongTopicsCount,
    totalTopicsCovered: masteries.length,
  };
}

/**
 * Reset all performance data for a user
 */
export function resetPerformanceData(userId: string): void {
  localStorage.removeItem(`${STORAGE_KEY}-${userId}`);
}
