-- Add title column for admin-entered display name in extraction jobs list
ALTER TABLE public.extraction_jobs
ADD COLUMN IF NOT EXISTS title TEXT;

COMMENT ON COLUMN public.extraction_jobs.title IS 'Admin-entered book title for display in job listing';
