"""
Extraction helpers for the book extraction pipeline.

Provides utility functions for ISBN extraction, slug generation, answer key parsing,
and image extraction/saving as specified in the implementation guide.
"""

import base64
import re
import uuid
from pathlib import Path
from typing import Any


def normalize_question_number(raw_number: str) -> str:
    """Normalize question number for matching (e.g. 'Q1' -> '1', '2.a' -> '2a')."""
    if not raw_number:
        return raw_number
    normalized = re.sub(r"^Question\s*", "", raw_number, flags=re.IGNORECASE)
    normalized = re.sub(r"^Q\s*", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\.([a-z])", r"\1", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"[.):]+$", "", normalized)
    normalized = re.sub(r"[^\da-z]", "", normalized, flags=re.IGNORECASE)
    return normalized.strip()


def to_slug(text: str) -> str:
    """
    Convert text to a stable slug for lookup keys.

    Used consistently for both chapters and topics throughout the pipeline.

    Examples:
        "Solutions and Colloids" -> "solutions_and_colloids"
        "Assessment Test 1" -> "assessment_test_1"
        "Hints and Explanations" -> "hints_and_explanations"
    """
    if not text or not text.strip():
        return ""
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def extract_isbn_from_blocks(pages: list[dict[str, Any]]) -> str | None:
    """
    Extract ISBN from page blocks (e.g. barcode image block).

    The ISBN is typically in page_NNN.json, inside the barcode image block
    whose text field contains "ISBN 978-93-528-6771-4".

    Args:
        pages: List of page dicts with "blocks" key, each block having
               layout_tag and text fields.

    Returns:
        ISBN string if found, None otherwise.
    """
    for page in pages:
        for block in page.get("blocks", []):
            if block.get("layout_tag") == "image":
                text = block.get("text", "")
                match = re.search(r"ISBN\s*([\d\-]{10,17})", text, re.IGNORECASE)
                if match:
                    return match.group(1)
    return None


def parse_answer_key(text: str) -> dict[str, str]:
    """
    Parse answer key section text into {question_number: answer_letter} map.

    Handles formats: 1. (b) | 1. b | 1) b | 1 b

    Args:
        text: Raw answer key section content.

    Returns:
        Dict mapping question number (str) to answer letter (lowercase a-d).
    """
    pattern = re.compile(
        r"(\d+[a-z]?)[.)\s]+\(?([a-dA-D])\)?",
        re.IGNORECASE,
    )
    return {m.group(1): m.group(2).lower() for m in pattern.finditer(text)}


def validate_answer(
    key_answer: str, explanation_text: str | None
) -> tuple[str, str]:
    """
    Cross-validate answer from answer key with explanation text.

    The document gives the answer from two independent places. Compare them.

    Returns:
        Tuple of (answer_to_use, answer_source).
        answer_source: "answer_key_section" | "explanation_derived" | "conflict"
    """
    if not explanation_text:
        return key_answer, "answer_key_section"

    match = re.search(
        r"correct option is \(?([a-dA-D])\)?",
        explanation_text,
        re.IGNORECASE,
    )
    expl_answer = match.group(1).lower() if match else None

    if expl_answer is None:
        return key_answer, "answer_key_section"
    if expl_answer == key_answer.lower():
        return key_answer, "answer_key_section"
    return key_answer, "conflict"


# Base64 image pattern for markdown: ![Image](data:image/xxx;base64,...)
BASE64_RE = re.compile(
    r"!\[Image\]\(data:image/(\w+);base64,([^)]+)\)",
    re.IGNORECASE,
)


def extract_and_save_images(
    question_text: str,
    question_id: str,
    book_id: str,
    storage_root: Path,
    storage_manager=None,
) -> list[dict[str, Any]]:
    """
    Extract base64 images from question text, save to storage, return records.

    When storage_manager is provided, uploads to Supabase instead of local disk.
    Records include storage_path, sort_order, position_in_question.

    Args:
        question_text: Markdown with possible ![Image](data:image/...;base64,...)
        question_id: UUID of the question (for path)
        book_id: UUID of the book (for path)
        storage_root: Root path for local storage (used when storage_manager is None)
        storage_manager: Optional StorageManager - when provided, upload to Supabase

    Returns:
        List of dicts for question_images table inserts.
    """
    records: list[dict[str, Any]] = []
    for i, match in enumerate(BASE64_RE.finditer(question_text)):
        fmt, data = match.group(1), match.group(2)
        ext = "jpg" if fmt.lower() in ("jpeg", "jpg") else fmt.lower()
        filename = f"img_{i:03d}.{ext}"
        image_data = base64.b64decode(data)
        rel_path = f"books/{book_id}/questions/{question_id}/{filename}"

        if storage_manager:
            try:
                from uuid import UUID
                storage_path = storage_manager.upload_question_image(
                    book_id=UUID(book_id),
                    question_id=UUID(question_id),
                    image_data=image_data,
                    image_filename=filename,
                )
                if storage_path.startswith("local://"):
                    rel_path = storage_path.replace("local://", "")
                else:
                    rel_path = storage_path
            except Exception:
                full_path = storage_root / rel_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_bytes(image_data)
        else:
            full_path = storage_root / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_bytes(image_data)

        records.append(
            {
                "id": str(uuid.uuid4()),
                "storage_path": rel_path,
                "sort_order": i,
                "position_in_question": "question",
                "alt_text": None,
            }
        )
    return records


def replace_images_in_text(text: str, records: list[dict[str, Any]]) -> str:
    """
    Replace base64 image placeholders in text with storage paths.

    Args:
        text: Original markdown with base64 images.
        records: Output from extract_and_save_images (must have storage_path).

    Returns:
        Text with base64 replaced by storage paths.
    """
    result = text
    for rec in records:
        result = BASE64_RE.sub(
            f'![Image]({rec["storage_path"]})',
            result,
            count=1,
        )
    return result
