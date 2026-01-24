from domain.services.anonymizer_service import AnonymizerService
from domain.interfaces.document_processor import DocumentProcessor

class PdfProcessor(DocumentProcessor):
    """Concrete implementation for PDF processing."""

    def process(self, file_content: bytes, anonymizer: AnonymizerService) -> bytes:
        """
        Process the PDF content.
        
        Note: Implementation is pending specialized PDF redaction logic.
        """
        raise NotImplementedError("PDF processing is not yet implemented.")
