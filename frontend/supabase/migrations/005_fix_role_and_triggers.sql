-- Migration: 005_fix_role_and_triggers.sql
-- Purpose: Fix role column and update triggers to prevent future user issues
-- Run this ONCE in Supabase SQL Editor to fix all issues

-- ============================================
-- PART 1: Add role column (if not exists)
-- ============================================

ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin'));

-- ============================================
-- PART 2: Update existing users to have role
-- ============================================

-- Set default role for any existing users without it
UPDATE public.users 
SET role = 'user' 
WHERE role IS NULL;

-- ============================================
-- PART 3: Fix the auth trigger to include role
-- ============================================

-- Drop and recreate the function to include role
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

-- Recreate the trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- PART 4: Ensure RLS policies allow profile access
-- ============================================

-- Policy for users to read their own profile
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
CREATE POLICY "Users can view own profile" ON public.users
  FOR SELECT USING (auth.uid() = id);

-- Policy for users to update their own profile
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;
CREATE POLICY "Users can update own profile" ON public.users
  FOR UPDATE USING (auth.uid() = id);

-- Policy for users to insert their own profile (for upserts during onboarding)
DROP POLICY IF EXISTS "Users can insert own profile" ON public.users;
CREATE POLICY "Users can insert own profile" ON public.users
  FOR INSERT WITH CHECK (auth.uid() = id);

-- ============================================
-- PART 5: Fix orphaned auth users (if any)
-- ============================================

-- This will create profiles for any auth users that don't have a profile
INSERT INTO public.users (id, email, name, grade, syllabus, target_exam, role)
SELECT 
  au.id,
  au.email,
  COALESCE(au.raw_user_meta_data->>'name', 'User'),
  COALESCE(au.raw_user_meta_data->>'grade', '10'),
  COALESCE(au.raw_user_meta_data->>'syllabus', 'cbse'),
  COALESCE(au.raw_user_meta_data->>'target_exam', 'jee-main'),
  'user'
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE pu.id IS NULL
ON CONFLICT (id) DO NOTHING;

-- Create preferences for users who don't have them
INSERT INTO public.user_preferences (user_id, daily_goal, difficulty_level)
SELECT 
  u.id,
  20,
  'adaptive'
FROM public.users u
LEFT JOIN public.user_preferences up ON u.id = up.user_id
WHERE up.user_id IS NULL
ON CONFLICT (user_id) DO NOTHING;

-- ============================================
-- PART 6: Verification Queries
-- ============================================

-- Check if role column exists
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'users' AND column_name = 'role'
  ) THEN
    RAISE NOTICE '✅ Role column exists';
  ELSE
    RAISE NOTICE '❌ Role column missing';
  END IF;
END $$;

-- Count users with and without profiles
DO $$
DECLARE
  auth_count INTEGER;
  profile_count INTEGER;
  orphaned_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO auth_count FROM auth.users;
  SELECT COUNT(*) INTO profile_count FROM public.users;
  orphaned_count := auth_count - profile_count;
  
  RAISE NOTICE '📊 Auth users: %, Profile users: %, Orphaned: %', 
    auth_count, profile_count, orphaned_count;
    
  IF orphaned_count = 0 THEN
    RAISE NOTICE '✅ All auth users have profiles';
  ELSE
    RAISE NOTICE '⚠️  % auth users missing profiles', orphaned_count;
  END IF;
END $$;

-- Show summary of users
SELECT 
  COUNT(*) as total_users,
  COUNT(*) FILTER (WHERE role = 'admin') as admin_users,
  COUNT(*) FILTER (WHERE role = 'user') as regular_users,
  COUNT(*) FILTER (WHERE role IS NULL) as users_without_role
FROM public.users;

-- ============================================
-- MIGRATION COMPLETE
-- ============================================

-- After running this migration:
-- 1. All existing users will have role = 'user'
-- 2. New signups will automatically get role = 'user'
-- 3. Orphaned auth users will get profiles created
-- 4. Onboarding flow will work correctly
-- 5. No more "role does not exist" errors
