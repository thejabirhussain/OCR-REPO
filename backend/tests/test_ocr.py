"""Tests for OCR service."""

import pytest
from pathlib import Path
from app.services.ocr import extract_text_from_image, preprocess_image


@pytest.mark.skip(reason="Requires actual image files and OCR models")
def test_extract_text_from_image():
    """Test OCR extraction from image."""
    # This would require actual test images
    # image_path = Path("tests/fixtures/sample_arabic.jpg")
    # blocks = extract_text_from_image(image_path, page_index=0)
    # assert len(blocks) > 0
    pass


@pytest.mark.skip(reason="Requires actual image files")
def test_preprocess_image():
    """Test image preprocessing."""
    # This would require actual test images
    pass

