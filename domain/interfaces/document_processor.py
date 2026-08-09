from abc import ABC, abstractmethod
from domain.services.anonymizer_service import AnonymizerService

class DocumentProcessor(ABC):
    """Domain interface for document processors."""

    @abstractmethod
    def process(self, file_content: bytes, anonymizer: AnonymizerService) -> str:
        """
        Process the document content and return the anonymized text as markdown.

        Args:
            file_content (bytes): The raw file content.
            anonymizer (AnonymizerService): The service to use for anonymization.

        Returns:
            str: The anonymized document content, rendered as markdown.
        """
        pass
