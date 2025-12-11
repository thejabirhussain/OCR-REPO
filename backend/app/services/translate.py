"""Translation service using open-source models."""

import logging
from typing import Dict, List, Optional

from langdetect import detect, LangDetectException

from app.config import get_settings
from app.schemas import Block, Page, StructuredDocument
from app.utils.text_normalizer import detect_language

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy loading of translation model
_translation_model = None
_translation_tokenizer = None


def _load_translation_model():
    """Load translation model and tokenizer."""
    global _translation_model, _translation_tokenizer
    if _translation_model is None:
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            model_name = settings.translation_model
            logger.info(f"Loading translation model: {model_name}")

            _translation_tokenizer = AutoTokenizer.from_pretrained(model_name)
            _translation_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

            # Move to GPU if available
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            _translation_model = _translation_model.to(device)
            _translation_model.eval()

            logger.info(f"Translation model loaded on {device}")
        except Exception as e:
            logger.error(f"Failed to load translation model: {e}")
            raise
    return _translation_model, _translation_tokenizer


def detect_text_language(text: str) -> Optional[str]:
    """
    Detect language of text.
    Returns language code or None if detection fails.
    """
    if not text or len(text.strip()) < 3:
        return None

    # First try simple Arabic detection
    lang = detect_language(text)
    if lang:
        return "ar" if lang == "ar" else "en"

    # Fallback to langdetect
    try:
        detected = detect(text)
        # Map common codes
        if detected.startswith("ar"):
            return "ar"
        elif detected.startswith("en"):
            return "en"
        return detected
    except LangDetectException:
        return None


def translate_text(
    text: str,
    source_lang: str = "ara_Arab",
    target_lang: str = "eng_Latn",
    skip_if_english: bool = True,
) -> str:
    """
    Translate a single text string.

    Args:
        text: Text to translate
        source_lang: Source language code (NLLB format)
        target_lang: Target language code (NLLB format)
        skip_if_english: Skip translation if text is detected as English

    Returns:
        Translated text
    """
    if not text or not text.strip():
        return text

    # Skip translation if text is already in target language
    if skip_if_english:
        detected_lang = detect_text_language(text)
        if detected_lang == "en" and target_lang.startswith("eng"):
            logger.debug(f"Skipping translation - text is already English: {text[:50]}...")
            return text

    try:
        model, tokenizer = _load_translation_model()

        # Tokenize
        inputs = tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=settings.max_length,
        )

        # Move to same device as model
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Translate
        with model.no_grad():
            translated_tokens = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_lang),
                max_length=settings.max_length,
                num_beams=5,
                early_stopping=True,
            )

        # Decode
        translated_text = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)

        return translated_text.strip()
    except Exception as e:
        logger.error(f"Translation error for text '{text[:50]}...': {e}")
        return text  # Return original on error


def translate_batch(
    texts: List[str],
    source_lang: str = "ara_Arab",
    target_lang: str = "eng_Latn",
    skip_if_english: bool = True,
) -> List[str]:
    """
    Translate a batch of texts (more efficient).

    Args:
        texts: List of texts to translate
        source_lang: Source language code
        target_lang: Target language code
        skip_if_english: Skip translation if text is detected as English

    Returns:
        List of translated texts
    """
    if not texts:
        return []

    # Filter out empty texts
    non_empty_texts = [(i, text) for i, text in enumerate(texts) if text and text.strip()]
    if not non_empty_texts:
        return [""] * len(texts)

    indices, texts_to_translate = zip(*non_empty_texts)

    # Skip English texts if requested
    texts_to_translate_list = list(texts_to_translate)
    if skip_if_english:
        filtered_indices = []
        filtered_texts = []
        for idx, text in zip(indices, texts_to_translate_list):
            detected_lang = detect_text_language(text)
            if detected_lang != "en" or not target_lang.startswith("eng"):
                filtered_indices.append(idx)
                filtered_texts.append(text)
            else:
                logger.debug(f"Skipping English text at index {idx}")

        if not filtered_texts:
            # All texts are English, return as-is
            return list(texts)
        texts_to_translate_list = filtered_texts
        indices = filtered_indices

    try:
        model, tokenizer = _load_translation_model()

        # Tokenize batch
        inputs = tokenizer(
            texts_to_translate_list,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=settings.max_length,
        )

        # Move to same device as model
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Translate
        with model.no_grad():
            translated_tokens = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_lang),
                max_length=settings.max_length,
                num_beams=5,
                early_stopping=True,
            )

        # Decode
        translated_texts = tokenizer.batch_decode(
            translated_tokens, skip_special_tokens=True
        )

        # Map back to original indices
        result = [""] * len(texts)
        for idx, translated in zip(indices, translated_texts):
            result[idx] = translated.strip()

        # Fill in skipped English texts
        for i, original_text in enumerate(texts):
            if not result[i]:
                result[i] = original_text

        return result
    except Exception as e:
        logger.error(f"Batch translation error: {e}")
        # Fallback to individual translation
        logger.info("Falling back to individual translation")
        return [translate_text(text, source_lang, target_lang, skip_if_english) for text in texts]


def translate_document(
    document: StructuredDocument,
    source_lang: str = "ara_Arab",
    target_lang: str = "eng_Latn",
) -> StructuredDocument:
    """
    Translate a structured document while preserving structure.

    Args:
        document: Structured document with Arabic text
        source_lang: Source language code
        target_lang: Target language code

    Returns:
        Translated structured document with same structure
    """
    logger.info(f"Translating document with {len(document.pages)} pages")

    # Collect all texts for batch translation
    all_texts = []
    text_to_block = {}  # Map text index to (page_idx, block_idx)

    for page_idx, page in enumerate(document.pages):
        for block_idx, block in enumerate(page.blocks):
            if block.text.strip():
                text_idx = len(all_texts)
                all_texts.append(block.text)
                text_to_block[text_idx] = (page_idx, block_idx)

    logger.info(f"Translating {len(all_texts)} text blocks")

    # Translate in batches
    batch_size = settings.batch_size
    translated_texts = []
    for i in range(0, len(all_texts), batch_size):
        batch = all_texts[i : i + batch_size]
        batch_translated = translate_batch(
            batch, source_lang=source_lang, target_lang=target_lang
        )
        translated_texts.extend(batch_translated)
        logger.info(f"Translated batch {i // batch_size + 1}/{(len(all_texts) + batch_size - 1) // batch_size}")

    # Reconstruct document with translated texts
    translated_pages = []
    for page_idx, page in enumerate(document.pages):
        translated_blocks = []
        for block_idx, block in enumerate(page.blocks):
            # Find corresponding translated text
            text_idx = None
            for idx, (p_idx, b_idx) in text_to_block.items():
                if p_idx == page_idx and b_idx == block_idx:
                    text_idx = idx
                    break

            if text_idx is not None and text_idx < len(translated_texts):
                translated_text = translated_texts[text_idx]
            else:
                translated_text = block.text  # Fallback

            # Create new block with translated text
            translated_block = Block(
                block_id=block.block_id,
                type=block.type,
                metadata=block.metadata,
                text=translated_text,
            )
            translated_blocks.append(translated_block)

        translated_pages.append(Page(page_index=page.page_index, blocks=translated_blocks))

    # Create translated document
    translated_doc = StructuredDocument(
        document_id=document.document_id,
        language="en",
        pages=translated_pages,
        metadata=document.metadata,
    )

    logger.info("Translation completed")
    return translated_doc




