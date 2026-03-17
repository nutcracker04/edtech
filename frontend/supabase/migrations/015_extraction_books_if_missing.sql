-- Ensure extraction_books, extraction_chapters, extraction_topics exist
-- Fixes PGRST205 when migration 011 was not applied (e.g. backend-only schema)

-- Phase 1: Extraction books (depends on extraction_jobs which exists from 001/011)
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

-- extraction_jobs.book_id FK to extraction_books
ALTER TABLE public.extraction_jobs DROP CONSTRAINT IF EXISTS extraction_jobs_book_id_fkey;
ALTER TABLE public.extraction_jobs ADD CONSTRAINT extraction_jobs_book_id_fkey
    FOREIGN KEY (book_id) REFERENCES public.extraction_books(id) ON DELETE SET NULL;

-- Phase 1: Extraction chapters
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

-- Phase 1: Extraction topics
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

-- RLS and policies
ALTER TABLE public.extraction_books ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_chapters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.extraction_topics ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role full access extraction_books" ON public.extraction_books;
CREATE POLICY "Service role full access extraction_books" ON public.extraction_books FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role full access extraction_chapters" ON public.extraction_chapters;
CREATE POLICY "Service role full access extraction_chapters" ON public.extraction_chapters FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role full access extraction_topics" ON public.extraction_topics;
CREATE POLICY "Service role full access extraction_topics" ON public.extraction_topics FOR ALL USING (true) WITH CHECK (true);
