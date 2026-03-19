-- Staging fields for manual question pipeline + reject workflow
-- Safe to run multiple times (IF NOT EXISTS).

ALTER TABLE raw_questions ADD COLUMN IF NOT EXISTS correct_answer TEXT;
ALTER TABLE raw_questions ADD COLUMN IF NOT EXISTS answer_type TEXT;
ALTER TABLE raw_questions ADD COLUMN IF NOT EXISTS marks NUMERIC(5,2);
ALTER TABLE raw_questions ADD COLUMN IF NOT EXISTS negative_marks NUMERIC(5,2);
ALTER TABLE raw_questions ADD COLUMN IF NOT EXISTS bloom_level TEXT;

-- Widen processing_status (Postgres: drop and recreate check name if present)
ALTER TABLE raw_questions DROP CONSTRAINT IF EXISTS raw_questions_processing_status_check;
ALTER TABLE raw_questions ADD CONSTRAINT raw_questions_processing_status_check
    CHECK (processing_status IN ('pending', 'tagged', 'error', 'failed', 'rejected'));

COMMENT ON COLUMN raw_questions.correct_answer IS 'Correct option label(s), e.g. A or A,C, or numeric text for integer items';
COMMENT ON COLUMN raw_questions.answer_type IS 'Staging hint: mcq_single, mcq_multiple, integer, numerical, subjective, true_false, fill_blank, match';
