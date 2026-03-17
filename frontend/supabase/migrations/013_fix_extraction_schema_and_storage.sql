-- Fix extraction_jobs schema and storage buckets for database-backed extraction flow
-- Resolves: PGRST204 (updated_at column not found), Bucket not found for source-pdfs

-- Add updated_at to extraction_jobs if missing (backend schema 001 doesn't have it)
ALTER TABLE public.extraction_jobs
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Create source-pdfs bucket for PDF uploads (used by StorageManager)
INSERT INTO storage.buckets (id, name, public)
VALUES ('source-pdfs', 'source-pdfs', false)
ON CONFLICT (id) DO NOTHING;

-- Create question-images bucket (used by StorageManager for extracted images)
INSERT INTO storage.buckets (id, name, public)
VALUES ('question-images', 'question-images', false)
ON CONFLICT (id) DO NOTHING;

-- Allow service role full access to source-pdfs (extraction runs as backend)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'storage' AND tablename = 'objects'
    AND policyname = 'Service role full access source-pdfs'
  ) THEN
    CREATE POLICY "Service role full access source-pdfs"
    ON storage.objects FOR ALL
    TO service_role
    USING (bucket_id = 'source-pdfs')
    WITH CHECK (bucket_id = 'source-pdfs');
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'storage' AND tablename = 'objects'
    AND policyname = 'Service role full access question-images'
  ) THEN
    CREATE POLICY "Service role full access question-images"
    ON storage.objects FOR ALL
    TO service_role
    USING (bucket_id = 'question-images')
    WITH CHECK (bucket_id = 'question-images');
  END IF;
END $$;
