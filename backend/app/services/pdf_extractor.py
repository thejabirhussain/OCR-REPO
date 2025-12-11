"""PDF and DOCX extraction service with structure preservation."""

import logging
from pathlib import Path
from typing import List, Optional

import pdfplumber
from docx import Document as DocxDocument

from app.utils.layout_schema import create_block
from app.schemas import Page, Block

logger = logging.getLogger(__name__)


def extract_text_from_pdf_pdfplumber(pdf_path: Path) -> List[dict]:
    """
    Extract text from PDF using pdfplumber (alternative method).

    Returns:
        List of page dictionaries
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            blocks = []
            block_id_counter = 0

            # Extract text with layout
            words = page.extract_words()
            if words:
                # Group words into paragraphs (simple approach)
                current_paragraph = []
                current_y = None
                y_threshold = 10

                for word in words:
                    word_y = word["top"]
                    if current_y is None or abs(word_y - current_y) < y_threshold:
                        current_paragraph.append(word["text"])
                        current_y = word_y
                    else:
                        # New paragraph
                        if current_paragraph:
                            block_text = " ".join(current_paragraph)
                            block_obj = create_block(
                                block_id=f"{page_num}-{block_id_counter}",
                                text=block_text,
                                block_type="paragraph",
                            )
                            blocks.append(block_obj.dict())
                            block_id_counter += 1
                        current_paragraph = [word["text"]]
                        current_y = word_y

                # Don't forget last paragraph
                if current_paragraph:
                    block_text = " ".join(current_paragraph)
                    block_obj = create_block(
                        block_id=f"{page_num}-{block_id_counter}",
                        text=block_text,
                        block_type="paragraph",
                    )
                    blocks.append(block_obj.dict())

            pages.append(Page(page_index=page_num, blocks=[Block(**b) for b in blocks]).dict())

    return pages


def extract_text_from_docx(docx_path: Path) -> List[dict]:
    """
    Extract text from DOCX file with structure preservation.

    Returns:
        List of page dictionaries (DOCX doesn't have pages, so we use a single "page")
    """
    doc = DocxDocument(docx_path)
    blocks = []
    block_id_counter = 0

    for element in doc.element.body:
        if element.tag.endswith("p"):  # Paragraph
            para = None
            for para_obj in doc.paragraphs:
                if para_obj._element == element:
                    para = para_obj
                    break

            if para:
                text = para.text.strip()
                if text:
                    # Check if heading
                    is_heading = para.style.name.startswith("Heading")
                    heading_level = None
                    if is_heading:
                        try:
                            heading_level = int(para.style.name.split()[-1])
                        except (ValueError, IndexError):
                            heading_level = 1

                    block_type = "heading" if is_heading else "paragraph"
                    block_obj = create_block(
                        block_id=f"0-{block_id_counter}",
                        text=text,
                        block_type=block_type,
                        is_heading=is_heading,
                        heading_level=heading_level,
                    )
                    blocks.append(block_obj.dict())
                    block_id_counter += 1

        elif element.tag.endswith("tbl"):  # Table
            # Find corresponding table object
            table = None
            for table_obj in doc.tables:
                if table_obj._element == element:
                    table = table_obj
                    break

            if table:
                table_id = f"table-{block_id_counter}"
                for row_idx, row in enumerate(table.rows):
                    for col_idx, cell in enumerate(row.cells):
                        cell_text = cell.text.strip()
                        if cell_text:
                            block_obj = create_block(
                                block_id=f"0-{block_id_counter}",
                                text=cell_text,
                                block_type="table_cell",
                                table_row=row_idx,
                                table_col=col_idx,
                                table_id=table_id,
                            )
                            blocks.append(block_obj.dict())
                            block_id_counter += 1

    # DOCX doesn't have pages, so we return a single page
    return [Page(page_index=0, blocks=[Block(**b) for b in blocks]).dict()]


def extract_text_from_file(
    file_path: Path,
    file_type: str,
    ocr_callback=None,
    ocr_engine: str = "paddleocr",
) -> List[dict]:
    """
    Extract text from file based on type.

    Args:
        file_path: Path to file
        file_type: File type ('pdf', 'docx', 'image')
        ocr_callback: Function for OCR: (image_path, page_index, engine) -> blocks
        ocr_engine: OCR engine to use

    Returns:
        List of page dictionaries
    """
    logger.info(f"Extracting text from {file_type} file: {file_path}")

    if file_type == "pdf":
        # Use pdfplumber for PDF extraction
        return extract_text_from_pdf_pdfplumber(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    elif file_type in ["image", "jpg", "jpeg", "png", "tiff", "tif"]:
        if ocr_callback:
            return [ocr_callback(file_path, 0, ocr_engine)]
        else:
            raise ValueError("OCR callback required for image files")
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

