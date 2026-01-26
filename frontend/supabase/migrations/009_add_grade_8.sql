-- Migration: 009_add_grade_8.sql
-- Purpose: Add grade 8 support to the users table
-- This aligns the database schema with the frontend which now supports grade 8

-- Update the grade constraint to include grade 8
ALTER TABLE public.users 
DROP CONSTRAINT IF EXISTS users_grade_check;

ALTER TABLE public.users 
ADD CONSTRAINT users_grade_check 
CHECK (grade IN ('8', '9', '10', '11', '12'));

-- Update the trigger function to handle grade 8 as a valid default
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  -- Insert new user profile with role
  INSERT INTO public.users (id, email, name, grade, syllabus, target_exam, role)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', 'User'),
    COALESCE(NEW.raw_user_meta_data->>'grade', '10'),
    COALESCE(NEW.raw_user_meta_data->>'syllabus', 'cbse'),
    COALESCE(NEW.raw_user_meta_data->>'target_exam', 'jee-main'),
    'user'  -- Default role for all new users
  )
  ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    name = COALESCE(EXCLUDED.name, users.name),
    grade = COALESCE(EXCLUDED.grade, users.grade),
    syllabus = COALESCE(EXCLUDED.syllabus, users.syllabus),
    target_exam = COALESCE(EXCLUDED.target_exam, users.target_exam),
    role = COALESCE(users.role, 'user');  -- Preserve existing role or set default
  
  -- Also create default preferences
  INSERT INTO public.user_preferences (user_id, daily_goal, difficulty_level)
  VALUES (NEW.id, 20, 'adaptive')
  ON CONFLICT (user_id) DO NOTHING;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Verification
DO $$
BEGIN
  RAISE NOTICE '✅ Grade 8 support added successfully';
  RAISE NOTICE 'Valid grades are now: 8, 9, 10, 11, 12';
END $$;
