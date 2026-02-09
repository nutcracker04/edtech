-- Add chapter_ids and topic_ids columns to pyq_questions table
ALTER TABLE pyq_questions 
ADD COLUMN IF NOT EXISTS chapter_ids UUID[],
ADD COLUMN IF NOT EXISTS topic_ids UUID[];

-- Migrate existing chapter_id data to chapter_ids
UPDATE pyq_questions 
SET chapter_ids = ARRAY[chapter_id] 
WHERE chapter_id IS NOT NULL AND chapter_ids IS NULL;

-- Migrate existing topic_id data to topic_ids
UPDATE pyq_questions 
SET topic_ids = ARRAY[topic_id] 
WHERE topic_id IS NOT NULL AND topic_ids IS NULL;

-- Add comments
COMMENT ON COLUMN pyq_questions.chapter_ids IS 'Array of chapter UUIDs (supports multiple concepts)';
COMMENT ON COLUMN pyq_questions.topic_ids IS 'Array of topic UUIDs';

-- Indexing for array (GIN)
CREATE INDEX IF NOT EXISTS idx_pyq_questions_chapter_ids ON pyq_questions USING GIN (chapter_ids);
CREATE INDEX IF NOT EXISTS idx_pyq_questions_topic_ids ON pyq_questions USING GIN (topic_ids);
