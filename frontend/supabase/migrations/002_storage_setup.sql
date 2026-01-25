-- Create storage buckets for test uploads
INSERT INTO storage.buckets (id, name, public)
VALUES 
  ('test-papers', 'test-papers', false),
  ('response-sheets', 'response-sheets', false)
ON CONFLICT (id) DO NOTHING;

-- Storage policies for test-papers bucket
CREATE POLICY "Users can upload their own test papers"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'test-papers' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can view their own test papers"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'test-papers' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can update their own test papers"
ON storage.objects FOR UPDATE
TO authenticated
USING (
  bucket_id = 'test-papers' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can delete their own test papers"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'test-papers' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

-- Storage policies for response-sheets bucket
CREATE POLICY "Users can upload their own response sheets"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'response-sheets' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can view their own response sheets"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'response-sheets' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can update their own response sheets"
ON storage.objects FOR UPDATE
TO authenticated
USING (
  bucket_id = 'response-sheets' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can delete their own response sheets"
ON storage.objects FOR DELETE
TO authenticated
USING (
  bucket_id = 'response-sheets' AND
  auth.uid()::text = (storage.foldername(name))[1]
);
