export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          email: string
          name: string
          phone: string | null
          grade: '9' | '10' | '11' | '12'
          syllabus: 'cbse' | 'icse' | 'state'
          target_exam: string
          role: 'user' | 'admin'
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          name: string
          phone?: string | null
          grade: '9' | '10' | '11' | '12'
          syllabus: 'cbse' | 'icse' | 'state'
          target_exam: string
          role?: 'user' | 'admin'
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          name?: string
          phone?: string | null
          grade?: '9' | '10' | '11' | '12'
          syllabus?: 'cbse' | 'icse' | 'state'
          target_exam?: string
          role?: 'user' | 'admin'
          created_at?: string
          updated_at?: string
        }
      }
      user_preferences: {
        Row: {
          id: string
          user_id: string
          daily_goal: number
          focus_subjects: Json
          difficulty_level: 'easy' | 'adaptive' | 'hard'
          notifications_enabled: boolean
          daily_reminders: boolean
          dark_mode: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          daily_goal?: number
          focus_subjects?: Json
          difficulty_level?: 'easy' | 'adaptive' | 'hard'
          notifications_enabled?: boolean
          daily_reminders?: boolean
          dark_mode?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          daily_goal?: number
          focus_subjects?: Json
          difficulty_level?: 'easy' | 'adaptive' | 'hard'
          notifications_enabled?: boolean
          daily_reminders?: boolean
          dark_mode?: boolean
          created_at?: string
          updated_at?: string
        }
      }
      topic_mastery: {
        Row: {
          id: string
          user_id: string
          subject: 'physics' | 'chemistry' | 'mathematics'
          topic: string
          mastery_score: number
          questions_attempted: number
          questions_correct: number
          last_attempt_date: string
          trend: 'improving' | 'declining' | 'stable' | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          subject: 'physics' | 'chemistry' | 'mathematics'
          topic: string
          mastery_score?: number
          questions_attempted?: number
          questions_correct?: number
          last_attempt_date?: string
          trend?: 'improving' | 'declining' | 'stable' | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          subject?: 'physics' | 'chemistry' | 'mathematics'
          topic?: string
          mastery_score?: number
          questions_attempted?: number
          questions_correct?: number
          last_attempt_date?: string
          trend?: 'improving' | 'declining' | 'stable' | null
          created_at?: string
          updated_at?: string
        }
      }
      tests: {
        Row: {
          id: string
          user_id: string
          title: string
          type: 'full' | 'topic' | 'practice' | 'adaptive' | 'uploaded'
          subject: 'physics' | 'chemistry' | 'mathematics' | null
          status: 'completed' | 'in_progress' | 'upcoming' | 'paused'
          duration: number
          scheduled_at: string | null
          started_at: string | null
          completed_at: string | null
          score: number | null
          max_score: number | null
          questions: Json
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          title: string
          type: 'full' | 'topic' | 'practice' | 'adaptive' | 'uploaded'
          subject?: 'physics' | 'chemistry' | 'mathematics' | null
          status?: 'completed' | 'in_progress' | 'upcoming' | 'paused'
          duration: number
          scheduled_at?: string | null
          started_at?: string | null
          completed_at?: string | null
          score?: number | null
          max_score?: number | null
          questions?: Json
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          title?: string
          type?: 'full' | 'topic' | 'practice' | 'adaptive' | 'uploaded'
          subject?: 'physics' | 'chemistry' | 'mathematics' | null
          status?: 'completed' | 'in_progress' | 'upcoming' | 'paused'
          duration?: number
          scheduled_at?: string | null
          started_at?: string | null
          completed_at?: string | null
          score?: number | null
          max_score?: number | null
          questions?: Json
          created_at?: string
          updated_at?: string
        }
      }
      test_attempts: {
        Row: {
          id: string
          test_id: string
          user_id: string
          question_id: string
          selected_answer: string | null
          is_correct: boolean
          time_spent: number
          marked_for_review: boolean
          created_at: string
        }
        Insert: {
          id?: string
          test_id: string
          user_id: string
          question_id: string
          selected_answer?: string | null
          is_correct?: boolean
          time_spent?: number
          marked_for_review?: boolean
          created_at?: string
        }
        Update: {
          id?: string
          test_id?: string
          user_id?: string
          question_id?: string
          selected_answer?: string | null
          is_correct?: boolean
          time_spent?: number
          marked_for_review?: boolean
          created_at?: string
        }
      }
      uploaded_tests: {
        Row: {
          id: string
          user_id: string
          test_image_url: string
          response_image_url: string | null
          extracted_questions: Json
          processing_status: 'pending' | 'processing' | 'completed' | 'failed'
          error_message: string | null
          uploaded_at: string
          processed_at: string | null
        }
        Insert: {
          id?: string
          user_id: string
          test_image_url: string
          response_image_url?: string | null
          extracted_questions?: Json
          processing_status?: 'pending' | 'processing' | 'completed' | 'failed'
          error_message?: string | null
          uploaded_at?: string
          processed_at?: string | null
        }
        Update: {
          id?: string
          user_id?: string
          test_image_url?: string
          response_image_url?: string | null
          extracted_questions?: Json
          processing_status?: 'pending' | 'processing' | 'completed' | 'failed'
          error_message?: string | null
          uploaded_at?: string
          processed_at?: string | null
        }
      }
      user_activity: {
        Row: {
          id: string
          user_id: string
          date: string
          questions_solved: number
          time_spent: number
          tests_taken: number
          streak_count: number
          created_at: string
        }
        Insert: {
          id?: string
          user_id: string
          date: string
          questions_solved?: number
          time_spent?: number
          tests_taken?: number
          streak_count?: number
          created_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          date?: string
          questions_solved?: number
          time_spent?: number
          tests_taken?: number
          streak_count?: number
          created_at?: string
        }
      }
      revision_capsules: {
        Row: {
          id: string
          user_id: string
          subject: 'physics' | 'chemistry' | 'mathematics'
          topics: Json
          generated_at: string
          expires_at: string | null
          focus_on_weak: boolean
          include_formulas: boolean
          include_common_mistakes: boolean
        }
        Insert: {
          id?: string
          user_id: string
          subject: 'physics' | 'chemistry' | 'mathematics'
          topics?: Json
          generated_at?: string
          expires_at?: string | null
          focus_on_weak?: boolean
          include_formulas?: boolean
          include_common_mistakes?: boolean
        }
        Update: {
          id?: string
          user_id?: string
          subject?: 'physics' | 'chemistry' | 'mathematics'
          topics?: Json
          generated_at?: string
          expires_at?: string | null
          focus_on_weak?: boolean
          include_formulas?: boolean
          include_common_mistakes?: boolean
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
}
