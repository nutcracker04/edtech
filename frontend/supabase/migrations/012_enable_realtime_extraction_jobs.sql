-- Enable Supabase Realtime for extraction_jobs table
-- Allows frontend to subscribe to real-time progress updates during extraction

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_publication_tables
    WHERE pubname = 'supabase_realtime' AND tablename = 'extraction_jobs'
  ) THEN
    ALTER PUBLICATION supabase_realtime ADD TABLE public.extraction_jobs;
  END IF;
END $$;
