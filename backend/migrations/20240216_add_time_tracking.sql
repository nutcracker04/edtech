-- Add detailed time tracking for test attempts
-- This enables comprehensive test journey analysis

-- Add columns to test_attempts for enhanced time tracking
ALTER TABLE test_attempts
ADD COLUMN IF NOT EXISTS question_order INTEGER,
ADD COLUMN IF NOT EXISTS first_viewed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS last_viewed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS answer_changed_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS came_from_question_id UUID,
ADD COLUMN IF NOT EXISTS went_to_question_id UUID;

-- Create a new table for question navigation tracking
CREATE TABLE IF NOT EXISTS question_navigation_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    from_question_id UUID,
    to_question_id UUID NOT NULL,
    from_question_index INTEGER,
    to_question_index INTEGER NOT NULL,
    navigation_type VARCHAR(50), -- 'next', 'previous', 'jump', 'review', 'initial'
    time_on_previous_question INTEGER, -- seconds spent on previous question
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_navigation_log_test_id ON question_navigation_log(test_id);
CREATE INDEX IF NOT EXISTS idx_navigation_log_user_id ON question_navigation_log(user_id);
CREATE INDEX IF NOT EXISTS idx_navigation_log_timestamp ON question_navigation_log(timestamp);

-- Create a table for answer change tracking
CREATE TABLE IF NOT EXISTS answer_change_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id UUID NOT NULL,
    question_index INTEGER NOT NULL,
    previous_answer TEXT,
    new_answer TEXT,
    change_type VARCHAR(50), -- 'initial', 'modified', 'cleared'
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for answer change log
CREATE INDEX IF NOT EXISTS idx_answer_change_test_id ON answer_change_log(test_id);
CREATE INDEX IF NOT EXISTS idx_answer_change_question_id ON answer_change_log(question_id);

-- Add comment for documentation
COMMENT ON TABLE question_navigation_log IS 'Tracks user navigation between questions during test taking for journey analysis';
COMMENT ON TABLE answer_change_log IS 'Tracks all answer changes to understand decision-making patterns';
