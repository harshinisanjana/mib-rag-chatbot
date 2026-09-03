from dataclasses import dataclass
from pathlib import Path

import fitz
from docx import Document as DocxDocument


class TextExtractionError(Exception):
    """Raised when a supported file cannot produce usable text."""


@dataclass(frozen=True)
class ExtractedPage:
    content: str
    page_number: int | None = None


class TextExtractionService:
    @staticmethod
    def extract_pages(file_path: str, file_type: str) -> list[ExtractedPage]:
        path = Path(file_path)
        if file_type == "pdf":
            return TextExtractionService._extract_pdf(path)
        if file_type == "docx":
            return TextExtractionService._extract_docx(path)
        raise TextExtractionError(f"Unsupported file type: {file_type}")

    @staticmethod
    def extract_text(file_path: str, file_type: str) -> str:
        return "\n\n".join(page.content for page in TextExtractionService.extract_pages(file_path, file_type))

    @staticmethod
    def _extract_pdf(path: Path) -> list[ExtractedPage]:
        try:
            with fitz.open(path) as document:
                pages = [
                    ExtractedPage(page.get_text("text"), page_number=index)
                    for index, page in enumerate(document, start=1)
                ]
        except Exception as exc:
            raise TextExtractionError(f"Could not read PDF: {exc}") from exc
        return pages

    @staticmethod
    def _extract_docx(path: Path) -> list[ExtractedPage]:
        try:
            document = DocxDocument(path)
            paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        except Exception as exc:
            raise TextExtractionError(f"Could not read DOCX: {exc}") from exc
        return [ExtractedPage("\n\n".join(paragraphs))] if paragraphs else []


def extract_text(file_path: str, file_type: str) -> str:
    return TextExtractionService.extract_text(file_path, file_type)