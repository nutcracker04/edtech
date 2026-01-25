-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE public.users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  phone TEXT,
  grade TEXT NOT NULL CHECK (grade IN ('9', '10', '11', '12')),
  syllabus TEXT NOT NULL CHECK (syllabus IN ('cbse', 'icse', 'state')),
  target_exam TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User preferences table
CREATE TABLE public.user_preferences (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  daily_goal INTEGER DEFAULT 20,
  focus_subjects JSONB DEFAULT '[]'::jsonb,
  difficulty_level TEXT DEFAULT 'adaptive' CHECK (difficulty_level IN ('easy', 'adaptive', 'hard')),
  notifications_enabled BOOLEAN DEFAULT true,
  daily_reminders BOOLEAN DEFAULT true,
  dark_mode BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Topic mastery table
CREATE TABLE public.topic_mastery (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  subject TEXT NOT NULL CHECK (subject IN ('physics', 'chemistry', 'mathematics')),
  topic TEXT NOT NULL,
  mastery_score NUMERIC(5,2) DEFAULT 0 CHECK (mastery_score >= 0 AND mastery_score <= 100),
  questions_attempted INTEGER DEFAULT 0,
  questions_correct INTEGER DEFAULT 0,
  last_attempt_date TIMESTAMPTZ DEFAULT NOW(),
  trend TEXT CHECK (trend IN ('improving', 'declining', 'stable')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, subject, topic)
);

-- Tests table
CREATE TABLE public.tests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('full', 'topic', 'practice', 'adaptive', 'uploaded')),
  subject TEXT CHECK (subject IN ('physics', 'chemistry', 'mathematics')),
  status TEXT NOT NULL DEFAULT 'upcoming' CHECK (status IN ('completed', 'in_progress', 'upcoming', 'paused')),
  duration INTEGER NOT NULL, -- in minutes
  scheduled_at TIMESTAMPTZ,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  score NUMERIC(5,2),
  max_score NUMERIC(5,2),
  questions JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Test attempts table
CREATE TABLE public.test_attempts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  test_id UUID NOT NULL REFERENCES public.tests(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL,
  selected_answer TEXT,
  is_correct BOOLEAN NOT NULL DEFAULT false,
  time_spent INTEGER DEFAULT 0, -- in seconds
  marked_for_review BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Uploaded tests table
CREATE TABLE public.uploaded_tests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  test_image_url TEXT NOT NULL,
  response_image_url TEXT,
  extracted_questions JSONB DEFAULT '[]'::jsonb,
  processing_status TEXT NOT NULL DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
  error_message TEXT,
  uploaded_at TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ
);

-- User activity table (for streak tracking)
CREATE TABLE public.user_activity (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  questions_solved INTEGER DEFAULT 0,
  time_spent INTEGER DEFAULT 0, -- in seconds
  tests_taken INTEGER DEFAULT 0,
  streak_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, date)
);

-- Revision capsules table
CREATE TABLE public.revision_capsules (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  subject TEXT NOT NULL CHECK (subject IN ('physics', 'chemistry', 'mathematics')),
  topics JSONB NOT NULL DEFAULT '[]'::jsonb,
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ,
  focus_on_weak BOOLEAN DEFAULT true,
  include_formulas BOOLEAN DEFAULT true,
  include_common_mistakes BOOLEAN DEFAULT true
);

-- Create indexes for better query performance
CREATE INDEX idx_topic_mastery_user_id ON public.topic_mastery(user_id);
CREATE INDEX idx_topic_mastery_subject ON public.topic_mastery(subject);
CREATE INDEX idx_tests_user_id ON public.tests(user_id);
CREATE INDEX idx_tests_status ON public.tests(status);
CREATE INDEX idx_tests_scheduled_at ON public.tests(scheduled_at);
CREATE INDEX idx_test_attempts_test_id ON public.test_attempts(test_id);
CREATE INDEX idx_test_attempts_user_id ON public.test_attempts(user_id);
CREATE INDEX idx_uploaded_tests_user_id ON public.uploaded_tests(user_id);
CREATE INDEX idx_uploaded_tests_status ON public.uploaded_tests(processing_status);
CREATE INDEX idx_user_activity_user_date ON public.user_activity(user_id, date DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON public.user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_topic_mastery_updated_at BEFORE UPDATE ON public.topic_mastery
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tests_updated_at BEFORE UPDATE ON public.tests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.topic_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.test_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.uploaded_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.revision_capsules ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view their own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- RLS Policies for user_preferences
CREATE POLICY "Users can view their own preferences" ON public.user_preferences
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own preferences" ON public.user_preferences
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own preferences" ON public.user_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- RLS Policies for topic_mastery
CREATE POLICY "Users can view their own topic mastery" ON public.topic_mastery
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own topic mastery" ON public.topic_mastery
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own topic mastery" ON public.topic_mastery
    FOR UPDATE USING (auth.uid() = user_id);

-- RLS Policies for tests
CREATE POLICY "Users can view their own tests" ON public.tests
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own tests" ON public.tests
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own tests" ON public.tests
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own tests" ON public.tests
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for test_attempts
CREATE POLICY "Users can view their own test attempts" ON public.test_attempts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own test attempts" ON public.test_attempts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- RLS Policies for uploaded_tests
CREATE POLICY "Users can view their own uploaded tests" ON public.uploaded_tests
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own uploaded tests" ON public.uploaded_tests
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own uploaded tests" ON public.uploaded_tests
    FOR UPDATE USING (auth.uid() = user_id);

-- RLS Policies for user_activity
CREATE POLICY "Users can view their own activity" ON public.user_activity
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own activity" ON public.user_activity
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own activity" ON public.user_activity
    FOR UPDATE USING (auth.uid() = user_id);

-- RLS Policies for revision_capsules
CREATE POLICY "Users can view their own capsules" ON public.revision_capsules
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own capsules" ON public.revision_capsules
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own capsules" ON public.revision_capsules
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own capsules" ON public.revision_capsules
    FOR DELETE USING (auth.uid() = user_id);
