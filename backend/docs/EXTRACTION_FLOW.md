# Extraction Flow: Local vs Database

## Why Local Storage During Processing?

The extraction pipeline **must** use local disk temporarily because:

1. **Sarvam API** – Returns extracted content as a downloadable zip. There is no streaming API.
2. **Pipeline reads** – Structure analysis and question extraction read `combined.md` from disk.
3. **Chunking** – Large PDFs are split into chunks; each chunk is sent to Sarvam separately and results are merged locally.

## Where Data Lives

| Stage | Location | Purpose |
|-------|----------|---------|
| Sarvam output | Local `backend/data/extracted_images/{job_id}/` | Temp storage during processing |
| Raw questions, chapters, topics | **Supabase DB** | Persistent; used by admin UI |
| combined.md, images | **Supabase `extraction-artifacts` bucket** | Persistent; served to frontend |
| Job status | **Supabase `extraction_jobs`** | Real-time progress, stage, metadata |

## Pipeline Steps

1. **Upload** – PDF uploaded to Supabase `source-pdfs` bucket
2. **Extraction** – Chunks sent to Sarvam, markdown/images downloaded locally
3. **Structure** – `StructureAnalyzer` finds chapters, topics, questions/answer-key sections
4. **Questions** – `QuestionExtractor` parses questions, links answers/hints
5. **DB write** – `DatabaseWriter` inserts into `extraction_raw_questions`, `extraction_questions`, etc.
6. **Upload** – `combined.md` and images uploaded to `extraction-artifacts`

## Why No Questions Sometimes?

If the structure analyzer finds an **answer key** section but no **questions** section (e.g. document uses non-standard headings), the pipeline previously wrote 0 questions. A fallback was added: when an answer key exists, content *before* the answer key is treated as the questions section.

## Why "No Page Markers"?

Sarvam output may not include `<!-- Page X -->` markers. The analyzer tries multiple formats; if none match, the whole document is treated as one page. Chapter detection then relies on heading patterns; if those don’t match, a fallback "Chapter 1 (Unstructured)" is created.
