"""SQLAlchemy database models."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Integer, JSON, String, Text

from app.database import Base


class JobStatus(str, Enum):
    """Job status enumeration."""

    QUEUED = "queued"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    OCR = "ocr"
    TRANSLATING = "translating"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStage(str, Enum):
    """Processing stage enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    """Job model for tracking document processing."""

    __tablename__ = "jobs"

    # Use string UUID for SQLite compatibility
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(SQLEnum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)

    # Processing stages
    extraction_stage = Column(
        SQLEnum(ProcessingStage),
        default=ProcessingStage.PENDING,
        nullable=False,
    )
    ocr_stage = Column(
        SQLEnum(ProcessingStage),
        default=ProcessingStage.PENDING,
        nullable=False,
    )
    translation_stage = Column(
        SQLEnum(ProcessingStage),
        default=ProcessingStage.PENDING,
        nullable=False,
    )

    # Results storage (JSON paths or direct JSON)
    arabic_json_path = Column(String(512), nullable=True)
    english_json_path = Column(String(512), nullable=True)
    arabic_json = Column(JSON, nullable=True)  # Store structured Arabic text
    english_json = Column(JSON, nullable=True)  # Store structured English translation

    # Statistics
    stats = Column(JSON, nullable=True)  # Total pages, blocks, characters, etc.

    # Error handling
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Configuration used for this job
    config = Column(JSON, nullable=True)  # OCR engine, translation model, etc.

    def __repr__(self) -> str:
        """String representation."""
        return f"<Job(id={self.id}, status={self.status}, filename={self.original_filename})>"



