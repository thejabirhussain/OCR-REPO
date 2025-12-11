"""OCR service using PaddleOCR and Tesseract."""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from app.config import get_settings
from app.utils.layout_schema import create_block

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy loading of OCR engines
_paddleocr_instance = None
_tesseract_available = None


def _get_paddleocr():
    """Get or initialize PaddleOCR instance."""
    global _paddleocr_instance
    if _paddleocr_instance is None:
        try:
            from paddleocr import PaddleOCR

            _paddleocr_instance = PaddleOCR(
                use_angle_cls=True,
                lang="ar",
                use_gpu=False,  # Set to True if GPU available
            )
            logger.info("PaddleOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise
    return _paddleocr_instance


def _check_tesseract():
    """Check if Tesseract is available."""
    global _tesseract_available
    if _tesseract_available is None:
        try:
            import pytesseract

            pytesseract.get_tesseract_version()
            _tesseract_available = True
            logger.info("Tesseract is available")
        except Exception:
            _tesseract_available = False
            logger.warning("Tesseract is not available")
    return _tesseract_available


def preprocess_image(image_path: Path) -> np.ndarray:
    """
    Preprocess image for better OCR results.
    - Convert to grayscale
    - Apply denoising
    - Optional: deskew, binarization
    """
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    # Convert to grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Optional: Adaptive thresholding for better contrast
    # binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    #                                cv2.THRESH_BINARY, 11, 2)

    return denoised


def ocr_with_paddleocr(image_path: Path) -> List[Tuple[str, float, List[float]]]:
    """
    Run OCR using PaddleOCR.

    Returns:
        List of tuples: (text, confidence, bbox)
        bbox format: [x1, y1, x2, y2]
    """
    try:
        ocr = _get_paddleocr()
        result = ocr.ocr(str(image_path), cls=True)

        if not result or not result[0]:
            return []

        ocr_results = []
        for line in result[0]:
            if line:
                bbox, (text, confidence) = line
                # Convert bbox from [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] to [x1, y1, x2, y2]
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                bbox_flat = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                ocr_results.append((text, confidence, bbox_flat))

        return ocr_results
    except Exception as e:
        logger.error(f"PaddleOCR error: {e}")
        return []


def ocr_with_tesseract(image_path: Path) -> List[Tuple[str, float, List[float]]]:
    """
    Run OCR using Tesseract.

    Returns:
        List of tuples: (text, confidence, bbox)
    """
    if not _check_tesseract():
        return []

    try:
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)
        # Get detailed data including bounding boxes
        data = pytesseract.image_to_data(
            img, lang=settings.tesseract_lang, output_type=pytesseract.Output.DICT
        )

        results = []
        n_boxes = len(data["text"])
        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = float(data["conf"][i]) if data["conf"][i] != "-1" else 0.0
            if text and conf > 0:
                x, y, w, h = (
                    data["left"][i],
                    data["top"][i],
                    data["width"][i],
                    data["height"][i],
                )
                bbox = [x, y, x + w, y + h]
                results.append((text, conf / 100.0, bbox))

        return results
    except Exception as e:
        logger.error(f"Tesseract OCR error: {e}")
        return []


def group_ocr_results_into_blocks(
    ocr_results: List[Tuple[str, float, List[float]]],
    page_index: int,
) -> List[dict]:
    """
    Group OCR results into logical blocks (paragraphs, lines).

    Args:
        ocr_results: List of (text, confidence, bbox) tuples
        page_index: Page index for block IDs

    Returns:
        List of block dictionaries
    """
    if not ocr_results:
        return []

    blocks = []
    current_block_text = []
    current_block_confidences = []
    current_block_bbox = None
    block_id_counter = 0

    # Simple grouping: lines close together belong to same paragraph
    # Sort by y-coordinate (top to bottom)
    sorted_results = sorted(ocr_results, key=lambda x: x[2][1])  # Sort by y1

    y_threshold = 30  # Pixels - lines within this distance are in same paragraph

    for text, confidence, bbox in sorted_results:
        if current_block_bbox is None:
            # Start new block
            current_block_text = [text]
            current_block_confidences = [confidence]
            current_block_bbox = bbox.copy()
        else:
            # Check if this line belongs to current block
            prev_y2 = current_block_bbox[3]
            curr_y1 = bbox[1]

            if curr_y1 - prev_y2 < y_threshold:
                # Same paragraph
                current_block_text.append(text)
                current_block_confidences.append(confidence)
                # Expand bbox
                current_block_bbox[0] = min(current_block_bbox[0], bbox[0])
                current_block_bbox[1] = min(current_block_bbox[1], bbox[1])
                current_block_bbox[2] = max(current_block_bbox[2], bbox[2])
                current_block_bbox[3] = max(current_block_bbox[3], bbox[3])
            else:
                # New paragraph - save current block
                block_text = " ".join(current_block_text)
                avg_confidence = sum(current_block_confidences) / len(current_block_confidences)
                block = create_block(
                    block_id=f"{page_index}-{block_id_counter}",
                    text=block_text,
                    block_type="paragraph",
                    bbox=current_block_bbox,
                    confidence=avg_confidence,
                )
                blocks.append(block.dict())

                # Start new block
                current_block_text = [text]
                current_block_confidences = [confidence]
                current_block_bbox = bbox.copy()
                block_id_counter += 1

    # Don't forget the last block
    if current_block_text:
        block_text = " ".join(current_block_text)
        avg_confidence = sum(current_block_confidences) / len(current_block_confidences)
        block = create_block(
            block_id=f"{page_index}-{block_id_counter}",
            text=block_text,
            block_type="paragraph",
            bbox=current_block_bbox,
            confidence=avg_confidence,
        )
        blocks.append(block.dict())

    return blocks


def extract_text_from_image(
    image_path: Path,
    page_index: int = 0,
    engine: str = "paddleocr",
    use_fallback: bool = True,
) -> List[dict]:
    """
    Extract text from an image using OCR.

    Args:
        image_path: Path to image file
        page_index: Page index for block IDs
        engine: OCR engine to use ('paddleocr', 'tesseract', 'ensemble')
        use_fallback: Whether to use fallback engine if primary fails

    Returns:
        List of block dictionaries
    """
    logger.info(f"Extracting text from image: {image_path} using engine: {engine}")

    # Preprocess image
    try:
        preprocessed_img = preprocess_image(image_path)
        # Save preprocessed image temporarily
        temp_path = image_path.parent / f"temp_{image_path.name}"
        cv2.imwrite(str(temp_path), preprocessed_img)
        image_path_to_use = temp_path
    except Exception as e:
        logger.warning(f"Image preprocessing failed, using original: {e}")
        image_path_to_use = image_path

    ocr_results = []

    try:
        if engine == "paddleocr" or engine == "ensemble":
            ocr_results = ocr_with_paddleocr(image_path_to_use)
            logger.info(f"PaddleOCR found {len(ocr_results)} text regions")

        if (not ocr_results or engine == "tesseract") and (
            engine == "tesseract" or (use_fallback and settings.use_tesseract_fallback)
        ):
            tesseract_results = ocr_with_tesseract(image_path_to_use)
            logger.info(f"Tesseract found {len(tesseract_results)} text regions")

            if engine == "ensemble":
                # Use results with higher confidence or longer text
                # Simple heuristic: prefer longer text if confidence is similar
                combined_results = {}
                for text, conf, bbox in ocr_results:
                    key = tuple(bbox)
                    if key not in combined_results or len(text) > len(combined_results[key][0]):
                        combined_results[key] = (text, conf, bbox)

                for text, conf, bbox in tesseract_results:
                    key = tuple(bbox)
                    if key not in combined_results or len(text) > len(combined_results[key][0]):
                        combined_results[key] = (text, conf, bbox)

                ocr_results = list(combined_results.values())
            elif not ocr_results:
                ocr_results = tesseract_results

    finally:
        # Clean up temp file
        if image_path_to_use != image_path and image_path_to_use.exists():
            image_path_to_use.unlink()

    if not ocr_results:
        logger.warning(f"No text extracted from image: {image_path}")
        return []

    # Group into blocks
    blocks = group_ocr_results_into_blocks(ocr_results, page_index)

    logger.info(f"Grouped into {len(blocks)} blocks")
    return blocks

