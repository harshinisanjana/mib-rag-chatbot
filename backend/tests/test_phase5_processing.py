from pathlib import Path

import fitz
import pytest
from docx import Document

from app.services.chunking_service import ChunkingService
from app.services.text_cleaning_service import clean_text
from app.services.text_extraction_service import TextExtractionError, TextExtractionService


def create_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def create_docx(path: Path, paragraphs: list[str]) -> None:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    document.save(path)


def test_extracts_pdf_text_and_page_metadata(tmp_path):
    path = tmp_path / "guide.pdf"
    create_pdf(path, "Reset your password from the account settings page.")

    pages = TextExtractionService.extract_pages(str(path), "pdf")

    assert len(pages) == 1
    assert "Reset your password" in pages[0].content
    assert pages[0].page_number == 1


def test_empty_pdf_has_no_extractable_pages(tmp_path):
    path = tmp_path / "empty.pdf"
    create_pdf(path, "")

    pages = TextExtractionService.extract_pages(str(path), "pdf")

    assert len(pages) == 1
    assert pages[0].content == ""


def test_invalid_pdf_raises_extraction_error(tmp_path):
    path = tmp_path / "invalid.pdf"
    path.write_bytes(b"not a PDF")

    with pytest.raises(TextExtractionError):
        TextExtractionService.extract_text(str(path), "pdf")


def test_extracts_docx_paragraphs(tmp_path):
    path = tmp_path / "faq.docx"
    create_docx(path, ["Account access", "Use the reset link to change your password."])

    text = TextExtractionService.extract_text(str(path), "docx")

    assert "Account access" in text
    assert "reset link" in text


def test_empty_and_invalid_docx_are_rejected(tmp_path):
    empty_path = tmp_path / "empty.docx"
    invalid_path = tmp_path / "invalid.docx"
    create_docx(empty_path, [])
    invalid_path.write_bytes(b"not a DOCX")

    assert TextExtractionService.extract_pages(str(empty_path), "docx") == []
    with pytest.raises(TextExtractionError):
        TextExtractionService.extract_text(str(invalid_path), "docx")


def test_cleaning_preserves_paragraph_boundaries():
    assert clean_text("  Heading\n\n\nBody   text  ") == "Heading\n\nBody text"


def test_chunking_supports_overlap_and_empty_text():
    service = ChunkingService(chunk_size_tokens=4, chunk_overlap_tokens=1)

    chunks = service.chunk_text("one two three four five six seven")

    assert [chunk.chunk_index for chunk in chunks] == [0, 1]
    assert all(chunk.document_id is None for chunk in chunks)
    assert chunks[0].content == "one two three four"
    assert chunks[1].content == "four five six seven"
    assert service.chunk_text("") == []