-- Migration: 008_add_question_image.sql
-- Goal: Add image_url field to repository_questions table and setup storage bucket for images

-- 1. Add image_url to repository_questions
ALTER TABLE public.repository_questions 
ADD COLUMN IF NOT EXISTS image_url TEXT;

COMMENT ON COLUMN public.repository_questions.image_url IS 'URL to question image stored in Supabase Storage (question-images bucket)';

-- 2. Create storage bucket for question images
INSERT INTO storage.buckets (id, name, public)
VALUES ('question-images', 'question-images', true)
ON CONFLICT (id) DO NOTHING;

-- 3. Set up storage policies for question-images
-- Allow public access to view images
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
TO public
USING ( bucket_id = 'question-images' );

-- Allow authenticated users (likely admins/staff) to upload images
CREATE POLICY "Authenticated users can upload question images"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK ( bucket_id = 'question-images' );

-- Allow authenticated users to update/delete (optional but good for management)
CREATE POLICY "Authenticated users can update question images"
ON storage.objects FOR UPDATE
TO authenticated
USING ( bucket_id = 'question-images' );

CREATE POLICY "Authenticated users can delete question images"
ON storage.objects FOR DELETE
TO authenticated
USING ( bucket_id = 'question-images' );
