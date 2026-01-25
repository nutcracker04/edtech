// User Profile Types
export type Grade = '9' | '10' | '11' | '12';
export type TargetExam = 'jee-main' | 'jee-advanced' | 'both';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  grade: Grade;
  targetExam: TargetExam;
  createdAt: Date;
  updatedAt: Date;
  preferences?: {
    dailyGoal?: number;
    focusSubjects?: string[];
    difficultyLevel?: 'easy' | 'adaptive' | 'hard';
  };
}

// Question Types
export type Subject = 'physics' | 'chemistry' | 'mathematics';
export type Difficulty = 'easy' | 'medium' | 'hard';

export interface Option {
  id: string;
  text: string;
}

export type AnswerType =
  | 'single_choice'    // Traditional MCQ (one correct answer)
  | 'multiple_choice'  // Multiple correct answers
  | 'integer'          // Numeric input
  | 'match_following'  // Match items from two columns
  | 'assertion_reason' // Assertion-Reason type
  | 'comprehension';   // Comprehension passage

export interface Question {
  id: string;
  question: string;
  options: Option[];
  correctAnswer: string | string[]; // Can be array for multiple_choice
  explanation: string;
  difficulty: Difficulty;
  topic: string;
  subject: Subject;
  gradeLevel: Grade[];
  tags?: string[];
  source?: string;
  answerType?: AnswerType; // Default: 'single_choice'
  // For integer type
  integerRange?: { min: number; max: number };
  // For match_following type
  leftColumn?: Array<{ id: string; text: string }>;
  rightColumn?: Array<{ id: string; text: string }>;
  // For multiple_choice
  minSelections?: number;
  maxSelections?: number;
}

// Test Types
export type TestType = 'full' | 'topic' | 'practice' | 'adaptive';
export type TestStatus = 'completed' | 'in_progress' | 'upcoming' | 'paused';

export interface Test {
  id: string;
  title: string;
  subject?: Subject;
  type: TestType;
  questions: Question[];
  duration: number; // in minutes
  status: TestStatus;
  score?: number;
  maxScore?: number;
  createdAt: Date;
  updatedAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  userId?: string;
}

export interface TestAttempt {
  id: string;
  testId: string;
  userId: string;
  questionId: string;
  selectedAnswer: string | null;
  isCorrect: boolean;
  timeSpent: number; // in seconds
  markedForReview: boolean;
  createdAt: Date;
}

export interface TestSession {
  id: string;
  testId: string;
  userId: string;
  attempts: TestAttempt[];
  status: TestStatus;
  startedAt: Date;
  completedAt?: Date;
  totalScore?: number;
  totalMaxScore?: number;
}

// Topic Mastery Types
export interface TopicMastery {
  id: string;
  userId: string;
  subject: Subject;
  topic: string;
  masteryScore: number; // 0-100
  questionsAttempted: number;
  questionsCorrect: number;
  lastAttemptDate: Date;
  trend?: 'improving' | 'declining' | 'stable';
  strength?: 'weak' | 'average' | 'strong';
}


// Performance Metrics Types
export interface PerformanceMetrics {
  subject: Subject;
  topic: string;
  masteryScore: number; // 0-100
  questionsAttempted: number;
  accuracy: number; // 0-100
  trend?: 'improving' | 'declining' | 'stable';
  strength: 'weak' | 'average' | 'strong';
  recommendations: string[];
}

export interface SubjectPerformance {
  subject: Subject;
  averageScore: number;
  topicMastery: TopicMastery[];
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

export interface UserPerformance {
  userId: string;
  overallScore: number;
  subjectPerformance: SubjectPerformance[];
  updatedAt: Date;
}

// Practice Session Types
export interface PracticeSession {
  id: string;
  userId: string;
  mode: 'adaptive' | 'topic-focus' | 'subject-focus' | 'grade-based';
  subject?: Subject;
  topic?: string;
  questions: Question[];
  attempts: TestAttempt[];
  status: 'in_progress' | 'completed';
  startedAt: Date;
  completedAt?: Date;
}

// Chart Data Types
export interface RadarDataPoint {
  subject: string;
  score: number;
  fullMark: number;
}

export interface ChartDataPoint {
  [key: string]: string | number;
}

// Filter and Selection Types
export interface TestFilterOptions {
  status?: TestStatus[];
  type?: TestType[];
  subject?: Subject[];
  dateRange?: {
    start: Date;
    end: Date;
  };
}

export interface QuestionFilterOptions {
  subject?: Subject;
  topic?: string;
  difficulty?: Difficulty[];
  gradeLevel?: Grade[];
  limit?: number;
}

export interface TestCreationConfig {
  title: string;
  type: TestType;
  subject?: Subject;
  topics?: string[];
  numberOfQuestions: number;
  duration: number;
  adaptiveConfig?: {
    focusOnWeakAreas: number; // 0-100
    includeStrongAreas: boolean;
  };
}

// Recommendation Types
export interface Recommendation {
  id: string;
  type: 'practice' | 'focus';
  title: string;
  description: string;
  subject?: Subject;
  topic?: string;
  priority: 'high' | 'medium' | 'low';
  actionUrl?: string;
}

// Stats Types
export interface StatsCard {
  title: string;
  value: string | number;
  icon: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string | number;
}
