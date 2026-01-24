from io import BytesIO
from docx import Document
from domain.services.anonymizer_service import AnonymizerService
from domain.interfaces.document_processor import DocumentProcessor

class DocxProcessor(DocumentProcessor):
    """Concrete implementation for DOCX processing using python-docx."""

    def process(self, file_content: bytes, anonymizer: AnonymizerService) -> bytes:
        source_stream = BytesIO(file_content)
        doc = Document(source_stream)
        
        def anonymize_text(text: str) -> str:
            if not text.strip():
                return text
            anonymized, _ = anonymizer.anonymize(text)
            return anonymized

        for paragraph in doc.paragraphs:
            if paragraph.text:
                paragraph.text = anonymize_text(paragraph.text)

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if paragraph.text:
                            paragraph.text = anonymize_text(paragraph.text)
        
        target_stream = BytesIO()
        doc.save(target_stream)
        return target_stream.getvalue()
