import re
from io import BytesIO
from typing import Callable, Iterator, Union
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from domain.services.anonymizer_service import AnonymizerService
from domain.interfaces.document_processor import DocumentProcessor

_HEADING_RE = re.compile(r"^Heading (\d)$")


def _iter_block_items(document: Document) -> Iterator[Union[Paragraph, Table]]:
    """Yields each top-level paragraph and table of the document body, in document order."""
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def _paragraph_to_markdown(paragraph: Paragraph, anonymize_text: Callable[[str], str]) -> str:
    text = anonymize_text(paragraph.text)
    if not text.strip():
        return ""

    style_name = paragraph.style.name if paragraph.style else ""
    heading_match = _HEADING_RE.match(style_name or "")
    if heading_match:
        level = min(int(heading_match.group(1)), 6)
        return f"{'#' * level} {text}"
    if style_name == "Title":
        return f"# {text}"
    if "List Bullet" in (style_name or ""):
        return f"- {text}"
    if "List Number" in (style_name or ""):
        return f"1. {text}"
    return text


def _table_to_markdown(table: Table, anonymize_text: Callable[[str], str]) -> str:
    rows = [
        [anonymize_text(cell.text).replace("\n", " ").replace("|", "\\|") for cell in row.cells]
        for row in table.rows
    ]
    if not rows:
        return ""

    header, *body_rows = rows
    separator = ["---"] * len(header)
    return "\n".join("| " + " | ".join(row) + " |" for row in [header, separator, *body_rows])


class DocxProcessor(DocumentProcessor):
    """Concrete implementation for DOCX processing using python-docx."""

    def process(self, file_content: bytes, anonymizer: AnonymizerService) -> str:
        doc = Document(BytesIO(file_content))

        type_counters: dict = {}
        value_to_token_str: dict = {}

        def anonymize_text(text: str) -> str:
            if not text.strip():
                return text
            anonymized, _ = anonymizer.anonymize(text, type_counters, value_to_token_str)
            return anonymized

        blocks = []
        for block in _iter_block_items(doc):
            if isinstance(block, Paragraph):
                markdown_block = _paragraph_to_markdown(block, anonymize_text)
            else:
                markdown_block = _table_to_markdown(block, anonymize_text)

            if markdown_block:
                blocks.append(markdown_block)

        return "\n\n".join(blocks)
