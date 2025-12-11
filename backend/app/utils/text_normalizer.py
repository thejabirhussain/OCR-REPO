"""Arabic text normalization utilities."""

import re
from typing import Optional


def normalize_arabic_text(text: str) -> str:
    """
    Normalize Arabic text by:
    - Unifying different forms of letters (ya, alef, etc.)
    - Removing tatweel (elongation marks)
    - Normalizing whitespace
    - Preserving punctuation
    """
    if not text:
        return text

    # Remove tatweel (U+0640)
    text = text.replace("\u0640", "")

    # Normalize different forms of Alef
    # Alef with Madda (U+0622) -> Alef (U+0627)
    text = text.replace("\u0622", "\u0627")
    # Alef with Hamza Above (U+0623) -> Alef (U+0627)
    text = text.replace("\u0623", "\u0627")
    # Alef with Hamza Below (U+0625) -> Alef (U+0627)
    text = text.replace("\u0625", "\u0627")

    # Normalize different forms of Ya
    # Arabic Letter Yeh (U+064A) -> Arabic Letter Farsi Yeh (U+06CC) or keep as is
    # For now, we'll keep both forms but you can unify if needed

    # Normalize whitespace (multiple spaces to single space)
    text = re.sub(r"\s+", " ", text)

    # Remove zero-width characters
    text = text.replace("\u200B", "")  # Zero-width space
    text = text.replace("\u200C", "")  # Zero-width non-joiner
    text = text.replace("\u200D", "")  # Zero-width joiner
    text = text.replace("\uFEFF", "")  # Zero-width no-break space

    # Trim whitespace
    text = text.strip()

    return text


def detect_language(text: str) -> Optional[str]:
    """
    Simple language detection for Arabic vs English.
    Returns 'ar' if Arabic characters detected, 'en' otherwise.
    """
    if not text:
        return None

    # Check for Arabic characters (Unicode range: U+0600-U+06FF)
    arabic_pattern = re.compile(r"[\u0600-\u06FF]")
    has_arabic = bool(arabic_pattern.search(text))

    if has_arabic:
        return "ar"
    return "en"


def clean_text(text: str, preserve_punctuation: bool = True) -> str:
    """
    Clean text while optionally preserving punctuation.
    """
    if not text:
        return text

    # Normalize Arabic text
    text = normalize_arabic_text(text)

    if preserve_punctuation:
        # Keep common punctuation marks
        # Arabic punctuation: ، ؛ ؟
        # English punctuation: . , ; : ? ! - ( ) [ ] { } " '
        pass
    else:
        # Remove all punctuation
        text = re.sub(r"[^\w\s]", "", text)

    return text




