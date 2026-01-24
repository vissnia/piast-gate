from abc import ABC, abstractmethod
from domain.interfaces.document_processor import DocumentProcessor

class DocumentProcessorFactory(ABC):
    """Domain interface for document processor factory."""

    @abstractmethod
    def get_processor(self, content_type: str) -> DocumentProcessor:
        """
        Returns an instance of the appropriate processor for the content type.

        Args:
            content_type (str): The MIME type of the file.

        Returns:
            DocumentProcessor: An instance of the processor.
        """
        pass
