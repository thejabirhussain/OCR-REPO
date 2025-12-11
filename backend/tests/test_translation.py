"""Tests for translation service."""

import pytest
from app.services.translate import translate_text, detect_text_language


def test_detect_text_language():
    """Test language detection."""
    # Test Arabic detection
    arabic_text = "مرحبا بك"
    assert detect_text_language(arabic_text) == "ar"

    # Test English detection
    english_text = "Hello world"
    assert detect_text_language(english_text) == "en"


@pytest.mark.skip(reason="Requires loaded translation model")
def test_translate_text():
    """Test text translation."""
    # This would require the model to be loaded
    # arabic_text = "مرحبا بك"
    # translated = translate_text(arabic_text)
    # assert len(translated) > 0
    pass




