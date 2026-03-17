# Extraction Flow: Local vs Database

## Schema Design (per 011_book_extraction_schema.sql)

**Phase 1:** extraction_jobs → extraction_pages → extraction_blocks → extraction_books → extraction_chapters → extraction_topics  
**Phase 2:** raw_questions → extraction_questions → extraction_options → question_images → extraction_answers → hints → explanations

## Flow (as Implemented)

1. **Upload** – PDF uploaded to Supabase `source-pdfs` bucket
2. **Extraction** – Chunks sent to Sarvam; zip downloaded and extracted locally
3. **Pages & blocks** – `_write_extraction_pages_from_metadata` writes `extraction_pages` and `extraction_blocks` from Sarvam metadata (`chunk_XXX/metadata/page_*.json`)
4. **Combined markdown** – `_build_combined_markdown` builds `combined.md` with `<!-- Page X -->` markers at chunk boundaries
5. **Structure** – `StructureAnalyzer` splits by page markers, finds chapters, topics, questions/answer-key sections
6. **Questions** – `QuestionExtractor` parses questions, links answers/hints
7. **DB write** – `DatabaseWriter` inserts books, chapters, topics, raw_questions, extraction_questions, etc.
8. **Upload** – `combined.md` and images uploaded to `extraction-artifacts`

## Where Data Lives

| Stage | Location | Purpose |
|-------|----------|---------|
| Sarvam output | Local `backend/data/extracted_images/{job_id}/` | Temp storage during processing |
| extraction_pages, extraction_blocks | **Supabase DB** | Per-page and block-level layout (schema design) |
| Raw questions, chapters, topics | **Supabase DB** | Persistent; used by admin UI |
| combined.md, images | **Supabase `extraction-artifacts` bucket** | Persistent; served to frontend |
| Job status | **Supabase `extraction_jobs`** | Real-time progress, stage, metadata |

## Why Local Storage During Processing?

1. **Sarvam API** – Returns extracted content as a downloadable zip. There is no streaming API.
2. **Pipeline reads** – Structure analysis and question extraction read `combined.md` from disk.
3. **Chunking** – Large PDFs are split into chunks; each chunk is sent to Sarvam separately and results are merged locally.

## Why No Questions Sometimes?

If the structure analyzer finds an **answer key** section but no **questions** section (e.g. document uses non-standard headings), the pipeline previously wrote 0 questions. A fallback was added: when an answer key exists, content *before* the answer key is treated as the questions section.

## Why "No Page Markers"?

Sarvam output may not include `<!-- Page X -->` markers. The analyzer tries multiple formats; if none match, the whole document is treated as one page. Chapter detection then relies on heading patterns; if those don’t match, a fallback "Chapter 1 (Unstructured)" is created.
