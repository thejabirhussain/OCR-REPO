"""Celery tasks for async document processing."""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from celery import Celery
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import Job, JobStatus, ProcessingStage
from app.schemas import StructuredDocument
from app.services.docx_generator import generate_docx_from_document, generate_txt_from_document
from app.services.ocr import extract_text_from_image
from app.services.pdf_extractor import extract_text_from_file
from app.services.translate import translate_document
from app.utils.layout_schema import (
    calculate_document_stats,
    create_empty_document,
)
from app.utils.text_normalizer import normalize_arabic_text

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Celery
celery_app = Celery(
    "arabic_ocr",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_time_limit=settings.job_timeout_minutes * 60,
    task_soft_time_limit=(settings.job_timeout_minutes * 60) - 60,
)


def get_db_session() -> Session:
    """Get database session."""
    return SessionLocal()


def update_job_status(
    job_id: str,
    status: JobStatus,
    error_message: Optional[str] = None,
    error_traceback: Optional[str] = None,
):
    """Update job status in database."""
    db = get_db_session()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = status
            job.updated_at = datetime.utcnow()
            if error_message:
                job.error_message = error_message
            if error_traceback:
                job.error_traceback = error_traceback
            if status == JobStatus.COMPLETED:
                job.completed_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        logger.error(f"Error updating job status: {e}")
        db.rollback()
    finally:
        db.close()


def update_processing_stage(job_id: str, stage: str, stage_status: ProcessingStage):
    """Update processing stage status."""
    db = get_db_session()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            if stage == "extraction":
                job.extraction_stage = stage_status
            elif stage == "ocr":
                job.ocr_stage = stage_status
            elif stage == "translation":
                job.translation_stage = stage_status
            job.updated_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        logger.error(f"Error updating processing stage: {e}")
        db.rollback()
    finally:
        db.close()


@celery_app.task(bind=True, name="process_document")
def process_document_task(self, job_id: str):
    """
    Main task to process a document: extract, OCR, translate.

    Args:
        job_id: Job UUID string
    """
    db = get_db_session()
    job = None

    try:
        # Get job from database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        logger.info(f"Starting processing for job {job_id}: {job.original_filename}")

        # Update status
        job.status = JobStatus.PROCESSING
        job.updated_at = datetime.utcnow()
        db.commit()

        file_path = Path(job.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get configuration
        config = job.config or {}
        ocr_engine = config.get("ocr_engine", settings.ocr_engine)
        source_lang = config.get("source_language", settings.source_language)
        target_lang = config.get("target_language", settings.target_language)
        translation_model = config.get("translation_model", settings.translation_model)

        # Step 1: Extract text from file
        logger.info("Step 1: Extracting text from file")
        update_processing_stage(job_id, "extraction", ProcessingStage.IN_PROGRESS)
        job.status = JobStatus.EXTRACTING
        db.commit()

        def ocr_callback(img_path: Path, page_idx: int, engine: str):
            """OCR callback for image pages."""
            return extract_text_from_image(img_path, page_idx, engine)

        # Determine file type
        file_ext = file_path.suffix.lower()
        if file_ext == ".pdf":
            file_type = "pdf"
        elif file_ext == ".docx":
            file_type = "docx"
        else:
            file_type = "image"

        # Extract pages
        pages_data = extract_text_from_file(
            file_path,
            file_type,
            ocr_callback=ocr_callback,
            ocr_engine=ocr_engine,
        )

        # Create structured document
        arabic_doc = create_empty_document(
            source_filename=job.original_filename,
            language="ar",
            ocr_engine=ocr_engine if file_type == "image" or any(
                p.get("blocks") for p in pages_data
            ) else None,
        )

        # Convert pages data to Page objects
        arabic_doc.pages = [
            Page(
                page_index=p["page_index"],
                blocks=[Block(**b) for b in p.get("blocks", [])],
            )
            for p in pages_data
        ]

        arabic_doc.metadata.total_pages = len(arabic_doc.pages)

        # Normalize Arabic text
        logger.info("Normalizing Arabic text")
        for page in arabic_doc.pages:
            for block in page.blocks:
                block.text = normalize_arabic_text(block.text)

        update_processing_stage(job_id, "extraction", ProcessingStage.COMPLETED)

        # Step 2: OCR (if needed - already done during extraction)
        if file_type == "image" or any(
            len(page.blocks) == 0 for page in arabic_doc.pages
        ):
            logger.info("Step 2: Running OCR")
            update_processing_stage(job_id, "ocr", ProcessingStage.IN_PROGRESS)
            job.status = JobStatus.OCR
            db.commit()
            # OCR already handled in extraction step
            update_processing_stage(job_id, "ocr", ProcessingStage.COMPLETED)
        else:
            update_processing_stage(job_id, "ocr", ProcessingStage.COMPLETED)

        # Step 3: Translate
        logger.info("Step 3: Translating document")
        update_processing_stage(job_id, "translation", ProcessingStage.IN_PROGRESS)
        job.status = JobStatus.TRANSLATING
        db.commit()

        english_doc = translate_document(
            arabic_doc,
            source_lang=source_lang,
            target_lang=target_lang,
        )

        update_processing_stage(job_id, "translation", ProcessingStage.COMPLETED)

        # Calculate statistics
        arabic_stats = calculate_document_stats(arabic_doc)
        english_stats = calculate_document_stats(english_doc)

        # Save results
        job.arabic_json = arabic_doc.dict()
        job.english_json = english_doc.dict()

        job.stats = {
            "total_pages": arabic_stats["total_pages"],
            "total_blocks": arabic_stats["total_blocks"],
            "total_characters_arabic": arabic_stats["total_characters"],
            "total_characters_english": english_stats["total_characters"],
        }

        # Update status
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        logger.error(traceback.format_exc())

        error_msg = str(e)
        error_tb = traceback.format_exc()

        if job:
            job.status = JobStatus.FAILED
            job.error_message = error_msg
            job.error_traceback = error_tb
            job.updated_at = datetime.utcnow()
            db.commit()

        # Re-raise for Celery to handle
        raise

    finally:
        db.close()

