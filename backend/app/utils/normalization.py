def normalize_subject(subject: str) -> str:
    """Normalize subject names for DB constraints."""
    if not subject:
        return subject
    s = subject.lower().strip()
    if s in ["maths", "mathematics"]:
        return "mathematics"
    return s
