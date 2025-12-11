"""Layout schema utilities for structured document representation."""

import uuid
from datetime import datetime
from typing import List, Optional

from app.schemas import (
    Block,
    BlockMetadata,
    DocumentMetadata,
    Page,
    StructuredDocument,
    TableMetadata,
)


def create_empty_document(
    source_filename: str,
    language: str = "ar",
    ocr_engine: Optional[str] = None,
) -> StructuredDocument:
    """Create an empty structured document."""
    return StructuredDocument(
        document_id=str(uuid.uuid4()),
        language=language,
        pages=[],
        metadata=DocumentMetadata(
            source_filename=source_filename,
            total_pages=0,
            extraction_timestamp=datetime.utcnow().isoformat() + "Z",
            ocr_engine=ocr_engine,
            processing_time_seconds=0.0,
        ),
    )


def create_block(
    block_id: str,
    text: str,
    block_type: str = "paragraph",
    bbox: Optional[List[float]] = None,
    is_heading: bool = False,
    heading_level: Optional[int] = None,
    list_level: Optional[int] = None,
    table_row: Optional[int] = None,
    table_col: Optional[int] = None,
    table_id: Optional[str] = None,
    confidence: Optional[float] = None,
) -> Block:
    """Create a text block with metadata."""
    table_metadata = None
    if table_row is not None and table_col is not None:
        table_metadata = TableMetadata(row=table_row, col=table_col, table_id=table_id)

    metadata = BlockMetadata(
        bbox=bbox,
        is_heading=is_heading,
        heading_level=heading_level,
        list_level=list_level,
        table=table_metadata,
        confidence=confidence,
    )

    return Block(block_id=block_id, type=block_type, metadata=metadata, text=text)


def create_page(page_index: int, blocks: List[Block]) -> Page:
    """Create a page with blocks."""
    return Page(page_index=page_index, blocks=blocks)


def calculate_document_stats(document: StructuredDocument) -> dict:
    """Calculate statistics for a document."""
    total_blocks = sum(len(page.blocks) for page in document.pages)
    total_characters = sum(
        len(block.text) for page in document.pages for block in page.blocks
    )

    return {
        "total_pages": len(document.pages),
        "total_blocks": total_blocks,
        "total_characters": total_characters,
    }

