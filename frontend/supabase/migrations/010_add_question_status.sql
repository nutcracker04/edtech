-- Add status column to repository_questions table
ALTER TABLE repository_questions 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT NULL;

-- Add a check constraint for valid status values (only in_review or null)
ALTER TABLE repository_questions 
ADD CONSTRAINT valid_status CHECK (status IS NULL OR status = 'in_review');

-- Create an index on status for faster filtering
CREATE INDEX IF NOT EXISTS idx_repository_questions_status ON repository_questions(status);

-- Add comment to explain the column
COMMENT ON COLUMN repository_questions.status IS 'Status of the question: in_review (fully tagged, pending approval to move to tagged repository), or NULL (not fully tagged, needs tagging work)';

