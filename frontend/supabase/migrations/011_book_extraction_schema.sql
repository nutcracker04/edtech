-- Migration: 011_book_extraction_schema.sql
-- Book extraction pipeline schema per implementation guide.
-- Phase 1: extraction_jobs, extraction_pages, extraction_blocks, books, extraction_chapters, extraction_topics
-- Phase 2: raw_questions, extraction_questions, extraction_options, question_images, question_tags, answers, hints, explanations

-- Phase 1: Extraction jobs (created first, book_id backfilled later)
CREATE TABLE IF NOT EXISTS public.extraction_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID,
    source_pdf_filename TEXT NOT NULL,
    source_pdf_path TEXT NOT NULL,
    stage TEXT NOT NULL DEFAULT 'queued' CHECK (stage IN ('queued', 'validation', 'extraction', 'completed', 'failed')),
    progress NUMERIC(5,2) DEFAULT 0.0 CHECK (progress >= 0 AND progress <= 100),
    total_pages INTEGER DEFAULT 0,
    pages_processed INTEGER DEFAULT 0,
    questions_extracted INTEGER DEFAULT 0,
    error TEXT,
    manifest_path TEXT,
    extracted_path TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    processing_time_seconds NUMERIC(10,2),
    sarvam_job_ids JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Phase 1: Books
CREATE TABLE IF NOT EXISTS public.extraction_books (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    subject TEXT NOT NULL,
    grade_level INTEGER NOT NULL,
    publisher TEXT,
    series TEXT,
    isbn TEXT,
    edition TEXT,
    language TEXT DEFAULT 'en',
    source_pdf_path TEXT,
    extraction_job_id UUID REFERENCES public.extraction_jobs(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(isbn)
);

-- Add extraction_jobs.book_id FK
ALTER TABLE public.extraction_jobs DROP CONSTRAINT IF EXISTS extraction_jobs_book_id_fkey;
ALTER TABLE public.extraction_jobs ADD CONSTRAINT extraction_jobs_book_id_fkey
    FOREIGN KEY (book_id) REFERENCES public.extraction_books(id) ON DELETE SET NULL;

-- Phase 1: Extraction pages
CREATE TABLE IF NOT EXISTS public.extraction_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES public.extraction_jobs(id) ON DELETE CASCADE,
    page_num INTEGER NOT NULL,
    image_width INTEGER,
    image_height INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    raw_json_path TEXT,
    block_count INTEGER DEFAULT 0,
    UNIQUE(job_id, page_num)
);

-- Phase 1: Extraction blocks
CREATE TABLE IF NOT EXISTS public.extraction_blocks (
    id TEXT PRIMARY KEY,
    page_id UUID NOT NULL REFERENCES public.extraction_pages(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES public.extraction_jobs(id) ON DELETE CASCADE,
    block_index INTEGER NOT NULL,
    layout_tag TEXT,
    confidence NUMERIC(5,4),
    reading_order INTEGER,
    text TEXT,
    x1 NUMERIC, y1 NUMERIC, x2 NUMERIC, y2 NUMERIC,
    raw_block JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Phase 1: Extraction chapters (book-specific)
CREATE TABLE IF NOT EXISTS public.extraction_chapters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID NOT NULL REFERENCES public.extraction_books(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    slug TEXT NOT NULL,
    page_start INTEGER NOT NULL,
    page_end INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(book_id, chapter_number)
);

-- Phase 1: Extraction topics (section-level)
CREATE TABLE IF NOT EXISTS public.extraction_topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chapter_id UUID NOT NULL REFERENCES public.extraction_chapters(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    slug TEXT NOT NULL,
    topic_order INTEGER NOT NULL DEFAULT 1,
    section_type TEXT NOT NULL CHECK (section_type IN ('questions', 'answer_key', 'hints', 'explanations')),
    page_start INTEGER NOT NULL,
    page_end INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(chapter_id, slug)
);

-- Phase 2: Raw questions (staging)
CREATE TABLE IF NOT EXISTS public.raw_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES public.extraction_jobs(id) ON DELETE CASCADE,
    question_number TEXT NOT NULL,
    question_text TEXT NOT NULL,
    options JSONB DEFAULT '[]'::jsonb,
    page_number INTEGER NOT NULL,
    chapter_context TEXT,
    topic_context TEXT,
    sub_topic_context TEXT,
    raw_images JSONB DEFAULT '[]'::jsonb,
    raw_tables JSONB DEFAULT '[]'::jsonb,
    processing_status TEXT NOT NULL DEFAULT 'pending' CHECK (processing_status IN ('pending', 'tagged', 'failed')),
    error_message TEXT,
    question_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Phase 2: Extraction questions (final structured questions)
CREATE TABLE IF NOT EXISTS public.extraction_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_number TEXT NOT NULL,
    question_text TEXT NOT NULL,
    topic_id UUID NOT NULL REFERENCES public.extraction_topics(id) ON DELETE CASCADE,
    chapter_id UUID NOT NULL REFERENCES public.extraction_chapters(id) ON DELETE CASCADE,
    book_id UUID NOT NULL REFERENCES public.extraction_books(id) ON DELETE CASCADE,
    sub_topic TEXT,
    answer_type TEXT NOT NULL DEFAULT 'mcq_single' CHECK (answer_type IN ('mcq_single', 'mcq_multiple', 'integer', 'numerical', 'subjective', 'true_false', 'fill_blank')),
    difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard')),
    bloom_level TEXT,
    page_number INTEGER NOT NULL,
    has_image BOOLEAN DEFAULT false,
    has_table BOOLEAN DEFAULT false,
    has_math BOOLEAN DEFAULT false,
    marks NUMERIC,
    negative_marks NUMERIC,
    raw_question_id UUID REFERENCES public.raw_questions(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Phase 2: Options (MCQ choices)
CREATE TABLE IF NOT EXISTS public.extraction_options (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES public.extraction_questions(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    text TEXT NOT NULL,
    image_id UUID,
    is_correct BOOLEAN DEFAULT false,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(question_id, label)
);

-- Phase 2: Question images
CREATE TABLE IF NOT EXISTS public.question_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES public.extraction_questions(id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL,
    alt_text TEXT,
    width_px INTEGER,
    height_px INTEGER,
    position_in_question TEXT CHECK (position_in_question IN ('question', 'option_a', 'option_b', 'option_c', 'option_d', 'explanation')),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Phase 2: Question tags
CREATE TABLE IF NOT EXISTS public.question_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES public.extraction_questions(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    source TEXT DEFAULT 'auto',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(question_id, tag)
);

-- Phase 2: Answers (linked to questions, written after answer key parse)
CREATE TABLE IF NOT EXISTS public.extraction_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES public.extraction_questions(id) ON DELETE CASCADE,
    correct_answer TEXT NOT NULL,
    correct_option_ids JSONB DEFAULT '[]'::jsonb,
    answer_source TEXT NOT NULL CHECK (answer_source IN ('answer_key_section', 'explanation_derived', 'conflict')),
    page_number INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(question_id)
);

-- Phase 2: Hints
CREATE TABLE IF NOT EXISTS public.extraction_hints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES public.extraction_questions(id) ON DELETE CASCADE,
    hint_text TEXT NOT NULL,
    page_number INTEGER,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(question_id)
);

-- Phase 2: Explanations
CREATE TABLE IF NOT EXISTS public.extraction_explanations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES public.extraction_questions(id) ON DELETE CASCADE,
    explanation_text TEXT NOT NULL,
    page_number INTEGER,
    images JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(question_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_extraction_jobs_stage ON public.extraction_jobs(stage);
CREATE INDEX IF NOT EXISTS idx_extraction_books_isbn ON public.extraction_books(isbn);
CREATE INDEX IF NOT EXISTS idx_extraction_chapters_book ON public.extraction_chapters(book_id);
CREATE INDEX IF NOT EXISTS idx_extraction_chapters_slug ON public.extraction_chapters(book_id, slug);
CREATE INDEX IF NOT EXISTS idx_extraction_topics_chapter ON public.extraction_topics(chapter_id);
CREATE INDEX IF NOT EXISTS idx_extraction_topics_slug ON public.extraction_topics(chapter_id, slug);
CREATE INDEX IF NOT EXISTS idx_raw_questions_job ON public.raw_questions(job_id);
CREATE INDEX IF NOT EXISTS idx_extraction_questions_book ON public.extraction_questions(book_id);
CREATE INDEX IF NOT EXISTS idx_extraction_questions_topic ON public.extraction_questions(topic_id);
CREATE INDEX IF NOT EXISTS idx_extraction_options_question ON public.extraction_options(question_id);

-- Fix extraction_jobs to allow creation before book exists (book_id nullable initially)
-- extraction_jobs.book_id is already nullable by default

-- RLS (allow service role full access for extraction pipeline)
ALTER TABLE public.extraction_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_books ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_chapters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.raw_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.question_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.question_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_hints ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_explanations ENABLE ROW LEVEL SECURITY;

-- Service role bypass (extraction runs as backend service)
CREATE POLICY "Service role full access extraction" ON public.extraction_jobs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access extraction_books" ON public.extraction_books FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access extraction_pages" ON public.extraction_pages FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access extraction_blocks" ON public.extraction_blocks FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access extraction_chapters" ON public.extraction_chapters FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access extraction_topics" ON public.extraction_topics FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access raw_questions" ON public.raw_questions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access extraction_questions" ON public.extraction_questions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access extraction_options" ON public.extraction_options FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access question_images" ON public.question_images FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access question_tags" ON public.question_tags FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access extraction_answers" ON public.extraction_answers FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access extraction_hints" ON public.extraction_hints FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access extraction_explanations" ON public.extraction_explanations FOR ALL USING (true) WITH CHECK (true);
