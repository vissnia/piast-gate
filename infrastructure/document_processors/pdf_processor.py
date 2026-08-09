import re
from io import BytesIO
import pdfplumber
from domain.services.anonymizer_service import AnonymizerService
from domain.interfaces.document_processor import DocumentProcessor

_SENTENCE_END_RE = re.compile(r"[.:;!?)\"'”]$")
_HYPHEN_WRAP_RE = re.compile(r"(?<=\w)-$")


def _reflow_page_text(raw_text: str) -> str:
    """
    Collapses PDF line-wrap artifacts into flowing paragraphs.

    pdfplumber emits one line per visual line of the page, so a wrapped
    sentence comes back as several short lines joined by single "\n"
    characters. A lone "\n" is not a paragraph break in markdown, so we
    rejoin wrapped lines into a single paragraph and only keep a real
    break where the source has a blank line or the previous line ends
    a sentence.
    """
    paragraphs = []
    current_lines = []

    def flush():
        if current_lines:
            paragraphs.append(" ".join(current_lines))
            current_lines.clear()

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
            continue

        if current_lines and _HYPHEN_WRAP_RE.search(current_lines[-1]):
            current_lines[-1] = current_lines[-1][:-1] + stripped
            continue

        if current_lines and _SENTENCE_END_RE.search(current_lines[-1]):
            flush()

        current_lines.append(stripped)

    flush()
    return "\n\n".join(paragraphs)


class PdfProcessor(DocumentProcessor):
    """Concrete implementation for PDF processing using pdfplumber."""

    def process(self, file_content: bytes, anonymizer: AnonymizerService) -> str:
        type_counters: dict = {}
        value_to_token_str: dict = {}

        pages_markdown = []
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                raw_text = page.extract_text() or ""
                text = _reflow_page_text(raw_text)
                if not text.strip():
                    continue
                anonymized, _ = anonymizer.anonymize(text, type_counters, value_to_token_str)
                pages_markdown.append(anonymized)

        return "\n\n---\n\n".join(pages_markdown)
