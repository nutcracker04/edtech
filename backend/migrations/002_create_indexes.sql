-- Migration: 002_create_indexes.sql
-- Description: Create database indexes for query performance optimization
-- Indexes support: question lookup, test sessions, analytics, and full-text search
-- Author: Database Architecture Migration
-- Date: 2024

-- ============================================================================
-- QUESTION LOOKUP INDEXES
-- ============================================================================

-- Index: idx_questions_hierarchy
-- Purpose: Supports test paper generation queries filtering by book/chapter/topic
-- Expected query time: <50ms for 20-question selection from 10,000+ questions
CREATE INDEX IF NOT EXISTS idx_questions_hierarchy 
    ON questions (book_id, chapter_id, topic_id);

-- Index: idx_questions_metadata
-- Purpose: Supports filtering questions by answer type and difficulty
-- Used in test paper generation with difficulty distribution
CREATE INDEX IF NOT EXISTS idx_questions_metadata 
    ON questions (answer_type, difficulty);

-- Index: idx_questions_features
-- Purpose: Supports filtering questions by content features (images, math, tables)
-- Enables queries like "find questions with images" or "math-heavy questions"
CREATE INDEX IF NOT EXISTS idx_questions_features 
    ON questions (has_image, has_math, has_table);

-- ============================================================================
-- TEST SESSION INDEXES
-- ============================================================================

-- Index: idx_sessions_student
-- Purpose: Supports dashboard queries for student's recent tests and active sessions
-- Expected query time: <100ms for session history with 50+ tests
CREATE INDEX IF NOT EXISTS idx_sessions_student 
    ON test_sessions (student_id, status);

-- Index: idx_sessions_paper
-- Purpose: Enables fast rank calculation within test paper
-- Supports queries to find all sessions for a specific test paper
CREATE INDEX IF NOT EXISTS idx_sessions_paper 
    ON test_sessions (test_paper_id, status);

-- Index: idx_sessions_active (Partial Index)
-- Purpose: Smaller index for frequently queried subset of active sessions
-- Faster lookups for in-progress sessions
CREATE INDEX IF NOT EXISTS idx_sessions_active 
    ON test_sessions (student_id) 
    WHERE status = 'in_progress';

-- Index: idx_attempts_session
-- Purpose: Fast retrieval of all attempts for a session
-- Critical for score calculation and session submission
CREATE INDEX IF NOT EXISTS idx_attempts_session 
    ON attempts (session_id, question_id);

-- ============================================================================
-- ANALYTICS INDEXES
-- ============================================================================

-- Index: idx_mastery_student
-- Purpose: Supports personalized recommendation queries
-- Enables fast lookup of student's mastery levels across topics
CREATE INDEX IF NOT EXISTS idx_mastery_student 
    ON student_topic_mastery (student_id, mastery_level);

-- Index: idx_daily_activity_student
-- Purpose: Enables fast streak calculation and activity history
-- Ordered by date descending for recent activity queries
CREATE INDEX IF NOT EXISTS idx_daily_activity_student 
    ON daily_activity (student_id, activity_date DESC);

-- Index: idx_question_tags
-- Purpose: Supports filtering questions by tags (e.g., 'mcq', 'calculation', 'has-image')
-- Used in test paper generation with tag-based selection
CREATE INDEX IF NOT EXISTS idx_question_tags 
    ON question_tags (tag);

-- ============================================================================
-- FULL-TEXT SEARCH INDEX
-- ============================================================================

-- Add tsvector column for full-text search on question text
-- This column will store the searchable text vector
ALTER TABLE questions 
    ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Index: idx_questions_fts
-- Purpose: Enables fast question search by text content
-- Supports LaTeX-aware search (strips math delimiters)
-- Expected query time: <500ms for full-text search across 50,000+ questions
CREATE INDEX IF NOT EXISTS idx_questions_fts 
    ON questions USING GIN(search_vector);

-- ============================================================================
-- FULL-TEXT SEARCH TRIGGER
-- ============================================================================

-- Function to update search_vector column
-- Strips LaTeX delimiters and creates searchable text vector
CREATE OR REPLACE FUNCTION update_question_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    -- Strip LaTeX delimiters (dollar signs and square brackets) and update search vector
    NEW.search_vector := to_tsvector('english', 
        regexp_replace(
            regexp_replace(NEW.question_text, '\$\$?|\\\[|\\\]', ' ', 'g'),
            '\s+', ' ', 'g'
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update search_vector on INSERT or UPDATE
CREATE TRIGGER questions_search_update 
    BEFORE INSERT OR UPDATE OF question_text
    ON questions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_question_search_vector();

-- ============================================================================
-- ADDITIONAL PERFORMANCE INDEXES
-- ============================================================================

-- Index: idx_extraction_jobs_stage
-- Purpose: Fast lookup of extraction jobs by stage for monitoring
CREATE INDEX IF NOT EXISTS idx_extraction_jobs_stage 
    ON extraction_jobs (stage, created_at DESC);

-- Index: idx_raw_questions_status
-- Purpose: Fast lookup of raw questions by processing status
-- Used to find pending questions for tagging
CREATE INDEX IF NOT EXISTS idx_raw_questions_status 
    ON raw_questions (job_id, processing_status);

-- Index: idx_test_paper_questions_paper
-- Purpose: Fast retrieval of all questions in a test paper
CREATE INDEX IF NOT EXISTS idx_test_paper_questions_paper 
    ON test_paper_questions (test_paper_id, sort_order);

-- ============================================================================
-- POPULATE EXISTING SEARCH VECTORS
-- ============================================================================

-- Update search_vector for all existing questions
-- This is a one-time operation to populate the search vector column
UPDATE questions 
SET search_vector = to_tsvector('english', 
    regexp_replace(
        regexp_replace(question_text, '\$\$?|\\\[|\\\]', ' ', 'g'),
        '\s+', ' ', 'g'
    )
)
WHERE search_vector IS NULL;

-- ============================================================================
-- INDEX STATISTICS AND COMMENTS
-- ============================================================================

COMMENT ON INDEX idx_questions_hierarchy IS 'Supports test paper generation by hierarchy (book/chapter/topic)';
COMMENT ON INDEX idx_questions_metadata IS 'Supports filtering by answer type and difficulty';
COMMENT ON INDEX idx_questions_features IS 'Supports filtering by content features (images, math, tables)';
COMMENT ON INDEX idx_sessions_student IS 'Supports student dashboard queries for test history';
COMMENT ON INDEX idx_sessions_paper IS 'Supports rank calculation within test paper';
COMMENT ON INDEX idx_sessions_active IS 'Partial index for active sessions only';
COMMENT ON INDEX idx_attempts_session IS 'Supports fast attempt retrieval for sessions';
COMMENT ON INDEX idx_mastery_student IS 'Supports personalized recommendations by mastery level';
COMMENT ON INDEX idx_daily_activity_student IS 'Supports streak calculation and activity history';
COMMENT ON INDEX idx_question_tags IS 'Supports tag-based question filtering';
COMMENT ON INDEX idx_questions_fts IS 'Full-text search index for question content';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
