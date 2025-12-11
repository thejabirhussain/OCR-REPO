"""Script to download ML models."""

import logging
from pathlib import Path

from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_models():
    """Download required ML models."""
    settings = get_settings()
    model_path = settings.model_path
    model_path.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading translation model...")
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        model_name = settings.translation_model
        logger.info(f"Downloading {model_name}...")

        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=str(model_path))
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name, cache_dir=str(model_path))

        logger.info("Translation model downloaded successfully")
    except Exception as e:
        logger.error(f"Error downloading translation model: {e}")
        raise

    logger.info("Models downloaded successfully")


if __name__ == "__main__":
    download_models()




