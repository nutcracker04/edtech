-- Staging fields for manual question pipeline + reject workflow (Supabase)

ALTER TABLE public.raw_questions ADD COLUMN IF NOT EXISTS correct_answer TEXT;
ALTER TABLE public.raw_questions ADD COLUMN IF NOT EXISTS answer_type TEXT;
ALTER TABLE public.raw_questions ADD COLUMN IF NOT EXISTS marks NUMERIC(5,2);
ALTER TABLE public.raw_questions ADD COLUMN IF NOT EXISTS negative_marks NUMERIC(5,2);
ALTER TABLE public.raw_questions ADD COLUMN IF NOT EXISTS bloom_level TEXT;

ALTER TABLE public.raw_questions DROP CONSTRAINT IF EXISTS raw_questions_processing_status_check;
ALTER TABLE public.raw_questions ADD CONSTRAINT raw_questions_processing_status_check
    CHECK (processing_status IN ('pending', 'tagged', 'failed', 'error', 'rejected'));
