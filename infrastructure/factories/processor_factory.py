from typing import Dict, Type
from domain.interfaces.document_processor_factory import DocumentProcessorFactory
from domain.interfaces.document_processor import DocumentProcessor
from infrastructure.document_processors.pdf_processor import PdfProcessor
from infrastructure.document_processors.docx_processor import DocxProcessor

class DocumentProcessorFactory(DocumentProcessorFactory):
    """Factory to retrieve the correct document processor."""

    _PROCESSORS: Dict[str, Type[DocumentProcessor]] = {
        "application/pdf": PdfProcessor,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxProcessor,
    }

    def get_processor(self, content_type: str) -> DocumentProcessor:
        """
        Returns an instance of the appropriate processor for the content type.

        Args:
            content_type (str): The MIME type of the file.

        Returns:
            DocumentProcessor: An instance of the processor.

        Raises:
            ValueError: If the content type is not supported.
        """
        processor_class = self._PROCESSORS.get(content_type)
        if not processor_class:
            raise ValueError(f"Unsupported content type: {content_type}")
        
        return processor_class()
