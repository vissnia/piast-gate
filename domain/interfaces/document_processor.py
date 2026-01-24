from abc import ABC, abstractmethod
from domain.services.anonymizer_service import AnonymizerService

class DocumentProcessor(ABC):
    """Domain interface for document processors."""

    @abstractmethod
    def process(self, file_content: bytes, anonymizer: AnonymizerService) -> bytes:
        """
        Process the document content and return the anonymized version.

        Args:
            file_content (bytes): The raw file content.
            anonymizer (AnonymizerService): The service to use for anonymization.

        Returns:
            bytes: The anonymized file content.
        """
        pass
