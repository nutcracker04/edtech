-- Create extraction-artifacts bucket for storing extracted markdown and images
-- All extracted content is stored in Supabase, not locally

INSERT INTO storage.buckets (id, name, public)
VALUES ('extraction-artifacts', 'extraction-artifacts', false)
ON CONFLICT (id) DO NOTHING;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname = 'storage' AND tablename = 'objects'
    AND policyname = 'Service role full access extraction-artifacts'
  ) THEN
    CREATE POLICY "Service role full access extraction-artifacts"
    ON storage.objects FOR ALL
    TO service_role
    USING (bucket_id = 'extraction-artifacts')
    WITH CHECK (bucket_id = 'extraction-artifacts');
  END IF;
END $$;
