import { Question, Subject, Difficulty } from '@/types';
import { questionBankService } from './mockData';
import {
  getWeakTopics,
  getStrongTopics,
  getTopicMasteries,
} from './performanceService';

export interface AdaptiveTestConfig {
  numberOfQuestions: number;
  focusOnWeakAreas: number; // 0-100, percentage of weak questions
  includeStrongAreas: boolean;
  subject?: Subject;
  userId: string;
}

export interface AdaptiveTestResult {
  questions: Question[];
  reasoning: string;
  composition: {
    weakQuestions: number;
    strongQuestions: number;
    mediumQuestions: number;
  };
}

/**
 * Calculate difficulty for a question based on user performance
 */
function calculateQuestionDifficulty(
  userId: string,
  question: Question
): Difficulty {
  const masteries = getTopicMasteries(userId);
  const topicMastery = masteries.find(m => m.topic === question.topic);

  if (!topicMastery) {
    // No history, use original difficulty
    return question.difficulty;
  }

  const masteryScore = topicMastery.masteryScore;

  // Adjust difficulty based on mastery
  if (masteryScore < 40) {
    // Very weak - increase difficulty gradually
    return question.difficulty === 'easy' ? 'easy' : 'medium';
  } else if (masteryScore < 60) {
    // Weak - slightly increase difficulty
    return question.difficulty === 'hard' ? 'hard' : 'medium';
  } else if (masteryScore < 75) {
    // Average - maintain difficulty
    return question.difficulty;
  } else if (masteryScore < 90) {
    // Strong - increase difficulty
    return question.difficulty === 'easy' ? 'medium' : question.difficulty === 'medium' ? 'hard' : 'hard';
  } else {
    // Very strong - focus on hard questions
    return 'hard';
  }
}

/**
 * Select questions by distribution - weak areas focus
 */
function selectByWeakAreaFocus(
  allQuestions: Question[],
  weakTopicsList: string[],
  strongTopicsList: string[],
  config: AdaptiveTestConfig
): { weakQuestions: Question[]; strongQuestions: Question[] } {
  const weakQuestionCount = Math.ceil(
    (config.numberOfQuestions * config.focusOnWeakAreas) / 100
  );
  const strongQuestionCount = config.numberOfQuestions - weakQuestionCount;

  // Get questions from weak topics
  const weakQuestions = allQuestions
    .filter(q => weakTopicsList.includes(q.topic))
    .sort(() => Math.random() - 0.5)
    .slice(0, weakQuestionCount);

  // If not enough weak questions, fill with medium difficulty
  if (weakQuestions.length < weakQuestionCount) {
    const mediumQuestions = allQuestions
      .filter(
        q =>
          !weakTopicsList.includes(q.topic) &&
          !strongTopicsList.includes(q.topic) &&
          !weakQuestions.find(wq => wq.id === q.id)
      )
      .sort(() => Math.random() - 0.5)
      .slice(0, weakQuestionCount - weakQuestions.length);
    weakQuestions.push(...mediumQuestions);
  }

  // Get questions from strong topics if enabled
  let strongQuestions: Question[] = [];
  if (config.includeStrongAreas && strongTopicsList.length > 0) {
    strongQuestions = allQuestions
      .filter(
        q =>
          strongTopicsList.includes(q.topic) &&
          !weakQuestions.find(wq => wq.id === q.id)
      )
      .sort(() => Math.random() - 0.5)
      .slice(0, strongQuestionCount);
  }

  // If not enough strong questions, fill with random
  if (strongQuestions.length < strongQuestionCount) {
    const remaining = allQuestions
      .filter(
        q =>
          !weakQuestions.find(wq => wq.id === q.id) &&
          !strongQuestions.find(sq => sq.id === q.id)
      )
      .sort(() => Math.random() - 0.5)
      .slice(0, strongQuestionCount - strongQuestions.length);
    strongQuestions.push(...remaining);
  }

  return { weakQuestions, strongQuestions };
}

/**
 * Main adaptive algorithm for generating test questions
 */
export function generateAdaptiveTest(
  config: AdaptiveTestConfig
): AdaptiveTestResult {
  const {
    numberOfQuestions,
    focusOnWeakAreas,
    includeStrongAreas,
    subject,
    userId,
  } = config;

  // Get user's topic mastery data
  const weakTopics = getWeakTopics(userId, subject);
  const strongTopics = getStrongTopics(userId, subject);
  const masteries = getTopicMasteries(userId).filter(m =>
    subject ? m.subject === subject : true
  );

  const weakTopicsList = weakTopics.map(t => t.topic);
  const strongTopicsList = strongTopics.map(t => t.topic);

  // Get all available questions
  let allQuestions = subject
    ? questionBankService.getQuestionsBySubject(subject)
    : questionBankService.getAllQuestions();

  // If user has no performance history, use default distribution
  if (masteries.length === 0) {
    const randomQuestions = allQuestions
      .sort(() => Math.random() - 0.5)
      .slice(0, numberOfQuestions);

    return {
      questions: randomQuestions,
      reasoning:
        'No performance history found. Generating random question set for baseline assessment.',
      composition: {
        weakQuestions: 0,
        strongQuestions: 0,
        mediumQuestions: numberOfQuestions,
      },
    };
  }

  // Select questions based on weak/strong area focus
  const { weakQuestions, strongQuestions } = selectByWeakAreaFocus(
    allQuestions,
    weakTopicsList,
    strongTopicsList,
    config
  );

  // Combine and shuffle
  const selectedQuestions = [...weakQuestions, ...strongQuestions]
    .sort(() => Math.random() - 0.5)
    .slice(0, numberOfQuestions);

  // Ensure we have exactly the requested number of questions
  if (selectedQuestions.length < numberOfQuestions) {
    const remaining = allQuestions
      .filter(q => !selectedQuestions.find(sq => sq.id === q.id))
      .sort(() => Math.random() - 0.5)
      .slice(0, numberOfQuestions - selectedQuestions.length);
    selectedQuestions.push(...remaining);
  }

  // Build reasoning string
  let reasoning = `Generated ${numberOfQuestions} questions: `;
  const composition = {
    weakQuestions: weakQuestions.length,
    strongQuestions: strongQuestions.length,
    mediumQuestions: selectedQuestions.length - weakQuestions.length - strongQuestions.length,
  };

  if (weakTopics.length > 0) {
    reasoning += `${composition.weakQuestions} from weak topics (${weakTopicsList.slice(0, 2).join(', ')}), `;
  }
  if (strongTopics.length > 0 && includeStrongAreas) {
    reasoning += `${composition.strongQuestions} from strong topics (${strongTopicsList.slice(0, 2).join(', ')}), `;
  }
  reasoning += `${composition.mediumQuestions} from other topics. Focus on weak areas: ${focusOnWeakAreas}%.`;

  return {
    questions: selectedQuestions,
    reasoning,
    composition,
  };
}

/**
 * Get difficulty distribution recommendations
 */
export function getDifficultyDistribution(
  userId: string
): Record<Difficulty, number> {
  const masteries = getTopicMasteries(userId);

  if (masteries.length === 0) {
    // Default for new users
    return {
      easy: 33,
      medium: 34,
      hard: 33,
    };
  }

  const averageMastery =
    masteries.reduce((sum, m) => sum + m.masteryScore, 0) / masteries.length;

  // Adjust distribution based on overall performance
  if (averageMastery < 50) {
    // Struggling - mostly easy/medium
    return {
      easy: 50,
      medium: 40,
      hard: 10,
    };
  } else if (averageMastery < 70) {
    // Average - balanced
    return {
      easy: 30,
      medium: 50,
      hard: 20,
    };
  } else if (averageMastery < 85) {
    // Good - more medium/hard
    return {
      easy: 20,
      medium: 40,
      hard: 40,
    };
  } else {
    // Excellent - mostly hard
    return {
      easy: 10,
      medium: 30,
      hard: 60,
    };
  }
}

/**
 * Get recommended next action based on performance
 */
export function getNextRecommendedAction(userId: string): {
  action: string;
  priority: 'high' | 'medium' | 'low';
  topic?: string;
} {
  const weakTopics = getWeakTopics(userId);

  if (weakTopics.length === 0) {
    return {
      action: 'Take a full mock test to assess overall readiness',
      priority: 'medium',
    };
  }

  const lowestMasteryTopic = weakTopics[0];

  if (lowestMasteryTopic.masteryScore < 40) {
    return {
      action: `Focus on ${lowestMasteryTopic.topic} - Your mastery is ${lowestMasteryTopic.masteryScore}%`,
      priority: 'high',
      topic: lowestMasteryTopic.topic,
    };
  }

  if (lowestMasteryTopic.masteryScore < 70) {
    return {
      action: `Practice more on ${lowestMasteryTopic.topic} to improve mastery`,
      priority: 'medium',
      topic: lowestMasteryTopic.topic,
    };
  }

  return {
    action: 'Continue consistent practice across all topics',
    priority: 'low',
  };
}

/**
 * Calculate estimated test duration
 */
export function estimateTestDuration(numberOfQuestions: number): number {
  // Average 2-3 minutes per question (accounting for reading and thinking)
  const avgTimePerQuestion = 2.5;
  return Math.ceil(numberOfQuestions * avgTimePerQuestion);
}
