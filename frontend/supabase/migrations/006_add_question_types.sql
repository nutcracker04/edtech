-- Migration: 006_add_question_types.sql
-- Purpose: Add support for different question types (single_choice, multi_choice, integer, assertion_reasoning)

-- Add question_type column
ALTER TABLE public.repository_questions 
ADD COLUMN IF NOT EXISTS question_type TEXT DEFAULT 'single_choice' 
CHECK (question_type IN ('single_choice', 'multi_choice', 'integer', 'assertion_reasoning'));

-- Add assertion and reasoning columns for assertion_reasoning type
ALTER TABLE public.repository_questions 
ADD COLUMN IF NOT EXISTS assertion TEXT;

ALTER TABLE public.repository_questions 
ADD COLUMN IF NOT EXISTS reasoning TEXT;

-- Update existing questions to have question_type
UPDATE public.repository_questions 
SET question_type = 'single_choice' 
WHERE question_type IS NULL;

-- Add comment for documentation
COMMENT ON COLUMN public.repository_questions.question_type IS 
'Type of question: single_choice (one correct), multi_choice (multiple correct), integer (0-9), assertion_reasoning (A&R format)';

COMMENT ON COLUMN public.repository_questions.assertion IS 
'Assertion statement for assertion_reasoning type questions';

COMMENT ON COLUMN public.repository_questions.reasoning IS 
'Reasoning statement for assertion_reasoning type questions';

COMMENT ON COLUMN public.repository_questions.correct_answer IS 
'Correct answer: single letter for single_choice/assertion_reasoning, comma-separated for multi_choice, number for integer';
