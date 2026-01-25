-- Migration: 007_make_difficulty_nullable.sql
-- Purpose: Make difficulty_level nullable since it's set during tagging, not creation

-- Make difficulty_level nullable (it's set during tagging, not creation)
ALTER TABLE public.repository_questions 
ALTER COLUMN difficulty_level DROP NOT NULL;

-- Add comment
COMMENT ON COLUMN public.repository_questions.difficulty_level IS 
'Difficulty level set during tagging (easy/medium/hard). NULL for untagged questions.';
