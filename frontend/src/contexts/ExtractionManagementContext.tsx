/**
 * Extraction Management State Context
 * Manages state for the extraction management module
 */

import React, { createContext, useContext, useReducer, useCallback } from 'react';
import {
  ExtractionJob,
  RawQuestion,
  ExtractionJobDetail,
  JobStatistics,
  QuestionFilters,
  JobFilters,
  SortConfig,
  PaginationState,
} from '@/types/admin';

interface ExtractionManagementState {
  // List view state
  jobs: ExtractionJob[];
  jobsLoading: boolean;
  jobsError: Error | null;
  jobFilters: JobFilters;
  jobSort: SortConfig;
  jobPagination: PaginationState;

  // Detail view state
  currentJob: ExtractionJobDetail | null;
  currentJobLoading: boolean;
  currentJobError: Error | null;

  // Questions state
  questions: RawQuestion[];
  questionsLoading: boolean;
  questionsError: Error | null;
  questionFilters: QuestionFilters;
  questionPagination: PaginationState;

  // Selection state
  selectedQuestionIds: Set<string>;

  // Operation state
  operationInProgress: boolean;
  operationError: Error | null;
}

type Action =
  | { type: 'SET_JOBS'; payload: ExtractionJob[] }
  | { type: 'SET_JOBS_LOADING'; payload: boolean }
  | { type: 'SET_JOBS_ERROR'; payload: Error | null }
  | { type: 'SET_JOB_FILTERS'; payload: JobFilters }
  | { type: 'SET_JOB_SORT'; payload: SortConfig }
  | { type: 'SET_JOB_PAGINATION'; payload: PaginationState }
  | { type: 'SET_CURRENT_JOB'; payload: ExtractionJobDetail | null }
  | { type: 'SET_CURRENT_JOB_LOADING'; payload: boolean }
  | { type: 'SET_CURRENT_JOB_ERROR'; payload: Error | null }
  | { type: 'SET_QUESTIONS'; payload: RawQuestion[] }
  | { type: 'SET_QUESTIONS_LOADING'; payload: boolean }
  | { type: 'SET_QUESTIONS_ERROR'; payload: Error | null }
  | { type: 'SET_QUESTION_FILTERS'; payload: QuestionFilters }
  | { type: 'SET_QUESTION_PAGINATION'; payload: PaginationState }
  | { type: 'SELECT_QUESTION'; payload: string }
  | { type: 'DESELECT_QUESTION'; payload: string }
  | { type: 'SELECT_ALL_QUESTIONS'; payload: string[] }
  | { type: 'DESELECT_ALL_QUESTIONS' }
  | { type: 'SET_OPERATION_IN_PROGRESS'; payload: boolean }
  | { type: 'SET_OPERATION_ERROR'; payload: Error | null }
  | { type: 'UPDATE_QUESTION'; payload: RawQuestion }
  | { type: 'REMOVE_QUESTION'; payload: string }
  | { type: 'RESET_STATE' }
  | { type: 'UPDATE_JOB_IN_LIST'; payload: { id: string; updates: Partial<ExtractionJob> } }
  | { type: 'UPSERT_JOB_IN_LIST'; payload: ExtractionJob }
  | { type: 'REMOVE_JOB_FROM_LIST'; payload: string };

const initialState: ExtractionManagementState = {
  jobs: [],
  jobsLoading: false,
  jobsError: null,
  jobFilters: {},
  jobSort: { field: 'created_at', order: 'desc' },
  jobPagination: { page: 1, page_size: 50, total: 0 },

  currentJob: null,
  currentJobLoading: false,
  currentJobError: null,

  questions: [],
  questionsLoading: false,
  questionsError: null,
  questionFilters: {},
  questionPagination: { page: 1, page_size: 50, total: 0 },

  selectedQuestionIds: new Set(),

  operationInProgress: false,
  operationError: null,
};

function extractionManagementReducer(
  state: ExtractionManagementState,
  action: Action
): ExtractionManagementState {
  switch (action.type) {
    case 'SET_JOBS':
      return { ...state, jobs: action.payload };
    case 'SET_JOBS_LOADING':
      return { ...state, jobsLoading: action.payload };
    case 'SET_JOBS_ERROR':
      return { ...state, jobsError: action.payload };
    case 'SET_JOB_FILTERS':
      return { ...state, jobFilters: action.payload, jobPagination: { ...state.jobPagination, page: 1 } };
    case 'SET_JOB_SORT':
      return { ...state, jobSort: action.payload };
    case 'SET_JOB_PAGINATION':
      return { ...state, jobPagination: action.payload };
    case 'SET_CURRENT_JOB':
      return { ...state, currentJob: action.payload };
    case 'SET_CURRENT_JOB_LOADING':
      return { ...state, currentJobLoading: action.payload };
    case 'SET_CURRENT_JOB_ERROR':
      return { ...state, currentJobError: action.payload };
    case 'SET_QUESTIONS':
      return { ...state, questions: action.payload };
    case 'SET_QUESTIONS_LOADING':
      return { ...state, questionsLoading: action.payload };
    case 'SET_QUESTIONS_ERROR':
      return { ...state, questionsError: action.payload };
    case 'SET_QUESTION_FILTERS':
      return { ...state, questionFilters: action.payload, questionPagination: { ...state.questionPagination, page: 1 } };
    case 'SET_QUESTION_PAGINATION':
      return { ...state, questionPagination: action.payload };
    case 'SELECT_QUESTION': {
      const newSelected = new Set(state.selectedQuestionIds);
      newSelected.add(action.payload);
      return { ...state, selectedQuestionIds: newSelected };
    }
    case 'DESELECT_QUESTION': {
      const newSelected = new Set(state.selectedQuestionIds);
      newSelected.delete(action.payload);
      return { ...state, selectedQuestionIds: newSelected };
    }
    case 'SELECT_ALL_QUESTIONS':
      return { ...state, selectedQuestionIds: new Set(action.payload) };
    case 'DESELECT_ALL_QUESTIONS':
      return { ...state, selectedQuestionIds: new Set() };
    case 'SET_OPERATION_IN_PROGRESS':
      return { ...state, operationInProgress: action.payload };
    case 'SET_OPERATION_ERROR':
      return { ...state, operationError: action.payload };
    case 'UPDATE_QUESTION':
      return {
        ...state,
        questions: state.questions.map((q) => (q.id === action.payload.id ? action.payload : q)),
      };
    case 'REMOVE_QUESTION':
      return {
        ...state,
        questions: state.questions.filter((q) => q.id !== action.payload),
        selectedQuestionIds: new Set(
          Array.from(state.selectedQuestionIds).filter((id) => id !== action.payload)
        ),
      };
    case 'RESET_STATE':
      return initialState;
    case 'UPDATE_JOB_IN_LIST':
      return {
        ...state,
        jobs: state.jobs.map((j) =>
          j.id === action.payload.id ? { ...j, ...action.payload.updates } : j
        ),
      };
    case 'UPSERT_JOB_IN_LIST':
      return {
        ...state,
        jobs: state.jobs.some((j) => j.id === action.payload.id)
          ? state.jobs.map((j) => (j.id === action.payload.id ? action.payload : j))
          : [action.payload, ...state.jobs],
      };
    case 'REMOVE_JOB_FROM_LIST':
      return {
        ...state,
        jobs: state.jobs.filter((j) => j.id !== action.payload),
      };
    default:
      return state;
  }
}

interface ExtractionManagementContextType {
  state: ExtractionManagementState;
  setJobs: (jobs: ExtractionJob[]) => void;
  setJobsLoading: (loading: boolean) => void;
  setJobsError: (error: Error | null) => void;
  setJobFilters: (filters: JobFilters) => void;
  setJobSort: (sort: SortConfig) => void;
  setJobPagination: (pagination: PaginationState) => void;
  setCurrentJob: (job: ExtractionJobDetail | null) => void;
  setCurrentJobLoading: (loading: boolean) => void;
  setCurrentJobError: (error: Error | null) => void;
  setQuestions: (questions: RawQuestion[]) => void;
  setQuestionsLoading: (loading: boolean) => void;
  setQuestionsError: (error: Error | null) => void;
  setQuestionFilters: (filters: QuestionFilters) => void;
  setQuestionPagination: (pagination: PaginationState) => void;
  selectQuestion: (questionId: string) => void;
  deselectQuestion: (questionId: string) => void;
  selectAllQuestions: (questionIds: string[]) => void;
  deselectAllQuestions: () => void;
  setOperationInProgress: (inProgress: boolean) => void;
  setOperationError: (error: Error | null) => void;
  updateQuestion: (question: RawQuestion) => void;
  removeQuestion: (questionId: string) => void;
  resetState: () => void;
  updateJobInList: (jobId: string, updates: Partial<ExtractionJob>) => void;
  upsertJobInList: (job: ExtractionJob) => void;
  removeJobFromList: (jobId: string) => void;
}

const ExtractionManagementContext = createContext<ExtractionManagementContextType | undefined>(undefined);

export function ExtractionManagementProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(extractionManagementReducer, initialState);

  const setJobs = useCallback((jobs: ExtractionJob[]) => {
    dispatch({ type: 'SET_JOBS', payload: jobs });
  }, []);

  const setJobsLoading = useCallback((loading: boolean) => {
    dispatch({ type: 'SET_JOBS_LOADING', payload: loading });
  }, []);

  const setJobsError = useCallback((error: Error | null) => {
    dispatch({ type: 'SET_JOBS_ERROR', payload: error });
  }, []);

  const setJobFilters = useCallback((filters: JobFilters) => {
    dispatch({ type: 'SET_JOB_FILTERS', payload: filters });
  }, []);

  const setJobSort = useCallback((sort: SortConfig) => {
    dispatch({ type: 'SET_JOB_SORT', payload: sort });
  }, []);

  const setJobPagination = useCallback((pagination: PaginationState) => {
    dispatch({ type: 'SET_JOB_PAGINATION', payload: pagination });
  }, []);

  const setCurrentJob = useCallback((job: ExtractionJobDetail | null) => {
    dispatch({ type: 'SET_CURRENT_JOB', payload: job });
  }, []);

  const setCurrentJobLoading = useCallback((loading: boolean) => {
    dispatch({ type: 'SET_CURRENT_JOB_LOADING', payload: loading });
  }, []);

  const setCurrentJobError = useCallback((error: Error | null) => {
    dispatch({ type: 'SET_CURRENT_JOB_ERROR', payload: error });
  }, []);

  const setQuestions = useCallback((questions: RawQuestion[]) => {
    dispatch({ type: 'SET_QUESTIONS', payload: questions });
  }, []);

  const setQuestionsLoading = useCallback((loading: boolean) => {
    dispatch({ type: 'SET_QUESTIONS_LOADING', payload: loading });
  }, []);

  const setQuestionsError = useCallback((error: Error | null) => {
    dispatch({ type: 'SET_QUESTIONS_ERROR', payload: error });
  }, []);

  const setQuestionFilters = useCallback((filters: QuestionFilters) => {
    dispatch({ type: 'SET_QUESTION_FILTERS', payload: filters });
  }, []);

  const setQuestionPagination = useCallback((pagination: PaginationState) => {
    dispatch({ type: 'SET_QUESTION_PAGINATION', payload: pagination });
  }, []);

  const selectQuestion = useCallback((questionId: string) => {
    dispatch({ type: 'SELECT_QUESTION', payload: questionId });
  }, []);

  const deselectQuestion = useCallback((questionId: string) => {
    dispatch({ type: 'DESELECT_QUESTION', payload: questionId });
  }, []);

  const selectAllQuestions = useCallback((questionIds: string[]) => {
    dispatch({ type: 'SELECT_ALL_QUESTIONS', payload: questionIds });
  }, []);

  const deselectAllQuestions = useCallback(() => {
    dispatch({ type: 'DESELECT_ALL_QUESTIONS' });
  }, []);

  const setOperationInProgress = useCallback((inProgress: boolean) => {
    dispatch({ type: 'SET_OPERATION_IN_PROGRESS', payload: inProgress });
  }, []);

  const setOperationError = useCallback((error: Error | null) => {
    dispatch({ type: 'SET_OPERATION_ERROR', payload: error });
  }, []);

  const updateQuestion = useCallback((question: RawQuestion) => {
    dispatch({ type: 'UPDATE_QUESTION', payload: question });
  }, []);

  const removeQuestion = useCallback((questionId: string) => {
    dispatch({ type: 'REMOVE_QUESTION', payload: questionId });
  }, []);

  const resetState = useCallback(() => {
    dispatch({ type: 'RESET_STATE' });
  }, []);

  const updateJobInList = useCallback((jobId: string, updates: Partial<ExtractionJob>) => {
    dispatch({ type: 'UPDATE_JOB_IN_LIST', payload: { id: jobId, updates } });
  }, []);

  const upsertJobInList = useCallback((job: ExtractionJob) => {
    dispatch({ type: 'UPSERT_JOB_IN_LIST', payload: job });
  }, []);

  const removeJobFromList = useCallback((jobId: string) => {
    dispatch({ type: 'REMOVE_JOB_FROM_LIST', payload: jobId });
  }, []);

  const value: ExtractionManagementContextType = {
    state,
    setJobs,
    setJobsLoading,
    setJobsError,
    setJobFilters,
    setJobSort,
    setJobPagination,
    setCurrentJob,
    setCurrentJobLoading,
    setCurrentJobError,
    setQuestions,
    setQuestionsLoading,
    setQuestionsError,
    setQuestionFilters,
    setQuestionPagination,
    selectQuestion,
    deselectQuestion,
    selectAllQuestions,
    deselectAllQuestions,
    setOperationInProgress,
    setOperationError,
    updateQuestion,
    removeQuestion,
    resetState,
    updateJobInList,
    upsertJobInList,
    removeJobFromList,
  };

  return (
    <ExtractionManagementContext.Provider value={value}>
      {children}
    </ExtractionManagementContext.Provider>
  );
}

export function useExtractionManagement() {
  const context = useContext(ExtractionManagementContext);
  if (!context) {
    throw new Error('useExtractionManagement must be used within ExtractionManagementProvider');
  }
  return context;
}
