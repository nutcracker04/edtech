-- Migration: 001_create_schema.sql
-- Description: Create all 21 tables for the IIT Foundation Platform database schema
-- Tables created in dependency order to satisfy foreign key constraints
-- Author: Database Architecture Migration
-- Date: 2024

-- ============================================================================
-- HIERARCHY TABLES (No dependencies)
-- ============================================================================

-- Table: books
-- Stores textbook information for organizing questions
CREATE TABLE IF NOT EXISTS books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    subject TEXT NOT NULL CHECK (subject IN ('Chemistry', 'Physics', 'Mathematics')),
    grade_level INTEGER NOT NULL CHECK (grade_level IN (7, 8, 9, 10)),
    publisher TEXT,
    series TEXT,
    isbn TEXT,
    edition TEXT,
    language TEXT DEFAULT 'en',
    source_pdf_path TEXT,
    extraction_job_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: chapters
-- Stores chapter information within books
CREATE TABLE IF NOT EXISTS chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    slug TEXT NOT NULL,
    page_start INTEGER,
    page_end INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_book_chapter UNIQUE (book_id, chapter_number),
    CONSTRAINT valid_page_range CHECK (page_end IS NULL OR page_start IS NULL OR page_end >= page_start)
);

-- Table: topics
-- Stores topic information within chapters
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    slug TEXT NOT NULL,
    topic_order INTEGER,
    section_type TEXT CHECK (section_type IN ('questions', 'hints', 'explanations', 'answer_key')),
    page_start INTEGER,
    page_end INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_chapter_slug UNIQUE (chapter_id, slug),
    CONSTRAINT valid_topic_page_range CHECK (page_end IS NULL OR page_start IS NULL OR page_end >= page_start)
);

-- ============================================================================
-- EXTRACTION PIPELINE TABLES
-- ============================================================================

-- Table: extraction_jobs
-- Tracks PDF extraction job status and progress
CREATE TABLE IF NOT EXISTS extraction_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID REFERENCES books(id) ON DELETE SET NULL,
    source_pdf_filename TEXT NOT NULL,
    source_pdf_path TEXT,
    stage TEXT NOT NULL DEFAULT 'queued' CHECK (stage IN ('queued', 'validation', 'upload', 'extraction', 'completed', 'failed')),
    progress NUMERIC(5,2) DEFAULT 0.0 CHECK (progress >= 0.0 AND progress <= 100.0),
    total_pages INTEGER,
    pages_processed INTEGER DEFAULT 0,
    questions_extracted INTEGER DEFAULT 0,
    success_rate NUMERIC(5,2),
    error TEXT,
    manifest_path TEXT,
    extracted_path TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    processing_time_seconds NUMERIC(10,2),
    sarvam_job_ids JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_completion_time CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at)
);

-- Table: extraction_pages
-- Stores individual page information from PDF extraction
CREATE TABLE IF NOT EXISTS extraction_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES extraction_jobs(id) ON DELETE CASCADE,
    page_num INTEGER NOT NULL,
    image_width INTEGER,
    image_height INTEGER,
    raw_json_path TEXT,
    block_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_job_page UNIQUE (job_id, page_num),
    CONSTRAINT valid_page_num CHECK (page_num > 0)
);

-- Table: extraction_blocks
-- Stores individual content blocks extracted from pages
CREATE TABLE IF NOT EXISTS extraction_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID NOT NULL REFERENCES extraction_pages(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES extraction_jobs(id) ON DELETE CASCADE,
    block_index INTEGER NOT NULL,
    layout_tag TEXT,
    confidence NUMERIC(4,3) CHECK (confidence >= 0.0 AND confidence <= 1.0),
    reading_order INTEGER,
    text TEXT,
    x1 NUMERIC(10,2),
    y1 NUMERIC(10,2),
    x2 NUMERIC(10,2),
    y2 NUMERIC(10,2),
    raw_block JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: raw_questions
-- Stores unprocessed questions extracted from PDFs before tagging
CREATE TABLE IF NOT EXISTS raw_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES extraction_jobs(id) ON DELETE CASCADE,
    question_number TEXT NOT NULL,
    question_text TEXT NOT NULL,
    options JSONB,
    page_number INTEGER,
    chapter_context TEXT,
    topic_context TEXT,
    sub_topic_context TEXT,
    raw_images JSONB,
    raw_tables JSONB,
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'tagged', 'error')),
    error_message TEXT,
    question_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- QUESTION BANK TABLES
-- ============================================================================

-- Table: questions
-- Stores processed questions with metadata
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_number TEXT NOT NULL,
    question_text TEXT NOT NULL,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE RESTRICT,
    chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE RESTRICT,
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
    sub_topic TEXT,
    answer_type TEXT NOT NULL CHECK (answer_type IN ('mcq_single', 'mcq_multiple', 'integer', 'numerical', 'subjective', 'true_false', 'fill_blank', 'match')),
    difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard')),
    page_number INTEGER,
    has_image BOOLEAN DEFAULT FALSE,
    has_table BOOLEAN DEFAULT FALSE,
    has_math BOOLEAN DEFAULT FALSE,
    marks NUMERIC(5,2),
    negative_marks NUMERIC(5,2),
    bloom_level TEXT,
    raw_question_id UUID REFERENCES raw_questions(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_topic_question_number UNIQUE (topic_id, question_number)
);

-- Add foreign key from raw_questions to questions (circular reference handled after table creation)
ALTER TABLE raw_questions ADD CONSTRAINT fk_raw_questions_question 
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE SET NULL;

-- Table: options
-- Stores answer options for MCQ questions
CREATE TABLE IF NOT EXISTS options (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    text TEXT NOT NULL,
    image_id UUID,
    is_correct BOOLEAN,
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_question_label UNIQUE (question_id, label),
    CONSTRAINT valid_label CHECK (label ~ '^[A-Z]$')
);

-- Table: answers
-- Stores correct answers for questions
CREATE TABLE IF NOT EXISTS answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL UNIQUE REFERENCES questions(id) ON DELETE CASCADE,
    correct_answer TEXT NOT NULL,
    correct_option_ids UUID[],
    answer_source TEXT DEFAULT 'answer_key_section',
    page_number INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: question_images
-- Stores images associated with questions
CREATE TABLE IF NOT EXISTS question_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL,
    alt_text TEXT,
    width_px INTEGER,
    height_px INTEGER,
    position_in_question TEXT CHECK (position_in_question IN ('question', 'option_a', 'option_b', 'option_c', 'option_d', 'option_e', 'explanation', 'hint')),
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: question_tables
-- Stores tables associated with questions
CREATE TABLE IF NOT EXISTS question_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    headers TEXT[],
    rows JSONB NOT NULL,
    caption TEXT,
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: question_tags
-- Stores tags for categorizing questions
CREATE TABLE IF NOT EXISTS question_tags (
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    source TEXT DEFAULT 'auto' CHECK (source IN ('auto', 'manual')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (question_id, tag)
);

-- Table: hints
-- Stores hints for questions
CREATE TABLE IF NOT EXISTS hints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    hint_text TEXT NOT NULL,
    hint_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: explanations
-- Stores detailed explanations for questions
CREATE TABLE IF NOT EXISTS explanations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    explanation_text TEXT NOT NULL,
    explanation_type TEXT CHECK (explanation_type IN ('solution', 'concept', 'common_mistake')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- TEST ENGINE TABLES
-- ============================================================================

-- Table: test_papers
-- Stores test paper configurations
CREATE TABLE IF NOT EXISTS test_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    book_id UUID REFERENCES books(id) ON DELETE SET NULL,
    chapter_id UUID REFERENCES chapters(id) ON DELETE SET NULL,
    subject TEXT,
    grade_level INTEGER CHECK (grade_level IN (7, 8, 9, 10)),
    total_marks NUMERIC(6,2) NOT NULL CHECK (total_marks > 0),
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    is_published BOOLEAN DEFAULT FALSE,
    created_by UUID NOT NULL,
    paper_type TEXT DEFAULT 'chapter_test' CHECK (paper_type IN ('chapter_test', 'full_syllabus', 'topic_test', 'custom')),
    negative_marking_scheme JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: test_paper_questions
-- Links questions to test papers with marks configuration
CREATE TABLE IF NOT EXISTS test_paper_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_paper_id UUID NOT NULL REFERENCES test_papers(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    sort_order INTEGER NOT NULL,
    marks NUMERIC(5,2) NOT NULL,
    negative_marks NUMERIC(5,2) DEFAULT 0,
    section_label TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_paper_question UNIQUE (test_paper_id, question_id)
);

-- Table: test_sessions
-- Stores student test session information
CREATE TABLE IF NOT EXISTS test_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_paper_id UUID NOT NULL REFERENCES test_papers(id) ON DELETE RESTRICT,
    student_id UUID NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    time_taken_seconds INTEGER,
    status TEXT DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'submitted', 'timed_out', 'abandoned')),
    total_marks_obtained NUMERIC(6,2),
    percentage NUMERIC(5,2),
    rank INTEGER,
    is_practice BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_submission_time CHECK (submitted_at IS NULL OR submitted_at >= started_at)
);

-- Table: attempts
-- Stores individual question attempts within test sessions
CREATE TABLE IF NOT EXISTS attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES test_sessions(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    test_paper_question_id UUID NOT NULL REFERENCES test_paper_questions(id) ON DELETE RESTRICT,
    student_answer TEXT,
    selected_option_ids UUID[],
    is_correct BOOLEAN,
    is_attempted BOOLEAN DEFAULT FALSE,
    marks_awarded NUMERIC(5,2),
    time_spent_seconds INTEGER,
    hint_used BOOLEAN DEFAULT FALSE,
    explanation_viewed BOOLEAN DEFAULT FALSE,
    flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_session_question UNIQUE (session_id, question_id)
);

-- ============================================================================
-- ANALYTICS TABLES
-- ============================================================================

-- Table: question_stats
-- Stores aggregated statistics for questions
CREATE TABLE IF NOT EXISTS question_stats (
    question_id UUID PRIMARY KEY REFERENCES questions(id) ON DELETE CASCADE,
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    accuracy_pct NUMERIC(5,2) DEFAULT 0 CHECK (accuracy_pct >= 0 AND accuracy_pct <= 100),
    avg_time_seconds NUMERIC(8,2) DEFAULT 0,
    skip_count INTEGER DEFAULT 0,
    hint_use_count INTEGER DEFAULT 0,
    explanation_view_count INTEGER DEFAULT 0,
    most_common_wrong_answer TEXT,
    discrimination_index NUMERIC(4,3) CHECK (discrimination_index IS NULL OR (discrimination_index >= -1.0 AND discrimination_index <= 1.0)),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: student_topic_mastery
-- Tracks student mastery level for each topic
CREATE TABLE IF NOT EXISTS student_topic_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    chapter_id UUID NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    accuracy_pct NUMERIC(5,2) DEFAULT 0 CHECK (accuracy_pct >= 0 AND accuracy_pct <= 100),
    mastery_level TEXT DEFAULT 'not_started' CHECK (mastery_level IN ('not_started', 'learning', 'developing', 'proficient', 'mastered')),
    last_attempted_at TIMESTAMPTZ,
    streak_days INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_student_topic UNIQUE (student_id, topic_id)
);

-- Table: daily_activity
-- Tracks daily student activity for streak calculation
CREATE TABLE IF NOT EXISTS daily_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    activity_date DATE NOT NULL,
    sessions_count INTEGER DEFAULT 0,
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_student_date UNIQUE (student_id, activity_date)
);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables with updated_at column
CREATE TRIGGER update_books_updated_at BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_questions_updated_at BEFORE UPDATE ON questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_test_papers_updated_at BEFORE UPDATE ON test_papers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_question_stats_updated_at BEFORE UPDATE ON question_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_student_topic_mastery_updated_at BEFORE UPDATE ON student_topic_mastery
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE books IS 'Stores textbook information for organizing questions by subject and grade';
COMMENT ON TABLE chapters IS 'Stores chapter information within books';
COMMENT ON TABLE topics IS 'Stores topic information within chapters';
COMMENT ON TABLE extraction_jobs IS 'Tracks PDF extraction job status and progress';
COMMENT ON TABLE extraction_pages IS 'Stores individual page information from PDF extraction';
COMMENT ON TABLE extraction_blocks IS 'Stores individual content blocks extracted from pages';
COMMENT ON TABLE raw_questions IS 'Stores unprocessed questions extracted from PDFs before metadata tagging';
COMMENT ON TABLE questions IS 'Stores processed questions with complete metadata';
COMMENT ON TABLE options IS 'Stores answer options for MCQ questions';
COMMENT ON TABLE answers IS 'Stores correct answers for questions';
COMMENT ON TABLE question_images IS 'Stores images associated with questions';
COMMENT ON TABLE question_tables IS 'Stores tables associated with questions';
COMMENT ON TABLE question_tags IS 'Stores tags for categorizing and filtering questions';
COMMENT ON TABLE hints IS 'Stores hints for questions';
COMMENT ON TABLE explanations IS 'Stores detailed explanations for questions';
COMMENT ON TABLE test_papers IS 'Stores test paper configurations';
COMMENT ON TABLE test_paper_questions IS 'Links questions to test papers with marks configuration';
COMMENT ON TABLE test_sessions IS 'Stores student test session information';
COMMENT ON TABLE attempts IS 'Stores individual question attempts within test sessions';
COMMENT ON TABLE question_stats IS 'Stores aggregated statistics for question performance';
COMMENT ON TABLE student_topic_mastery IS 'Tracks student mastery level for each topic';
COMMENT ON TABLE daily_activity IS 'Tracks daily student activity for streak calculation';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
